from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from add_comment import add_comment
from get_comments import get_comments
import html
import json
import secrets
from email.parser import BytesParser
from email import policy
from pathlib import Path

csrf_token = secrets.token_hex(32)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class StoredXSSHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        comments = get_comments()
        comments_html = ""

        for comment in comments:
            safe_username = html.escape(comment[1])
            safe_content = html.escape(comment[2])

            comments_html += f"""
            <div>
                <h3>{safe_username}</h3>
                <p>{safe_content}</p>
            </div>
            """

        files_html = "" 

        for file_path in UPLOAD_DIR.glob("*.txt"):
            #获取文件名，不包含前面的目录路径
            #文件名中的特殊字符转换成 HTML 实体，避免浏览器把文件名当成 HTML 标签或代码解析
            files_html += f"""
            <li>{html.escape(file_path.name)}</li>
            """

        response_html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>校园留言板</title>
        </head>
        <body>
            <h1>校园留言板</h1>

            <h2>发布留言</h2>

            <form method="POST" action="/comments">
                <input type="text" name="username" placeholder="用户名">
                <input type="hidden" name="csrf_token" value="{csrf_token}">
                <textarea name="content" placeholder="留言内容"></textarea>
                <button type="submit">提交留言</button>
            </form>

            <h2>上传附件</h2>
            
            <form method="POST" action="/upload" enctype="multipart/form-data">
                <input type="file" name="uploaded_file" accept=".txt">
                <input type="hidden" name="csrf_token" value="{csrf_token}">
                <button type="submit">上传附件</button>
            </form>

            <h2>留言列表</h2>

            {comments_html}
            <h2>已上传附件</h2>
            <ul>
                {files_html}
            </ul>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8"
        )
        self.end_headers()
        self.wfile.write(response_html.encode("utf-8"))

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/comments":
            self.handle_comment()
        elif path == "/upload":
            self.handle_upload()
        else:
            self.send_response(404)
            self.end_headers()

    def handle_comment(self):

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")

        data = parse_qs(body)

        submitted_token = data.get("csrf_token",[""])[0]

        username = data.get("username", [""])[0]#只选取第一个
        content = data.get("content", [""])[0]

        if not secrets.compare_digest(submitted_token, csrf_token):
            self.send_response(403)
            self.end_headers()
            return 


        add_comment(username, content)

        # 保存成功后，重新访问留言板
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def handle_upload(self):
        print("收到文件上传POST请求")
        MAX_SIZE = 1024*1024
        
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self.send_response(400)
            self.end_headers()
            return

        if length <= 0:
            self.send_response(400)
            self.end_headers()
            return
        print("Content-Length:", length)
        if length > MAX_SIZE:
            self.send_response(413)
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True
            return

        body = self.rfile.read(length)
        content_type = self.headers.get("Content-Type", "")
        mime_data=(
            f"Content-Type: {content_type}\r\n"
            "MIME-Version:1.0\r\n"
            "\r\n"
        ).encode("utf-8") + body

        message = BytesParser(policy=policy.default).parsebytes(mime_data)
        submitted_token = "" 
        filename = None
        file_data = None

        if not message.is_multipart():
            self.send_response(400)
            self.end_headers()
            return

        for part in message.iter_parts():
            field_name = part.get_param(
                "name", header="content-disposition"
            )


            if field_name == "csrf_token":
                submitted_token = part.get_content()

            elif field_name == "uploaded_file":
                filename = part.get_filename()
                file_data = part.get_payload(decode=True)

            
        if not secrets.compare_digest(submitted_token, csrf_token):
            self.send_response(403)
            self.end_headers()
            return

        if filename is None or file_data is None:
            self.send_response(400)
            self.end_headers()
            return

        try:
            file_data.decode("utf-8")
        except UnicodeDecodeError:
            self.send_response(415)
            self.end_headers()
            return

        
        if Path(filename).suffix.lower() != ".txt":
            self.send_response(415)
            self.end_headers()
            return
        safe_filename = secrets.token_hex(16) + ".txt"
        file_path = UPLOAD_DIR / safe_filename

        with open(file_path, "xb") as f:
            f.write(file_data)
        print("文件上传验证通过")
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

        
    


server = HTTPServer(
    ("127.0.0.1", 8001),
    StoredXSSHandler
)

print("留言板服务器启动：http://127.0.0.1:8001")

server.serve_forever()
    