import json
import mysql.connector
from fastapi import HTTPException
from langchain_openai import ChatOpenAI

class Method:
    def __init__(self):
        self.mysql_host = ""
        self.mysql_user = ""
        self.mysql_password = ""
        self.mysql_db = ""
        self.ai_model = ""
        self.ai_key = ""
        self.ai_url = ""
        self.llm = None
        self.db_ready = False

    def db_conn(self):
        if not self.db_ready:
            raise HTTPException(400, "请先完成配置")
        try:
            return mysql.connector.connect(
                host=self.mysql_host,
                user=self.mysql_user,
                password=self.mysql_password,
                database=self.mysql_db,
                charset="utf8mb4"
            )
        except Exception as e:
            raise HTTPException(500, f"数据库连接失败: {str(e)}")

    def user_exist(self, username):
        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM user WHERE username=%s", (username,))
        flag = cur.fetchone() is not None
        cur.close()
        conn.close()
        return flag

    def register(self, username, pwd):
        if self.user_exist(username):
            raise HTTPException(400, "用户名已存在")
        default = json.dumps({
            "知识基础": "暂未采集",
            "认知风格": "暂未采集",
            "易错点偏好": "暂未采集",
            "学习目标": "暂未采集",
            "学习历史": "暂未采集",
            "学习习惯": "暂未采集"
        }, ensure_ascii=False)
        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user(username,password,student_profile) VALUES(%s,%s,%s)",
            (username, pwd, default)
        )
        conn.commit()
        cur.close()
        conn.close()

    def login_check(self, username, pwd):
        conn = self.db_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT password FROM user WHERE username=%s", (username,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row and row["password"] == pwd

    def edit_username(self, old_name, new_name):
        if self.user_exist(new_name):
            raise HTTPException(400, "新用户名已存在")
        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute("UPDATE user SET username=%s WHERE username=%s", (new_name, old_name))
        conn.commit()
        cur.close()
        conn.close()

    def edit_pwd(self, username, old_pwd, new_pwd):
        if not self.login_check(username, old_pwd):
            raise HTTPException(400, "原密码错误")
        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute("UPDATE user SET password=%s WHERE username=%s", (new_pwd, username))
        conn.commit()
        cur.close()
        conn.close()

    def del_user(self, username):
        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM user WHERE username=%s", (username,))
        conn.commit()
        cur.close()
        conn.close()

    def save_chat(self, username, role, content):
        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chat_history(username,role,content) VALUES(%s,%s,%s)",
            (username, role, content)
        )
        conn.commit()
        cur.close()
        conn.close()

    def load_chat_plain(self, username):
        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute("SELECT role,content FROM chat_history WHERE username=%s ORDER BY id ASC", (username,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [{"role": r, "content": c} for r, c in rows]

    def clear_chat(self, username):
        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM chat_history WHERE username=%s", (username,))
        conn.commit()
        cur.close()
        conn.close()

    def get_profile(self, username):
        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute("SELECT student_profile FROM user WHERE username=%s", (username,))
        res = cur.fetchone()
        cur.close()
        conn.close()

        default = {
            "知识基础": "暂未采集",
            "认知风格": "暂未采集",
            "易错点偏好": "暂未采集",
            "学习目标": "暂未采集",
            "学习历史": "暂未采集",
            "学习习惯": "暂未采集"
        }
        if not res or res[0] is None:
            return default
        try:
            if isinstance(res[0], str):
                return json.loads(res[0])
            return res[0]
        except:
            return default

    def save_profile(self, username, data):
        js = json.dumps(data, ensure_ascii=False)
        conn = self.db_conn()
        cur = conn.cursor()
        cur.execute("UPDATE user SET student_profile=%s WHERE username=%s", (js, username))
        conn.commit()
        cur.close()
        conn.close()

    def init_llm(self):
        self.llm = ChatOpenAI(
            model=self.ai_model,
            api_key=self.ai_key,
            base_url=self.ai_url,
            temperature=0.1
        )

    def ai_text(self, prompt):
        if not self.llm:
            raise HTTPException(400, "请先配置AI")
        return self.llm.invoke(prompt).content.strip()

    def ai_json(self, prompt):
        raw = self.ai_text(prompt).replace("```json", "").replace("```", "").strip()
        return json.loads(raw)