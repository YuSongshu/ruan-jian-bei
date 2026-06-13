# 多智能体部分
import json
from typing import TypedDict, Annotated, Sequence

import mysql.connector
# FastAPI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# AI 记忆模块
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

# ---------------------------
# AI 模板系统
# ---------------------------
AI_PROMPT_TEMPLATES = {
    "study_profile_extract": """
你是专业教育数据分析师，从学生自然语言中抽取**6个核心维度**学习画像，严格输出JSON，不要多余内容。
维度：知识基础、认知风格、易错点偏好、学习目标、学习历史、学习习惯。
输入：{user_input}
输出JSON格式：
{{
    "知识基础": "",
    "认知风格": "",
    "易错点偏好": "",
    "学习目标": "",
    "学习历史": "",
    "学习习惯": ""
}}
"""
}


def call_ai_by_template(template_id: str, params: dict, parse_json: bool = False):
    from fastapi import HTTPException
    if template_id not in AI_PROMPT_TEMPLATES:
        return {"error": f"模板 {template_id} 不存在"} if parse_json else "模板不存在"

    try:
        prompt = AI_PROMPT_TEMPLATES[template_id].format(**params)
    except KeyError as e:
        return {"error": f"缺少参数：{e}"} if parse_json else f"缺少参数：{e}"

    # 调用全局已配置的 LLM
    if not llm:
        raise HTTPException(status_code=400, detail="请先完成AI配置")

    result = llm.invoke(prompt).content.strip()

    if parse_json:
        try:
            result = result.replace("```json", "").replace("```", "").strip()
            return json.loads(result)
        except:
            return {"error": "JSON解析失败", "原始内容": result}
    return result

app = FastAPI()

# FastAPI 的跨域（CORS）中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局配置
global_config = {
    "mysql_host": "localhost",
    "mysql_user": "root",
    "mysql_password": "",
    "mysql_database": "",
    "ai_model": "",
    "ai_api_key": "",
    "ai_base_url": ""
}

llm = None
db_configured = False


# ---------------------------
# 请求模型定义
# ---------------------------
class AllConfig(BaseModel):
    mysql_host: str
    mysql_user: str
    mysql_password: str
    mysql_database: str
    ai_model: str
    ai_api_key: str
    ai_base_url: str


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class StudyRequest(BaseModel):
    topic: str
    question: str


class ChatRequest(BaseModel):
    username: str
    message: str


class EditUsernameReq(BaseModel):
    old_name: str
    new_name: str

class EditPwdReq(BaseModel):
    username: str
    old_pwd: str
    new_pwd: str

class UsernameReq(BaseModel):
    username: str





# ---------------------------
# 配置接口
# ---------------------------
@app.post("/api/set-all-config")
def set_all_config(config: AllConfig):
    global global_config, llm, db_configured

    try:
        global_config["mysql_host"] = config.mysql_host
        global_config["mysql_user"] = config.mysql_user
        global_config["mysql_password"] = config.mysql_password
        global_config["mysql_database"] = config.mysql_database
        global_config["ai_model"] = config.ai_model
        global_config["ai_api_key"] = config.ai_api_key
        global_config["ai_base_url"] = config.ai_base_url

        db_configured = True

        llm = ChatOpenAI(
            model=config.ai_model,
            api_key=config.ai_api_key,
            base_url=config.ai_base_url,
            temperature=0.1
        )

        return {"status": "success", "msg": "✅ 配置成功！"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI配置失败：{str(e)}")


# ---------------------------
# 数据库连接
# ---------------------------
def get_db():
    if not db_configured:
        raise HTTPException(status_code=400, detail="请先完成配置")

    try:
        return mysql.connector.connect(
            host=global_config["mysql_host"],
            user=global_config["mysql_user"],
            password=global_config["mysql_password"],
            database=global_config["mysql_database"]
        )
    except:
        raise HTTPException(status_code=500, detail="数据库连接失败")


# ---------------------------
# 注册
# ---------------------------
@app.post("/register")
def register(user: UserCreate):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT username FROM user WHERE username=%s", (user.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="用户名已存在")

        cursor.execute(
            "INSERT INTO user (username,password) VALUES (%s,%s)",
            (user.username, user.password)
        )
        db.commit()
        return {"msg": "注册成功"}

    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=500, detail="注册失败")


