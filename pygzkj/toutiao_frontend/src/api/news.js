import request from './request'

/**
 * 获取新闻分类列表
 * @param {Object} params 可选查询参数，如 { skip: 0, limit: 100 }
 * @returns {Promise<Array>} 分类数组，元素为 { id, name, sort_order }
 */
export function getNewsCategories(params = {}) {
  return request({
    url: '/news/categories',
    method: 'get',
    params
  })
}

/**
 * 获取某分类下的新闻列表
 * @param {Object} params 查询参数 { categoryId, page, pageSize }
 * @returns {Promise<{ List: Array }>} 后端 data 里是 { List: [...] }
 */
export function getNewsList(params = {}) {
  return request({
    url: '/news/list',
    method: 'get',
    params
  })
}

/**
 * 获取新闻详情（后端会同时累加一次浏览量）
 * @param {Object} params 查询参数 { id: 新闻ID }
 * @returns {Promise<Object>} { id, title, content, image, author, publishTime, categoryId, views, relater }
 */
export function getNewsDetail(params = {}) {
  return request({
    url: '/news/detail',
    method: 'get',
    params
  })
}
