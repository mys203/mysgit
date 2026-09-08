<script setup>
import { ref, computed } from 'vue'
import { loginUser, registerUser, getUserInfo } from '../api/users'
import { authState, setAuth, clearAuth } from '../utils/auth'

// 当前模式：login 登录 / register 注册
const mode = ref('login')

const form = ref({
  username: '',
  password: '',
  confirmPassword: ''
})

const loading = ref(false)
const refreshing = ref(false)
const error = ref('')

const isLogin = computed(() => mode.value === 'login')
// 已登录状态：token 存在即视为已登录
const isLoggedIn = computed(() => !!authState.token)
// 当前用户信息与令牌（登录后持久化到 localStorage）
const userinfo = computed(() => authState.userinfo)
const token = computed(() => authState.token)

// 用户名和密码都非空时才允许提交
const canSubmit = computed(
  () => form.value.username.trim() !== '' && form.value.password !== ''
)

// 性别枚举值 → 中文展示
function genderLabel(value) {
  if (value === 'male') return '男'
  if (value === 'female') return '女'
  return '保密'
}

// 客户端校验，返回错误文案（空串表示通过）
function validate() {
  const username = form.value.username.trim()
  const password = form.value.password
  if (!username) return '请输入用户名'
  if (username.length < 2 || username.length > 20) return '用户名长度需在 2-20 个字符之间'
  if (!password) return '请输入密码'
  if (!isLogin.value) {
    if (password.length < 6) return '密码至少 6 位'
    if (password !== form.value.confirmPassword) return '两次输入的密码不一致'
  }
  return ''
}

