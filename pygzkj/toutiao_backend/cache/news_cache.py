# 新闻相关的缓存方法:新闻分类的读取和写入
from typing import List, Dict, Any

from config.cache_conf import get_redis_json, set_cache

SETS_KEY="CATEGORY_KEY:{skip}:{limit}"
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