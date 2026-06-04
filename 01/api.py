from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from method import Method
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

Method = Method()
router = APIRouter()

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

@router.post("/api/set-all-config")
def set_cfg(cfg: AllConfig):
    Method.mysql_host = cfg.mysql_host
    Method.mysql_user = cfg.mysql_user
    Method.mysql_password = cfg.mysql_password
    Method.mysql_db = cfg.mysql_database
    Method.ai_model = cfg.ai_model
    Method.ai_key = cfg.ai_api_key
    Method.ai_url = cfg.ai_base_url
    Method.db_ready = True
    Method.init_llm()
    return {"status": "success", "msg": "✅ 配置成功！"}

@router.post("/register")
def register(u: UserCreate):
    Method.register(u.username, u.password)
    return {"msg": "注册成功"}

@router.post("/login")
def login(u: UserCreate):
    if not Method.login_check(u.username, u.password):
        raise HTTPException(401, "账号或密码错误")
    return {"msg": "登录成功"}

@router.post("/api/update-username")
def rename(req: EditUsernameReq):
    Method.edit_username(req.old_name, req.new_name)
    return {"msg": "修改成功"}

@router.post("/api/update-pwd")
def repwd(req: EditPwdReq):
    Method.edit_pwd(req.username, req.old_pwd, req.new_pwd)
    return {"msg": "密码修改成功"}

@router.post("/api/del-user")
def deluser(req: UsernameReq):
    Method.del_user(req.username)
    return {"msg": "账号已注销"}

@router.post("/api/get-study-material")
def study(req: StudyRequest):
    if not Method.llm:
        raise HTTPException(400, "请先配置AI")

    t_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是专业教师，生成简洁学习资料"),
        ("user", "主题:{topic}")
    ])
    material = t_prompt.invoke({"topic": req.topic})
    material = Method.llm.invoke(material).content

    q_prompt = ChatPromptTemplate.from_messages([
        ("system", "结合资料通俗解答"),
        ("user", f"资料:{material}\n问题:{req.question}")
    ])
    ans = Method.llm.invoke(q_prompt.invoke({})).content

    e_prompt = ChatPromptTemplate.from_messages([
        ("system", "生成3道选择题+答案+解析"),
        ("user", material)
    ])
    exam = Method.llm.invoke(e_prompt.invoke({})).content

    return {"study_content": material, "answer": ans, "questions": exam}

@router.post("/api/update-profile")
def update_profile(data: dict):
    uname = data.get("username")
    content = data.get("new_content", "").strip()
    old = Method.get_profile(uname)
    if not content:
        return old
    prompt = f"""基于旧画像更新6维信息，只返回json
旧画像：{old}
最新对话：{content}
字段：知识基础、认知风格、易错点偏好、学习目标、学习历史、学习习惯"""
    new_p = Method.ai_json(prompt)
    Method.save_profile(uname, new_p)
    return new_p

@router.post("/api/chat")
def chat(req: ChatRequest):
    if not Method.llm:
        raise HTTPException(400, "请先配置AI")

    mem_store = {}
    def get_mem(sid):
        if sid not in mem_store:
            mem_store[sid] = InMemoryChatMessageHistory()
        return mem_store[sid]

    chat_chain = RunnableWithMessageHistory(
        ChatPromptTemplate.from_messages([
            ("system", "你是专业学习助手"),
            MessagesPlaceholder("history"),
            ("human", "{input}")
        ]) | Method.llm,
        get_mem,
        input_messages_key="input",
        history_messages_key="history"
    )

    resp = chat_chain.invoke(
        {"input": req.message},
        config={"configurable": {"session_id": req.username}}
    )
    Method.save_chat(req.username, "user", req.message)
    Method.save_chat(req.username, "ai", resp.content)
    return {"reply": resp.content}

@router.post("/api/load-chat-history")
def load_history(req: UsernameReq):
    return Method.load_chat_plain(req.username)

@router.post("/api/clear-chat")
def clear(req: UsernameReq):
    Method.clear_chat(req.username)
    return {"msg": "清空成功"}