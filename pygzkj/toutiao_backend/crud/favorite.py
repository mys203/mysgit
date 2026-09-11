from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite


#第三轮模块开始
async def add_favorite(
        db:AsyncSession,
        user_id:int,
        news_id:int
):
    query=select(Favorite).where(Favorite.user_id == user_id,Favorite.news_id == news_id)
    result = await db.execute(query)
    return result.scalars().one_or_none() is not None


#添加收藏的方法
async def add_news_favorite(
        db:AsyncSession,
        user_id:int,
        news_id:int
):
    # 先查是否已收藏，避免唯一约束冲突报错（重复收藏直接返回已有记录）
    query = select(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(query)
    existing = result.scalars().one_or_none()
    if existing:
        return existing

    # 模型构造函数只接受关键字参数，不能传位置参数
    favorite = Favorite(user_id=user_id, news_id=news_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite
