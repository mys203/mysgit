import { reactive } from 'vue'

const TOKEN_KEY = 'toutiao_token'
const USER_KEY = 'toutiao_user'

// 从 localStorage 读取用户信息，实现刷新页面后仍保持登录态
function readUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch (e) {
    return null
  }
}

// 全局登录状态：token + 用户信息（响应式，组件里可直接引用）
export const authState = reactive({
  token: localStorage.getItem(TOKEN_KEY) || '',
  userinfo: readUser()
})

// 登录/注册成功后保存 token 与用户信息
export function setAuth(token, userinfo) {
  authState.token = token
  authState.userinfo = userinfo
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(userinfo))
}

// 退出登录 / token 失效时清空本地登录态
export function clearAuth() {
  authState.token = ''
  authState.userinfo = null
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

// 供请求拦截器读取 token
export function getToken() {
  return authState.token
}