# ---------------------------
# 登录
# ---------------------------
@app.post("/login")
def login(user: UserLogin):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user WHERE username=%s", (user.username,))
        row = cursor.fetchone()

        if not row or user.password != row["password"]:
            raise HTTPException(status_code=401, detail="账号或密码错误")

        return {"msg": "登录成功"}

    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=500, detail="登录失败")


# ---------------------------
# 学习模块
# ---------------------------
class State(TypedDict):
    topic: str
    messages: Annotated[Sequence[BaseMessage], "messages"]
    study_material: str
    answer: str
    exam: str


def teacher_node(state):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是专业教师，生成清晰、简洁的学习资料。"),
        MessagesPlaceholder(variable_name="messages"),
        ("user", "主题：{topic}")
    ])
    material = (prompt | llm | StrOutputParser()).invoke({
        "topic": state["topic"],
        "messages": state["messages"]
    })
    return {"study_material": material, "messages": state["messages"] + [AIMessage(content=material)]}


def qa_node(state):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "结合学习资料通俗解答问题。"),
        MessagesPlaceholder(variable_name="messages"),
    ])
    answer = (prompt | llm | StrOutputParser()).invoke({"messages": state["messages"]})
    return {"answer": answer, "messages": state["messages"] + [AIMessage(content=answer)]}


def exam_node(state):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "生成3道选择题+答案+解析。"),
        MessagesPlaceholder(variable_name="messages"),
    ])
    exam = (prompt | llm | StrOutputParser()).invoke({"messages": state["messages"]})
    return {"exam": exam}


@app.post("/api/get-study-material")
def study(req: StudyRequest):
    if not llm:
        raise HTTPException(status_code=400, detail="请先完成AI配置")

    try:
        teacher_result = teacher_node({
            "topic": req.topic,
            "messages": [HumanMessage(content=f"主题：{req.topic}")]
        })
        qa_result = qa_node({
            "topic": req.topic,
            "messages": [
                HumanMessage(content=f"主题：{req.topic}"),
                AIMessage(content=teacher_result["study_material"]),
                HumanMessage(content=req.question)
            ]
        })
        exam_result = exam_node({
            "messages": [
                HumanMessage(content=f"主题：{req.topic}"),
                AIMessage(content=teacher_result["study_material"])
            ]
        })
        return {
            "study_content": teacher_result["study_material"],
            "answer": qa_result["answer"],
            "questions": exam_result["exam"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI生成失败：{str(e)}")


# ---------------------------
# 学生学习画像
# ---------------------------
class AutoUpdateProfileRequest(BaseModel):
    username: str
def get_user_profile(username):
    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT student_profile FROM user WHERE username=%s", (username,))
        result = cursor.fetchone()

        return json.loads(result[0])

    except Exception as e:
        print("获取画像错误:", e)
        return {}
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()


#保存用户画像
def save_user_profile(username, profile_data):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        profile_json = json.dumps(profile_data, ensure_ascii=False)

        cursor.execute(
            "UPDATE user SET student_profile=%s WHERE username=%s",(profile_json, username)
        )
        db.commit()

        return True

    except Exception as e:
        print("保存画像错误:", e)
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()


@app.post("/api/update-profile")
def update_profile(data: dict):
    username = data.get("username")
    new_content = data.get("new_content", "")
    old_profile = get_user_profile(username)

    if not old_profile:
        old_profile = {
            "知识基础": "暂未采集",
            "认知风格": "暂未采集",
            "易错点偏好": "暂未采集",
            "学习目标": "暂未采集",
            "学习历史": "暂未采集",
            "学习习惯": "暂未采集"
        }
        save_user_profile(username, old_profile)
    if new_content.strip():
        update_prompt = f"""基于旧画像，结合学生最新学习对话内容，动态更新6维学生画像，只返回纯JSON：
旧画像数据：{old_profile}
学生最新学习内容：{new_content}
保留6个固定维度：知识基础、认知风格、易错点偏好、学习目标、学习历史、学习习惯
"""
        res = llm.invoke(update_prompt)
        # 清洗AI返回内容
        profile_str = res.content.replace("```json", "").replace("```", "").strip()
        new_profile = json.loads(profile_str)
        save_user_profile(username, new_profile)
        return new_profile
    else:
        return old_profile


# ---------------------------
# 记忆对话模块
# ---------------------------

def save_chat_message(username, role, content):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO chat_history (username, role, content) VALUES (%s, %s, %s)",
            (username, role, content)
        )
        db.commit()
    except Exception as e:
        print("保存失败:", e)
    finally:
        try:
            cursor.close()
            db.close()
        except:
            pass

def get_chat_history(username):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT role, content FROM chat_history WHERE username=%s ORDER BY id ASC",
            (username,)
        )
        rows = cursor.fetchall()
        history = []
        for role, content in rows:
            if role == "user":
                history.append(HumanMessage(content=content))
            else:
                history.append(AIMessage(content=content))
        return history
    except:
        return []
    finally:
        try:
            cursor.close()
            db.close()
        except:
            pass

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是专业学习助手，有超强记忆。"),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])

