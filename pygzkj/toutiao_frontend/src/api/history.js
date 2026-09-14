import request from './request'

/**
 * 记录一条浏览历史（后端对重复浏览做了幂等处理：已存在则更新浏览时间，不存在则新增）
 * @param {number} newsId 新闻 ID
 * @returns {Promise<{ news_id: number }>} 后端 data 部分：{ news_id }
 */
export function addNewsHistory(newsId) {
  return request({
    url: '/history/add',
    method: 'post',
    data: { newsId }
  })
}

/**
 * 获取当前登录用户的浏览历史列表（分页，按浏览时间倒序）
 * @param {Object} params { page, pageSize }
 * @returns {Promise<{ List: Array, total: number, hasMore: boolean }>}
 */
export function getHistoryList(params = {}) {
  return request({
    url: '/history/list',
    method: 'get',
    params
  })
}
