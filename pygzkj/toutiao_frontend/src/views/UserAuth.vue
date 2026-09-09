<script setup>
import { ref, computed } from 'vue'
import { loginUser, registerUser, getUserInfo, updateUser, changePassword } from '../api/users'
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

// 编辑资料相关状态
const editing = ref(false)
const updating = ref(false)
const editForm = ref({
  nickname: '',
  avatar: '',
  gender: 'unknown',
  bio: '',
  phone: ''
})

const isLogin = computed(() => mode.value === 'login')
// 已登录状态：token 存在即视为已登录
const isLoggedIn = computed(() => !!authState.token)
// 当前用户信息与令牌（登录后持久化到 localStorage）
const userinfo = computed(() => authState.userinfo)
const token = computed(() => authState.token)

// 修改密码相关状态
const changingPwd = ref(false)
const pwdUpdating = ref(false)
const pwdSuccess = ref('')
const pwdForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 三个密码框都非空时才允许提交修改
const canSubmitPwd = computed(
  () =>
    pwdForm.value.oldPassword !== '' &&
    pwdForm.value.newPassword !== '' &&
    pwdForm.value.confirmPassword !== ''
)

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

// 进入编辑模式：用当前用户信息预填表单
function startEdit() {
  const u = authState.userinfo || {}
  editForm.value = {
    nickname: u.nickname || '',
    avatar: u.avatar || '',
    gender: u.gender || 'unknown',
    bio: u.bio || '',
    phone: u.phone || ''
  }
  editing.value = true
  error.value = ''
}

// 取消编辑，恢复展示模式
function cancelEdit() {
  editing.value = false
  error.value = ''
}

// 提交修改：调用 /user/update，成功后合并返回字段并退出编辑
async function submitUpdate() {
  updating.value = true
  error.value = ''
  try {
    // username 用于后端定位要更新的用户，必传
    const payload = { username: authState.userinfo?.username }
    const f = editForm.value
    // 只提交用户实际填写的字段，未填写的字段后端会保持原样
    if (f.nickname.trim()) payload.nickname = f.nickname.trim()
    if (f.avatar.trim()) payload.avatar = f.avatar.trim()
    if (f.bio.trim()) payload.bio = f.bio.trim()
    if (f.phone.trim()) payload.phone = f.phone.trim()
    if (f.gender) payload.gender = f.gender

    const updated = await updateUser(payload)
    // 用后端返回的最新字段合并到本地用户信息，token 保持不变
    setAuth(authState.token, { ...authState.userinfo, ...updated })
    editing.value = false
  } catch (e) {
    error.value = e.message || '更新失败，请稍后重试'
  } finally {
    updating.value = false
  }
}

// 进入修改密码模式
function startChangePwd() {
  pwdForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
  pwdSuccess.value = ''
  error.value = ''
  changingPwd.value = true
}

// 取消修改密码
function cancelChangePwd() {
  changingPwd.value = false
  pwdSuccess.value = ''
  error.value = ''
}

