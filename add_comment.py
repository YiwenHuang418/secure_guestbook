import sqlite3

def add_comment(username, content):
    conn = sqlite3.connect("guestbook.db")
    cursor = conn.cursor() #游标

    sql = """
    INSERT INTO comments (username, content)
    VALUES (?, ?)
    """
    try:
        cursor.execute(sql,(username, content))
        conn.commit()

    finally:
        
        conn.close()

if __name__ == "__main__":
    add_comment("Alice", "大家好！")
    add_comment("Bob", "周末一起出去玩吧！")