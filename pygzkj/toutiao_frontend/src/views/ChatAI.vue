<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { chatWithAI, getChatHistory } from '../api/chat_ai'

const SESSION_KEY = 'toutiao_ai_session'

const messages = ref([]) // { role: 'user' | 'assistant', content }
const input = ref('')
const sending = ref(false)
const error = ref('')
const listRef = ref(null)

// 会话 id 持久化到 localStorage，刷新页面后继续同一轮对话
const sessionId = ref(localStorage.getItem(SESSION_KEY) || '')

async function scrollToBottom() {
  await nextTick()
  if (listRef.value) {
    listRef.value.scrollTop = listRef.value.scrollHeight
  }
}

async function send() {
  const q = input.value.trim()
  if (!q || sending.value) return
  messages.value.push({ role: 'user', content: q })
  input.value = ''
  sending.value = true
  error.value = ''
  await scrollToBottom()
  try {
    const res = await chatWithAI({
      question: q,
      session_id: sessionId.value || undefined
    })
    sessionId.value = res.session_id
    localStorage.setItem(SESSION_KEY, res.session_id)
    messages.value.push({ role: 'assistant', content: res.answer })
  } catch (e) {
    error.value = e.message || 'AI 暂时不可用，请稍后再试'
  } finally {
    sending.value = false
    await scrollToBottom()
  }
}

// 新会话：清空记录和本地 session
function newSession() {
  messages.value = []
  sessionId.value = ''
  localStorage.removeItem(SESSION_KEY)
  error.value = ''
  welcome()
}

function welcome() {
  messages.value.push({ role: 'assistant', content: '你好，我是 AI 新闻助手，有什么想了解的都可以问我~' })
}

// 挂载时：有 session 就从后端拉历史恢复，没有就显示开场白
onMounted(async () => {
  if (sessionId.value) {
    try {
      const res = await getChatHistory(sessionId.value)
      messages.value = res.messages || []
      if (messages.value.length === 0) welcome()
    } catch (e) {
      welcome()
    }
  } else {
    welcome()
  }
})
</script>

<template>
  <section class="chat-ai">
    <div class="chat-head">
      <h2 class="chat-title">AI 助手</h2>
      <button class="new-btn" @click="newSession">＋ 新会话</button>
    </div>

    <div ref="listRef" class="chat-list">
      <div
        v-for="(m, i) in messages"
        :key="i"
        :class="['msg-row', m.role]"
      >
        <div class="bubble">{{ m.content }}</div>
      </div>

      <div v-if="sending" class="msg-row assistant">
        <div class="bubble typing">
          <span></span><span></span><span></span>
        </div>
      </div>

      <p v-if="error" class="chat-error">{{ error }}</p>
    </div>

    <form class="chat-input-bar" @submit.prevent="send">
      <input
        v-model="input"
        class="chat-input"
        type="text"
        placeholder="输入你的问题，回车发送…"
        :disabled="sending"
      />
      <button class="send-btn" type="submit" :disabled="!input.trim() || sending">
        {{ sending ? '生成中' : '发送' }}
      </button>
    </form>
  </section>
</template>

<style scoped>
.chat-ai {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 200px);
  min-height: 420px;
  background: #15151a;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 16px;
  overflow: hidden;
}

.chat-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(255, 255, 255, 0.02);
}

.chat-title {
  font-size: 18px;
  font-weight: 700;
  color: #ececf0;
}

.new-btn {
  padding: 7px 16px;
  border: 1px solid rgba(212, 175, 55, 0.5);
  border-radius: 20px;
  background: transparent;
  color: #d4af37;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}
.new-btn:hover {
  background: rgba(212, 175, 55, 0.12);
}

.chat-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.msg-row {
  display: flex;
}
.msg-row.user {
  justify-content: flex-end;
}
.msg-row.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 76%;
  padding: 11px 15px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.user .bubble {
  background: linear-gradient(135deg, #d4af37 0%, #b8962f 100%);
  color: #1a1a1a;
  border-bottom-right-radius: 4px;
}

.assistant .bubble {
  background: #1e1e25;
  color: #ececf0;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-bottom-left-radius: 4px;
}

/* 打字动画 */
.typing {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 14px 16px;
}
.typing span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #d4af37;
  animation: blink 1.2s infinite ease-in-out;
}
.typing span:nth-child(2) {
  animation-delay: 0.2s;
}
.typing span:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes blink {
  0%, 80%, 100% { opacity: 0.2; transform: translateY(0); }
  40% { opacity: 1; transform: translateY(-3px); }
}

.chat-error {
  align-self: center;
  font-size: 13px;
  color: #ff6b6b;
}

.chat-input-bar {
  display: flex;
  gap: 10px;
  padding: 14px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(255, 255, 255, 0.02);
}

.chat-input {
  flex: 1;
  padding: 11px 14px;
  border: 1px solid #2a2a33;
  border-radius: 10px;
  background: #1e1e25;
  color: #ececf0;
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s ease;
}
.chat-input:focus {
  border-color: #d4af37;
}
.chat-input::placeholder {
  color: #6e6e78;
}

.send-btn {
  flex-shrink: 0;
  padding: 0 22px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #d4af37 0%, #b8962f 100%);
  color: #1a1a1a;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease;
}
.send-btn:hover:not(:disabled) {
  opacity: 0.88;
}
.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