// 提交修改密码：调用 /user/password，成功后提示并退出修改
async function submitChangePwd() {
  error.value = ''
  pwdSuccess.value = ''
  const f = pwdForm.value
  if (!f.oldPassword) {
    error.value = '请输入原密码'
    return
  }
  if (!f.newPassword) {
    error.value = '请输入新密码'
    return
  }
  if (f.newPassword.length < 6) {
    error.value = '新密码至少 6 位'
    return
  }
  if (f.newPassword === f.oldPassword) {
    error.value = '新密码不能与原密码相同'
    return
  }
  if (f.newPassword !== f.confirmPassword) {
    error.value = '两次输入的新密码不一致'
    return
  }

  pwdUpdating.value = true
  try {
    // username 用于后端定位要改密码的用户，必传
    await changePassword({
      username: authState.userinfo?.username,
      old_password: f.oldPassword,
      new_password: f.newPassword
    })
    pwdSuccess.value = '密码修改成功'
    changingPwd.value = false
  } catch (e) {
    error.value = e.message || '密码修改失败，请稍后重试'
  } finally {
    pwdUpdating.value = false
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

      <ul v-if="!editing && !changingPwd" class="info-list">
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
        <li v-if="userinfo?.phone" class="info-item">
          <span class="info-key">手机号</span>
          <span class="info-val">{{ userinfo?.phone }}</span>
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

      <!-- 编辑资料表单 -->
      <form v-else-if="editing" class="edit-form" @submit.prevent="submitUpdate">
        <label class="field">
          <span class="field-label">昵称</span>
          <input
            v-model="editForm.nickname"
            class="field-input"
            type="text"
            placeholder="请输入昵称"
            maxlength="50"
          />
        </label>

        <label class="field">
          <span class="field-label">头像 URL</span>
          <input
            v-model="editForm.avatar"
            class="field-input"
            type="text"
            placeholder="请输入头像图片地址"
          />
        </label>

        <label class="field">
          <span class="field-label">性别</span>
          <select v-model="editForm.gender" class="field-input">
            <option value="male">男</option>
            <option value="female">女</option>
            <option value="unknown">保密</option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">手机号</span>
          <input
            v-model="editForm.phone"
            class="field-input"
            type="text"
            placeholder="请输入手机号"
            maxlength="20"
          />
        </label>

        <label class="field">
          <span class="field-label">个人简介</span>
          <textarea
            v-model="editForm.bio"
            class="field-input bio-input"
            placeholder="介绍一下自己吧~"
            maxlength="500"
          ></textarea>
        </label>

        <div v-if="error" class="error-box">{{ error }}</div>

        <div class="action-row">
          <button class="submit-btn" type="submit" :disabled="updating">
            <span v-if="updating" class="btn-spinner" aria-label="保存中"></span>
            <span v-else>保存修改</span>
          </button>
          <button class="submit-btn secondary" type="button" :disabled="updating" @click="cancelEdit">取消</button>
        </div>
      </form>

      <!-- 修改密码表单 -->
      <form v-else class="edit-form" @submit.prevent="submitChangePwd">
        <label class="field">
          <span class="field-label">原密码</span>
          <input
            v-model="pwdForm.oldPassword"
            class="field-input"
            type="password"
            placeholder="请输入原密码"
            autocomplete="current-password"
          />
        </label>

        <label class="field">
          <span class="field-label">新密码</span>
          <input
            v-model="pwdForm.newPassword"
            class="field-input"
            type="password"
            placeholder="请输入新密码（至少 6 位）"
            autocomplete="new-password"
          />
        </label>

        <label class="field">
          <span class="field-label">确认新密码</span>
          <input
            v-model="pwdForm.confirmPassword"
            class="field-input"
            type="password"
            placeholder="请再次输入新密码"
            autocomplete="new-password"
          />
        </label>

        <div v-if="error" class="error-box">{{ error }}</div>

        <div class="action-row">
          <button class="submit-btn" type="submit" :disabled="!canSubmitPwd || pwdUpdating">
            <span v-if="pwdUpdating" class="btn-spinner" aria-label="提交中"></span>
            <span v-else>确认修改</span>
          </button>
          <button class="submit-btn secondary" type="button" :disabled="pwdUpdating" @click="cancelChangePwd">取消</button>
        </div>
      </form>

      <div v-if="!editing && !changingPwd && pwdSuccess" class="success-box">{{ pwdSuccess }}</div>

      <div v-if="!editing && !changingPwd && error" class="error-box">{{ error }}</div>

      <div v-if="!editing && !changingPwd" class="action-row">
        <button class="submit-btn" :disabled="refreshing" @click="refreshInfo">
          <span v-if="refreshing" class="btn-spinner" aria-label="刷新中"></span>
          <span v-else>刷新个人信息</span>
        </button>
        <button class="submit-btn secondary" @click="startEdit">编辑资料</button>
        <button class="submit-btn secondary" @click="startChangePwd">修改密码</button>
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

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 20px;
  text-align: left;
}

.bio-input {
  resize: vertical;
  min-height: 80px;
  font-family: inherit;
  line-height: 1.5;
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

.success-box {
  margin-top: 16px;
  padding: 10px 14px;
  border: 1px solid #d4f0d8;
  border-radius: 8px;
  background: #f0fbf2;
  color: #1f8f3a;
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
