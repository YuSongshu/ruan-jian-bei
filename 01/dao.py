import mysql.connector
from fastapi import HTTPException

DB_CONFIG = {
    "host": "",
    "user": "",
    "password": "",
    "database": ""
}
DB_READY = False

def get_db_connection():
    if not DB_READY:
        raise HTTPException(status_code=400, detail="请先完成系统配置")
    try:
        return mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            charset="utf8mb4"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库连接失败：{str(e)}")

def user_exists(username: str) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM user WHERE username=%s", (username,))
    flag = cur.fetchone() is not None
    cur.close()
    conn.close()
    return flag

def add_user(username: str, password: str, profile_json: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user(username,password,student_profile) VALUES(%s,%s,%s)",
        (username, password, profile_json)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_user_info(username: str):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM user WHERE username=%s", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def update_username(old_name: str, new_name: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE user SET username=%s WHERE username=%s", (new_name, old_name))
    conn.commit()
    cur.close()
    conn.close()

def update_user_pwd(username: str, new_pwd: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE user SET password=%s WHERE username=%s", (new_pwd, username))
    conn.commit()
    cur.close()
    conn.close()

def delete_user(username: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM user WHERE username=%s", (username,))
    conn.commit()
    cur.close()
    conn.close()

def get_user_profile(username: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT student_profile FROM user WHERE username=%s", (username,))
    res = cur.fetchone()
    cur.close()
    conn.close()
    return res[0] if res else None

def save_user_profile(username: str, profile_json: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE user SET student_profile=%s WHERE username=%s", (profile_json, username))
    conn.commit()
    cur.close()
    conn.close()

# ---------- 聊天记录表 chat_history 操作 ----------
def add_chat_record(username: str, role: str, content: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chat_history(username,role,content) VALUES(%s,%s,%s)",
        (username, role, content)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_chat_records(username: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT role,content FROM chat_history WHERE username=%s ORDER BY id ASC", (username,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def clear_chat_records(username: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM chat_history WHERE username=%s", (username,))
    conn.commit()
    cur.close()
    conn.close()