import json
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_openai import ChatOpenAI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import dao

# ===================== 全局变量 =====================
llm = None
db_configured = False

# AI 提示词
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

# ===================== 请求模型 =====================
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

# ===================== AI 智能体 =====================
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

# ===================== 初始化 =====================
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== 接口 =====================
@app.post("/api/set-all-config")
def set_all_config(config: AllConfig):
    global llm, db_configured
    try:
        dao.DB_CONFIG["host"] = config.mysql_host
        dao.DB_CONFIG["user"] = config.mysql_user
        dao.DB_CONFIG["password"] = config.mysql_password
        dao.DB_CONFIG["database"] = config.mysql_database
        dao.DB_READY = True
        db_configured = True

        # 初始化大模型
        llm = ChatOpenAI(
            model=config.ai_model,
            api_key=config.ai_api_key,
            base_url=config.ai_base_url,
            temperature=0.1
        )
        return {"status": "success", "msg": "✅ 配置成功！"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI配置失败：{str(e)}")

# 注册
@app.post("/register")
def register(user: UserCreate):
    if dao.user_exists(user.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    # 默认画像
    default_profile = json.dumps({
        "知识基础": "暂未采集",
        "认知风格": "暂未采集",
        "易错点偏好": "暂未采集",
        "学习目标": "暂未采集",
        "学习历史": "暂未采集",
        "学习习惯": "暂未采集"
    }, ensure_ascii=False)
    dao.add_user(user.username, user.password, default_profile)
    return {"msg": "注册成功"}

# 登录
@app.post("/login")
def login(user: UserLogin):
    row = dao.get_user_info(user.username)
    if not row or row["password"] != user.password:
        raise HTTPException(status_code=401, detail="账号或密码错误")
    return {"msg": "登录成功"}

# 学习资料
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

# 学生画像
@app.post("/api/update-profile")
def update_profile(data: dict):
    username = data.get("username")
    new_content = data.get("new_content", "")
    old_profile_str = dao.get_user_profile(username)

    default_profile = {
        "知识基础": "暂未采集",
        "认知风格": "暂未采集",
        "易错点偏好": "暂未采集",
        "学习目标": "暂未采集",
        "学习历史": "暂未采集",
        "学习习惯": "暂未采集"
    }
    old_profile = default_profile
    if old_profile_str:
        try:
            old_profile = json.loads(old_profile_str)
        except:
            pass

    if not new_content.strip():
        return old_profile

    # AI 更新画像
    update_prompt = f"""基于旧画像，结合学生最新学习对话，更新6维内容，只返回纯JSON：
旧画像：{old_profile}
最新内容：{new_content}
字段：知识基础、认知风格、易错点偏好、学习目标、学习历史、学习习惯"""
    res = llm.invoke(update_prompt)
    profile_str = res.content.replace("```json", "").replace("```", "").strip()
    new_profile = json.loads(profile_str)
    dao.save_user_profile(username, json.dumps(new_profile, ensure_ascii=False))
    return new_profile

# 聊天模块
chat_store = {}
def get_chat_history_msg(sid):
    history = dao.get_chat_records(sid)
    msg_list = []
    for role, content in history:
        if role == "user":
            msg_list.append(HumanMessage(content=content))
        else:
            msg_list.append(AIMessage(content=content))
    return msg_list

def get_store(session_id):
    if session_id not in chat_store:
        chat_store[session_id] = InMemoryChatMessageHistory()
        for msg in get_chat_history_msg(session_id):
            chat_store[session_id].add_message(msg)
    return chat_store[session_id]

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是专业学习助手，有超强记忆。"),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])

@app.post("/api/chat")
def chat(req: ChatRequest):
    if not llm:
        raise HTTPException(status_code=400, detail="请先完成AI配置")
    try:
        chain = RunnableWithMessageHistory(
            prompt | llm,
            get_store,
            input_messages_key="input",
            history_messages_key="history"
        )
        response = chain.invoke(
            {"input": req.message},
            config={"configurable": {"session_id": req.username}}
        )
        # 保存聊天记录
        dao.add_chat_record(req.username, "user", req.message)
        dao.add_chat_record(req.username, "ai", response.content)
        return {"reply": response.content}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="发送失败")

# 加载聊天记录
@app.post("/api/load-chat-history")
def load_chat_history(req: UsernameReq):
    rows = dao.get_chat_records(req.username)
    return [{"role": r, "content": c} for r, c in rows]

# 修改用户名
@app.post("/api/update-username")
def edit_username(req: EditUsernameReq):
    if dao.user_exists(req.new_name):
        raise HTTPException(status_code=400, detail="新用户名已存在")
    dao.update_username(req.old_name, req.new_name)
    return {"msg":"修改成功"}

# 修改密码
@app.post("/api/update-pwd")
def edit_pwd(req: EditPwdReq):
    row = dao.get_user_info(req.username)
    if not row or row["password"] != req.old_pwd:
        raise HTTPException(status_code=400, detail="原密码错误")
    dao.update_user_pwd(req.username, req.new_pwd)
    return {"msg":"密码修改成功"}

# 清空聊天
@app.post("/api/clear-chat")
def clear_chat(req: UsernameReq):
    dao.clear_chat_records(req.username)
    return {"msg":"清空成功"}

# 注销账号
@app.post("/api/del-user")
def del_user(req: UsernameReq):
    dao.delete_user(req.username)
    dao.clear_chat_records(req.username)
    return {"msg":"账号已注销"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)