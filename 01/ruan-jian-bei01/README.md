# Vue 3 + Vite
## 项目简介
本项目基于 **Vue3 + FastAPI + MySQL + 大模型** 开发，是一套多智能体协同个性化学习系统。
实现用户注册登录、系统配置、AI学习资料生成、记忆智能体对话、六维学生画像动态持久化管理核心功能。

### 项目结构

```
├── 前端Vue
│   ├── src
│ 	│ 	└── components
│   │   	├── tool（主页面组件（配置/登录/主面板））
│   │ 		└── tool_css.css 全局样式
│  	├── App.vue
│  	└──main.js
│ 	
├── 后端FastAPI
│   └── main
│
└── 数据库(MySQL)
    └── ai_study 数据库 + 对应数据表
```



## 环境配置
### 前端
1.安装 Node.js
    进入前端目录安装依赖

```
npm install
```

### 后端（python）

#### 虚拟环境

​	打开项目所在的文件夹

​	创建虚拟环境

```
python -m venv .venv
```

依赖目录 	requirements.txt

```
# 核心 Web 框架
fastapi>=0.100.0
uvicorn>=0.23.2
python-multipart>=0.0.6

# 数据库
mysql-connector-python>=8.1.0

# AI & LangChain
langchain>=0.1.0
langchain-openai>=0.0.2
openai>=1.0.0

# 数据工具
pydantic>=2.0.0
json5>=0.9.14
typing-extensions>=4.7.1
```

​	进入后端目录

```
pip install -r requirements.txt
```

### 数据库（MySQL）

```
CREATE DATABASE IF NOT EXISTS ai_study;
USE ai_study;

-- 用户表
DROP TABLE IF EXISTS user;
CREATE TABLE user (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  student_profile JSON NULL
);

-- 聊天历史表
DROP TABLE IF EXISTS chat_history;
CREATE TABLE chat_history (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL,
  role VARCHAR(20) NOT NULL,
  content TEXT NOT NULL,
  create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (username) REFERENCES user(username)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);
```




## 技术栈
### 前端
- 框架：Vue3 + Vite
- 网络请求：Axios
- 核心功能：标签页监听、页面状态管理、接口请求封装

### 后端
- 框架：FastAPI
- 数据库：MySQL
- AI能力：大模型API调用
- 核心接口：配置管理、用户登录注册、学习资料生成、智能体对话、学生画像读写/更新

### 数据库
- 数据表：用户表、学生画像表、对话记忆表
- 数据持久化：画像JSON结构化存储，支持读取旧数据、增量更新





## 项目运行流程
1. 启动后端 FastAPI 服务
2. 启动前端 Vue 项目
3. 首次进入填写 MySQL + AI 配置并保存
4. 注册账号 → 登录系统
5. 正常使用学习资料生成、AI对话功能





## 启动方式
### 后端
```bash
# 启动服务
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 前端
```bash
# 运行项目
cd ruan-jian-bei01
npm run dev
```



## 注意事项
1. 需提前本地安装 MySQL，创建 `ai_study` 数据库
2. AI接口密钥与地址需正确配置，否则无法生成内容