def get_memory_chain():
    if not llm:
        raise HTTPException(status_code=400, detail="请先完成AI配置")

    from langchain_core.chat_history import InMemoryChatMessageHistory
    store = {}

    def get_store(session_id):
        if session_id not in store:
            store[session_id] = InMemoryChatMessageHistory()

            for msg in get_chat_history(session_id):
                store[session_id].add_message(msg)
        return store[session_id]

    return RunnableWithMessageHistory(
        prompt | llm,
        get_store,
        input_messages_key="input",
        history_messages_key="history"
    )

@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        chain = get_memory_chain()
        response = chain.invoke(
            {"input": req.message},
            config={"configurable": {"session_id": req.username}}
        )

        save_chat_message(req.username, "user", req.message)
        save_chat_message(req.username, "ai", response.content)

        return {"reply": response.content}
    except Exception as e:
        print("报错：", e)
        raise HTTPException(status_code=500, detail="发送失败")

# 加载用户聊天历史


class UsernameReq(BaseModel):
    username: str

@app.post("/api/load-chat-history")
def load_chat_history(req: UsernameReq):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT role, content FROM chat_history WHERE username=%s ORDER BY id ASC",(req.username,))
        rows = cursor.fetchall()

        result = []
        for role, content in rows:
            result.append({
                "role": role,
                "content": content
            })

        return result

    except Exception as e:
        print("加载错误:", e)
        return []
    finally:
        try:
            cursor.close()
            db.close()
        except:
            pass


# ---------------------------
# 设置
# ---------------------------
@app.post("/api/update-username")
def edit_username(req: EditUsernameReq):
    db = get_db()
    cursor = db.cursor()
    # 检查新用户名是否重复
    cursor.execute("SELECT id FROM user WHERE username=%s", (req.new_name,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="新用户名已存在")
    cursor.execute("UPDATE user SET username=%s WHERE username=%s",(req.new_name, req.old_name))

    db.commit()
    cursor.close()
    db.close()
    return {"msg":"修改成功"}


@app.post("/api/update-pwd")
def edit_pwd(req: EditPwdReq):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user WHERE username=%s", (req.username,))
    row = cursor.fetchone()
    if not row or row["password"] != req.old_pwd:
        raise HTTPException(status_code=400, detail="原密码错误")
    cursor.execute("UPDATE user SET password=%s WHERE username=%s",(req.new_pwd, req.username))
    db.commit()
    cursor.close()
    db.close()
    return {"msg":"密码修改成功"}


@app.post("/api/clear-chat")
def clear_chat(req: UsernameReq):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM chat_history WHERE username=%s", (req.username,))
    db.commit()
    cursor.close()
    db.close()
    return {"msg":"清空成功"}

@app.post("/api/del-user")
def del_user(req: UsernameReq):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM user WHERE username=%s", (req.username,))
    db.commit()
    cursor.close()
    db.close()
    return {"msg":"账号已注销"}






if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)