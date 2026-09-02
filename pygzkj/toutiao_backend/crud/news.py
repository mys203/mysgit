from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
#把模型类导进来
from models.news import Category

async def get_news_category(db:AsyncSession,skip: int = 0, limit: int = 100):
    stmt = select(Category).offset(skip).limit(limit)
    results = await db.execute(stmt)
    return results.scalars().all()