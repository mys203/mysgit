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

/**
 * 获取当前登录用户信息（携带 token 的受保护接口）
 * @returns {Promise<Object>} 后端 data 部分：用户信息对象
 */
export function getUserInfo() {
  return request({
    url: '/user/info',
    method: 'get'
  })
}

/**
 * 更新当前登录用户信息
 * @param {Object} data 更新参数，username 必填，其余字段按需传入：
 *   { username, nickname?, avatar?, gender?, bio?, phone? }
 * @returns {Promise<{ phone, nickname, avatar, gender, bio }>} 后端 data 部分：更新后的字段
 */
export function updateUser(data) {
  return request({
    url: '/user/update',
    method: 'put',
    data
  })
}

/**
 * 修改当前登录用户密码
 * @param {Object} data 修改参数 { username, old_password, new_password }
 * @returns {Promise<null>} 后端 data 部分为 null，成功即代表修改完成
 */
export function changePassword(data) {
  return request({
    url: '/user/password',
    method: 'put',
    data
  })
}
