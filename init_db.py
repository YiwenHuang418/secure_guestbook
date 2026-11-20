import sqlite3

conn = sqlite3.connect("guestbook.db")
cursor = conn.cursor()

sql = """
CREATE TABLE IF NOT EXISTS comments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    content TEXT NOT NULL
);
"""

cursor.execute(sql)
cursor.execute("PRAGMA table_info(comments)")
print(cursor.fetchall())
conn.commit()
conn.close()

print("留言数据库初始化成功")