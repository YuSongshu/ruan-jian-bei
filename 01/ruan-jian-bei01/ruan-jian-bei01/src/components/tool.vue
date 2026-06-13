<template>
  <div class="page">
    <!-- 配置 -->
    <div v-if="page === 'config'">
      <div class="config-box">
        <h2>⚙️ 系统配置</h2>
        <p class="subtitle">请先配置数据库与AI模型</p>

        <div class="section">
          <h3>🗄️ MySQL 配置</h3>
          <input v-model="config.mysql_host" placeholder="MySQL 主机" />
          <input v-model="config.mysql_user" placeholder="MySQL 用户名" />
          <input v-model="config.mysql_password" placeholder="MySQL 密码" type="password" />
          <input v-model="config.mysql_database" placeholder="数据库名" />
        </div>

        <div class="section">
          <h3>🤖 AI 配置</h3>
          <input v-model="config.ai_model" placeholder="模型名称" />
          <input v-model="config.ai_api_key" placeholder="API Key" />
          <input v-model="config.ai_base_url" placeholder="Base URL" />
        </div>

        <button class="btn save" @click="saveAllConfig">保存并进入系统</button>
      </div>
    </div>

    <!-- 登录 -->
    <div v-else-if="page === 'login'">
      <div class="login-box">
        <h2>AI 学习助手</h2>
        <p class="subtitle">探索知识，提升自我</p>
        <input v-model="username" placeholder="用户名" />
        <input v-model="password" placeholder="密码" type="password" />
        <button class="btn login" @click="handleLogin">登录</button>
        <button class="btn register" @click="handleRegister">注册</button>
      </div>
    </div>

    <div v-else class="main-layout">
      <!-- 学习资料 -->
      <div class="panel">
        <h2>📚 学习资料</h2>
        <div class="input-group">
          <input v-model="topic" placeholder="学习主题" />
          <input v-model="question" placeholder="你的疑问" />
          <button class="btn primary" @click="getData" :disabled="loading">
            {{ loading ? "请稍等，生成中..." : "开始生成" }}
          </button>
        </div>
        <div class="output" v-if="result">
          <div class="card"><label>学习内容</label><pre>{{ result.study_content }}</pre></div>
          <div class="card"><label>问题解答</label><pre>{{ result.answer }}</pre></div>
          <div class="card"><label>练习题</label><pre>{{ result.questions }}</pre></div>
        </div>
      </div>

      <!-- 切换面板 -->
      <div class="panel">
        <!-- 切换按钮 -->
        <div class="tab-buttons">
          <button @click="activeTab = 'profile'" :class="['tab-btn', activeTab === 'profile' ? 'active' : '']">学生画像</button>
          <button @click="activeTab = 'chat'" :class="['tab-btn', activeTab === 'chat' ? 'active' : '']">记忆智能体</button>
          <button @click="activeTab = 'setting'" :class="['tab-btn', activeTab === 'setting' ? 'active' : '']">个人设置</button>
          
        </div>

        <!-- 学生画像 -->
        <div v-show="activeTab === 'profile'" class="output">
          <h3>👤 学生画像</h3>
          <p>知识基础、认知风格、易错点偏好、学习目标、学习历史、学习习惯</p>
          <p>示例：我是计算机专业大二学生，正在学Python和数据结构，已经掌握基础语法，但链表、递归总是搞不懂，做题经常逻辑错误；喜欢看视频+动手写代码，每天晚上学2小时，目标是本学期掌握数据结构，能独立写算法题，之前学过C语言，刷题时数组、循环没问题，指针和递归容易错</p>

         

          <div class="output" v-if="profileResult">
            <div class="card" v-if="typeof profileResult === 'object'">
              <label>知识基础</label><div>{{ profileResult.知识基础 }}</div>
            </div>
            <div class="card" v-if="typeof profileResult === 'object'">
              <label>认知风格</label><div>{{ profileResult.认知风格 }}</div>
            </div>
            <div class="card" v-if="typeof profileResult === 'object'">
              <label>易错点偏好</label><div>{{ profileResult.易错点偏好 }}</div>
            </div>
            <div class="card" v-if="typeof profileResult === 'object'">
              <label>学习目标</label><div>{{ profileResult.学习目标 }}</div>
            </div>
            <div class="card" v-if="typeof profileResult === 'object'">
              <label>学习历史</label><div>{{ profileResult.学习历史 }}</div>
            </div>
            <div class="card" v-if="typeof profileResult === 'object'">
              <label>学习习惯</label><div>{{ profileResult.学习习惯 }}</div>
            </div>
          </div>
        </div>

        <!-- 记忆智能体 -->
        <div v-show="activeTab === 'chat'" class="output">
          <h3>⭐ 记忆智能体</h3>
          <div class="chat-box">
            <div class="msg-list" ref="msgList">
              <div v-for="(msg,i) in messages" :key="i" :class="['msg',msg.role]">
                {{ msg.content }}
              </div>
            </div>
            <div class="chat-input">
              <input v-model="chatText" @keyup.enter="sendChat" placeholder="输入消息..." />
              <button @click="sendChat">发送</button>
            </div>
          </div>
        </div>

        <!-- 个人设置 -->
        <div v-show="activeTab === 'setting'" class="output">
          <h3>⚙️ 个人设置</h3>

          <div class="setting-item">
            <p>当前用户名：{{ username }}</p>
            <input v-model="newUsername" placeholder="输入新用户名" />
            <button class="btn" @click="updateUsername">修改用户名</button>
          </div>

          <div class="setting-item">
            <input v-model="oldPwd" placeholder="原密码" type="password" />
            <input v-model="newPwd" placeholder="新密码" type="password" />
            <button class="btn" @click="updatePassword">修改密码</button>
          </div>

          <div class="setting-item">
            <button class="btn warn" @click="clearChat">清空全部对话</button>
          </div>

          <div class="setting-item">
            <button class="btn danger" @click="logoutAndDel">注销账号</button>
          </div>
          
          <div class="setting-item">
            <button class="btn" @click="reLogin">重新登录</button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>

