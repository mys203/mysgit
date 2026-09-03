import axios from 'axios'

// 统一封装的 axios 实例
const request = axios.create({
  baseURL: '/api', // 开发环境由 Vite 代理转发到 http://localhost:8000，避免跨域
  timeout: 10000
})

// 请求拦截器：可在此统一添加 token、公共参数等
request.interceptors.request.use(
  (config) => {
    // 示例：const token = localStorage.getItem('token')
    // if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一处理后端返回结构 { code, msg, data }
request.interceptors.response.use(
  (response) => {
    const res = response.data
    // 后端约定 code === 200 表示成功
    if (res.code === 200) {
      return res.data
    }
    // 业务错误
    const err = new Error(res.msg || '请求失败')
    err.code = res.code
    return Promise.reject(err)
  },
  (error) => {
    // 网络错误 / HTTP 状态码错误
    let msg = '网络异常，请稍后重试'
    if (error.response) {
      const status = error.response.status
      if (status === 404) {
        msg = '接口不存在 (404)'
      } else if (status >= 500) {
        msg = '服务器错误，请稍后重试'
      } else {
        msg = `请求失败 (${status})`
      }
    } else if (error.code === 'ECONNABORTED') {
      msg = '请求超时，请确认后端服务是否已启动'
    }
    const err = new Error(msg)
    err.code = error.response?.status
    return Promise.reject(err)
  }
)

export default request
