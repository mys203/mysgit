import request from './request'

/**
 * 检查某条新闻是否已被当前登录用户收藏
 * @param {number} newsId 新闻 ID
 * @returns {Promise<{ isFavorite: boolean }>} 后端 data 部分：{ isFavorite }
 */
export function checkFavorite(newsId) {
  return request({
    url: '/favorite/check',
    method: 'get',
    params: { newsId }
  })
}

/**
 * 收藏某条新闻（后端对重复收藏做了幂等处理，重复添加直接返回已有记录）
 * @param {number} newsId 新闻 ID
 * @returns {Promise<{ news_id: number }>} 后端 data 部分：{ news_id }
 */
export function addFavorite(newsId) {
  return request({
    url: '/favorite/add',
    method: 'post',
    data: { newsId }
  })
}

/**
 * 取消收藏某条新闻
 * @param {number} newsId 新闻 ID
 * @returns {Promise} 后端删除成功后 data 为空，走统一成功返回
 */
export function removeFavorite(newsId) {
  return request({
    url: '/favorite/remove',
    method: 'delete',
    params: { newsId }
  })
}

/**
 * 获取当前登录用户的收藏列表（分页）
 * @param {Object} params { page, pageSize }
 * @returns {Promise<{ List: Array, total: number, hasMore: boolean }>}
 */
export function getFavoriteList(params = {}) {
  return request({
    url: '/favorite/list',
    method: 'get',
    params
  })
}
