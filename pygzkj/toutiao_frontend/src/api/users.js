import request from './request'

/**
 * 用户注册
 * @param {Object} data 注册参数 { username, password }
 * @returns {Promise<{ token: string, userinfo: { id, username, bio, avatar } }>}
 * 后端响应 data 部分：{ token, userinfo }
 */
export function registerUser(data) {
  return request({
    url: '/user/register',
    method: 'post',
    data
  })
}

/**
 * 用户登录
 * @param {Object} data 登录参数 { username, password }
 * @returns {Promise<{ token: string, userinfo: { id, username, bio, avatar, gender, phone_number } }>}
 * 后端响应 data 部分：{ token, userinfo }
 */
export function loginUser(data) {
  return request({
    url: '/user/login',
    method: 'post',
    data
  })
}
