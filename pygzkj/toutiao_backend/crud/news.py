from unittest import result

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
#把模型类导进来（最重要）
from models.news import Category, News

#第一轮对表的查询操作
async def get_news_category(db:AsyncSession,skip: int = 0, limit: int = 10):
    stmt = select(Category).offset(skip).limit(limit)
    results = await db.execute(stmt)
    return results.scalars().all()

#第二轮对表的查询操作，获得新闻列表
async def get_news_list(db:AsyncSession,category_id:int,
                        skip: int = 0,
                        limit: int = 100):
    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    results = await db.execute(stmt)
    return results.scalars().all()

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