import sqlite3

def get_comments():
    conn = sqlite3.connect("guestbook.db")
    cursor = conn.cursor()

    sql = """
    SELECT * FROM comments ORDER BY id ASC
    """

    try:
        cursor.execute(sql) #返回的是 Cursor 游标对象
        lst = cursor.fetchall() #获取查询结果中的所有记录
        #查询不需要 commit()

    finally:
        conn.close()

    return lst

if __name__ == "__main__":
    comments = get_comments()

    for comment in comments:
        print(comment)