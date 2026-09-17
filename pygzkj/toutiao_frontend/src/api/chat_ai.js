import request from './request'

/**
 * 调用 AI 对话接口
 * @param {Object} data 请求参数 { question, session_id? }
 *   - question: 用户这次问的问题
 *   - session_id: 会话ID，不传则后端新建会话并返回
 * @returns {Promise<{ session_id: string, answer: string }>}
 */
export function chatWithAI(data) {
  return request({
    url: '/ai/chat',
    method: 'post',
    data,
    timeout: 60000 // AI 生成较慢，单独放宽超时时间
  })
}

/**
 * 获取某个会话的历史对话，前端切回聊天页时用它恢复内容
 * @param {string} sessionId 会话ID
 * @returns {Promise<{ messages: Array<{ role, content }> }>}
 */
export function getChatHistory(sessionId) {
  return request({
    url: '/ai/history',
    method: 'get',
    params: { session_id: sessionId }
  })
}