import './tool_css.css' 
import { ref, onUpdated, watch } from 'vue'
import axios from 'axios'

const page = ref('config')
const activeTab = ref('profile') 
const username = ref('')
const password = ref('')
const config = ref({
  mysql_host: "localhost",
  mysql_user: "root",
  mysql_password: "",
  mysql_database: "ai_study",
  ai_model: "qwen-turbo",
  ai_api_key: "",
  ai_base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
})

// 保存配置
const saveAllConfig = async () => {
  try {
    await axios.post("http://127.0.0.1:8000/api/set-all-config", config.value)
    alert("配置成功！")
    page.value = "login"
  } catch (e) {
    alert(e.response?.data?.detail || "配置失败")
  }
}

// 登录
const handleLogin = async () => {
  try {
    await axios.post("http://127.0.0.1:8000/login", {
      username: username.value,
      password: password.value
    })
    page.value = "dashboard"
    loadProfileFromDB()
  } catch (e) {
    alert("登录失败")
  }
}

// 注册
const handleRegister = async () => {
  try {
    await axios.post("http://127.0.0.1:8000/register", {
      username: username.value,
      password: password.value
    })
    alert("注册成功")
  } catch (e) {
    alert("注册失败")
  }
}

// 获取学习资料
const topic = ref('')
const question = ref('')
const loading = ref(false)
const result = ref(null)

const getData = async () => {
  loading.value = true
  try {
    const res = await axios.post("http://127.0.0.1:8000/api/get-study-material", {
      topic: topic.value,
      question: question.value
    })
    result.value = res.data
    await autoUpdateProfile("学习主题：" + topic.value + "，问题：" + question.value);
  } catch (e) {
    alert("请求失败")
  }
  loading.value = false
}

