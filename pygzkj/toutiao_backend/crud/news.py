
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from cache.news_cache import get_cache_categories, set_cache_categories, get_cache_list, set_cache_list
#把模型类导进来（最重要）
from models.news import Category, News

#第一轮对表的查询操作
async def get_news_category(db:AsyncSession,skip: int = 0, limit: int = 10):
    #从缓存里读取，如果有就返回，没有就查库
    cache_category = await get_cache_categories()
    if cache_category:
        return cache_category

    stmt = select(Category).offset(skip).limit(limit)
    results = await db.execute(stmt)
    categories= results.scalars().all()  #问题categories是ORM数据无法直接传到操作里

    if categories:
        category = jsonable_encoder(categories)  #这个解决
        await  set_cache_categories(category)
    return categories


#第二轮对表的查询操作，获得新闻列表
async def get_news_list(db:AsyncSession,category_id:int,
                        skip: int = 0,
                        limit: int = 100):
    #先从缓存里读，有就直接返回
    cache_list = await get_cache_list(category_id, skip, limit)
    if cache_list:
        return cache_list

    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    results = await db.execute(stmt)
    news_list = results.scalars().all()

    #查到数据就写入缓存
    if news_list:
        await set_cache_list(jsonable_encoder(news_list), category_id, skip, limit)
    return news_list

#第三轮对表的查询操作，获得新闻内容
async def get_news_detail(db:AsyncSession,category_id:int,):
    stmt = select(News).where(News.id == category_id)
    results = await db.execute(stmt)
    return results.scalar_one_or_none()

#第三轮需要对浏览量修改，所以继续创建方法对数据库修改操作
async def increase_news_views(db:AsyncSession,news_id:int):
    stmt = update(News).where(News.id == news_id).values(views=News.views + 1)#对数据库的进行修改加1
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def get_related_news(db:AsyncSession,news_id:int,category_id:int,limit: int = 5):
    stmt = select(News).where(News.category_id == category_id).order_by(News.views.desc(),News.publish_time.desc()).limit(limit)
    results = await db.execute(stmt)
    return results.scalars().all()



#现在新闻操作基本完成，现在要去做用户登录、查询什么相关的数据库操作了。