async function handleSubmit() {
  const msg = validate()
  if (msg) {
    error.value = msg
    return
  }
  loading.value = true
  error.value = ''
  try {
    const payload = {
      username: form.value.username.trim(),
      password: form.value.password
    }
    // 响应拦截器已剥掉 code/msg/data，这里拿到的是后端 data 内容 { token, userinfo }
    const data = isLogin.value ? await loginUser(payload) : await registerUser(payload)
    // 持久化 token 与用户信息，后续请求会自动带上 Authorization 头
    setAuth(data.token, data.userinfo)
  } catch (e) {
    error.value = e.message || '操作失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 切换登录 / 注册，清空表单与提示
function switchMode(target) {
  mode.value = target
  form.value = { username: '', password: '', confirmPassword: '' }
  error.value = ''
}

// 退出登录：清空本地 token，回到登录表单
function handleLogout() {
  clearAuth()
  mode.value = 'login'
  error.value = ''
}

// 使用 token 重新获取最新用户信息（演示受保护的 /user/info 接口）
async function refreshInfo() {
  refreshing.value = true
  error.value = ''
  try {
    const info = await getUserInfo()
    // 用后端返回的最新信息更新本地（token 保持不变）
    setAuth(authState.token, { ...authState.userinfo, ...info })
  } catch (e) {
    error.value = e.message || '获取用户信息失败'
  } finally {
    refreshing.value = false
  }
}
</script>

<template>
  <section class="user-auth">
    <!-- 登录 / 注册表单 -->
    <div v-if="!isLoggedIn" class="auth-card">
      <div class="card-head">
        <div class="logo">👤</div>
        <h2 class="card-title">{{ isLogin ? '欢迎回来' : '创建账号' }}</h2>
        <p class="card-sub">{{ isLogin ? '登录你的头条账号' : '注册头条账号，开启你的阅读之旅' }}</p>
      </div>

      <!-- 模式切换 -->
      <div class="mode-tabs">
        <button
          :class="['mode-tab', { active: isLogin }]"
          @click="switchMode('login')"
        >登录</button>
        <button
          :class="['mode-tab', { active: !isLogin }]"
          @click="switchMode('register')"
        >注册</button>
      </div>

      <form class="auth-form" @submit.prevent="handleSubmit">
        <label class="field">
          <span class="field-label">用户名</span>
          <input
            v-model="form.username"
            class="field-input"
            type="text"
            placeholder="请输入用户名"
            autocomplete="username"
            maxlength="20"
          />
        </label>

        <label class="field">
          <span class="field-label">密码</span>
          <input
            v-model="form.password"
            class="field-input"
            type="password"
            :placeholder="isLogin ? '请输入密码' : '请输入密码（至少 6 位）'"
            autocomplete="current-password"
          />
        </label>

        <label v-if="!isLogin" class="field">
          <span class="field-label">确认密码</span>
          <input
            v-model="form.confirmPassword"
            class="field-input"
            type="password"
            placeholder="请再次输入密码"
            autocomplete="new-password"
          />
        </label>

        <div v-if="error" class="error-box">{{ error }}</div>

        <button class="submit-btn" type="submit" :disabled="!canSubmit || loading">
          <span v-if="loading" class="btn-spinner" aria-label="提交中"></span>
          <span v-else>{{ isLogin ? '登录' : '立即注册' }}</span>
        </button>
      </form>
    </div>

    <!-- 已登录：展示当前用户信息 -->
    <div v-else class="success-card">
      <img
        class="success-avatar"
        :src="userinfo?.avatar"
        :alt="userinfo?.username"
      />
      <h2 class="success-title">欢迎回来 🎉</h2>
      <p class="success-welcome">{{ userinfo?.username }}</p>

      <ul class="info-list">
        <li class="info-item">
          <span class="info-key">用户 ID</span>
          <span class="info-val">{{ userinfo?.id }}</span>
        </li>
        <li class="info-item">
          <span class="info-key">用户名</span>
          <span class="info-val">{{ userinfo?.username }}</span>
        </li>
        <li v-if="userinfo?.nickname" class="info-item">
          <span class="info-key">昵称</span>
          <span class="info-val">{{ userinfo?.nickname }}</span>
        </li>
        <li v-if="userinfo?.gender" class="info-item">
          <span class="info-key">性别</span>
          <span class="info-val">{{ genderLabel(userinfo?.gender) }}</span>
        </li>
        <li v-if="userinfo?.phone_number" class="info-item">
          <span class="info-key">手机号</span>
          <span class="info-val">{{ userinfo?.phone_number }}</span>
        </li>
        <li class="info-item">
          <span class="info-key">个人简介</span>
          <span class="info-val">{{ userinfo?.bio }}</span>
        </li>
        <li class="info-item">
          <span class="info-key">访问令牌</span>
          <span class="info-val token">{{ token }}</span>
        </li>
      </ul>

      <div v-if="error" class="error-box">{{ error }}</div>

      <div class="action-row">
        <button class="submit-btn" :disabled="refreshing" @click="refreshInfo">
          <span v-if="refreshing" class="btn-spinner" aria-label="刷新中"></span>
          <span v-else>刷新个人信息</span>
        </button>
        <button class="submit-btn secondary" @click="handleLogout">退出登录</button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.user-auth {
  max-width: 460px;
  margin: 0 auto;
}

.auth-card,
.success-card {
  background: #fff;
  border-radius: 16px;
  padding: 36px 32px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

/* 卡片头部 */
.card-head {
  text-align: center;
}

.logo {
  width: 56px;
  height: 56px;
  margin: 0 auto 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  border-radius: 50%;
  background: #fff1f0;
}

.card-title {
  font-size: 22px;
  font-weight: 700;
  color: #1f2329;
}

.card-sub {
  margin-top: 6px;
  font-size: 13px;
  color: #8a919f;
}

/* 模式切换 */
.mode-tabs {
  display: flex;
  gap: 4px;
  margin-top: 24px;
  padding: 4px;
  background: #f4f5f7;
  border-radius: 12px;
}

.mode-tab {
  flex: 1;
  padding: 9px 0;
  border: none;
  border-radius: 9px;
  background: transparent;
  color: #8a919f;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.mode-tab.active {
  background: #fff;
  color: #e02e24;
  font-weight: 600;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 20px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  font-size: 14px;
  font-weight: 600;
  color: #1f2329;
}

.field-input {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #e5e6eb;
  border-radius: 10px;
  font-size: 15px;
  color: #1f2329;
  background: #fafbfc;
  outline: none;
  transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}

.field-input:focus {
  border-color: #e02e24;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(224, 46, 36, 0.1);
}

.field-input::placeholder {
  color: #b6bcc6;
}

.error-box {
  padding: 10px 14px;
  border: 1px solid #ffd6d4;
  border-radius: 8px;
  background: #fff1f0;
  color: #e02e24;
  font-size: 13px;
}

.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 13px 16px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #e02e24 0%, #ff5a3c 100%);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease, transform 0.1s ease;
}

.submit-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.submit-btn:active:not(:disabled) {
  transform: translateY(1px);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.submit-btn.secondary {
  margin-top: 24px;
  background: #fff;
  color: #e02e24;
  border: 1px solid #e02e24;
}

.action-row {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.action-row .submit-btn {
  margin-top: 0;
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 成功 */
.success-card {
  text-align: center;
}

.success-avatar {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  object-fit: cover;
  background: #f0f1f3;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.success-title {
  margin-top: 18px;
  font-size: 22px;
  font-weight: 700;
  color: #1f2329;
}

.success-welcome {
  margin-top: 6px;
  font-size: 14px;
  color: #6b7280;
}

.info-list {
  list-style: none;
  margin-top: 24px;
  text-align: left;
  border-top: 1px solid #f0f1f3;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f0f1f3;
}

.info-key {
  flex-shrink: 0;
  width: 72px;
  font-size: 13px;
  color: #8a919f;
}

.info-val {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  color: #1f2329;
  word-break: break-all;
}

.info-val.token {
  color: #e02e24;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
}
</style>
