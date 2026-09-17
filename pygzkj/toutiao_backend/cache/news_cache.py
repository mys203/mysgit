# 新闻相关的缓存方法:新闻分类的读取和写入
from optparse import Option
from typing import List, Dict, Any, Optional

from config.cache_conf import get_redis_json, set_cache

SETS_KEY="CATEGORY_KEY:{skip}:{limit}"

LISTSETS_KEY="NEWS_LIST:{category_id}:{skip}:{limit}"
#读取缓存
async def get_cache_categories(
):
    return await get_redis_json(SETS_KEY)


#存储写入缓存,
async def set_cache_categories(
        date: List[Dict[str, Any]],
        expire: int = 7200  #过期时间一般7200，列表600，详情是1800秒,验证码120
):
    return await set_cache(SETS_KEY,date,expire)
#读取列表的缓存
async def get_cache_list(
        category_id: int,
        skip: int,
        limit: int,
):
    key = LISTSETS_KEY.format(category_id=category_id, skip=skip, limit=limit)
    return await get_redis_json(key)


#写入列表的缓存
async def set_cache_list(
        data: List[Dict[str, Any]],
        category_id: int,
        skip: int,
        limit: int,
        expire: int = 600
):
    key = LISTSETS_KEY.format(category_id=category_id, skip=skip, limit=limit)
    return await set_cache(key, data, expire)