// 获取学生画像
const profileResult = ref(null)

const loadProfileFromDB = async () => {
  if (!username.value) return
  try {
    const res = await axios.post("http://127.0.0.1:8000/api/update-profile", {
      username: username.value
    })
    profileResult.value = res.data
  } catch (err) {
    console.log("读取画像失败", err)
  }
}

const autoUpdateProfile = async (newContent) => {
  try {
    const res = await axios.post("http://127.0.0.1:8000/api/update-profile", {
      username: username.value,   
      
      new_content: newContent      
    });
    
    profileResult.value = res.data;
  } catch (e) {
    console.log("画像自动更新失败", e);
  }
};

// 发送聊天 记忆智能体
const chatText = ref('')
const messages = ref([])
const msgList = ref(null)  //作用：让聊天框自动滚动到底部

const sendChat = async () => {
  if (!chatText.value) return
  const text = chatText.value
  messages.value.push({ role: 'user', content: text })
  chatText.value = ''

  try {
    const res = await axios.post("http://127.0.0.1:8000/api/chat", {
      username: username.value,
      message: text
    })
    messages.value.push({ role: 'ai', content: res.data.reply })
    await autoUpdateProfile(text + res.data.reply)
  } catch (e) {
    alert("发送失败")
  }
}

const loadChatHistory = async () => {
  if (!username.value) return

  try {
    const res = await axios.post("http://127.0.0.1:8000/api/load-chat-history", {
      username: username.value
    })
    
    messages.value = res.data
  } catch (err) {
    console.log("加载聊天记录失败", err)
  }
}


//设置
const newUsername = ref('')
const oldPwd = ref('')
const newPwd = ref('')

const updateUsername = async () => {
  if(!newUsername.value) return alert("请输入新用户名")
  try {
    await axios.post("http://127.0.0.1:8000/api/update-username",{
      old_name: username.value,
      new_name: newUsername.value
    })
    username.value = newUsername.value
    newUsername.value = ''
    alert("用户名修改成功")
  }catch(e){
    alert(e.response?.data?.detail || "修改失败")
  }
}

const updatePassword = async () => {
  if(!oldPwd.value || !newPwd.value) return alert("请完整填写")
  try {
    await axios.post("http127.0.0.1:8000/api/update-pwd",{
      username: username.value,
      old_pwd: oldPwd.value,
      new_pwd: newPwd.value
    })
    oldPwd.value = ''
    newPwd.value = ''
    alert("密码修改成功，请重新登录")
    page.value = "login"
  }catch(e){
    alert(e.response?.data?.detail || "修改失败")
  }
}

const clearChat = async () => {
  if(!confirm("确定清空所有聊天记录？不可恢复")) return
  try {
    await axios.post("http://127.0.0.1:8000/api/clear-chat",{
      username: username.value
    })
    messages.value = []
    alert("对话已清空")
  }catch(e){
    alert("清空失败")
  }
}

const logoutAndDel = async () => {
  if(!confirm("确定注销账号？账号和所有数据将永久删除")) return
  try {
    await axios.post("http://127.0.0.1:8000/api/del-user",{
      username: username.value
    })
    page.value = "login"
    username.value = ''
    alert("账号已注销")
  }catch(e){
    alert("注销失败")
  }
}

const reLogin = () => {
  if(!confirm("确定退出当前账号？")) return
  username.value = ''
  messages.value = []
  profileResult.value = null
  
  page.value = "login"
  alert("已退出，请重新登录")
}

// 自动滚动到底部
onUpdated(() => {
  if (msgList.value) {
    msgList.value.scrollTop = msgList.value.scrollHeight
  }
})


// 监听标签切换
watch(activeTab, (newTab) => {
  if (newTab === 'profile') {
    loadProfileFromDB()
  }
  if (newTab === 'chat') {
    loadChatHistory()
  }
})

</script>
