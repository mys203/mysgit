from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
#把模型类导进来
from models.news import Category, News
#第一轮对表的查询操作
async def get_news_category(db:AsyncSession,skip: int = 0, limit: int = 10):
    stmt = select(Category).offset(skip).limit(limit)
    results = await db.execute(stmt)
    return results.scalars().all()

#第二轮对表的查询操作，获得新闻内容
async def get_news_list(db:AsyncSession,category_id:int,
                        skip: int = 0,
                        limit: int = 100):
    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    results = await db.execute(stmt)
    return results.scalars().all()