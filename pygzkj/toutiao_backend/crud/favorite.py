from idlelib import delegator

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.news import News


#第三轮模块开始,这个检验是否收藏有，有就显示收藏
async def check_favorite(
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

#设定删除
async def remove_favorite(
        db:AsyncSession,
        user_id:int,
        news_id:int
):
    stmt=delete(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0

#获取当前用户收藏的新闻列表（分页），返回 (新闻列表, 总量)
async def get_favorite_list(db:AsyncSession, user_id:int, page:int = 1, page_size:int = 10):
    # 收藏的总量
    count_query = select(func.count()).where(Favorite.user_id == user_id)
    total = (await db.execute(count_query)).scalar_one()
    # 联表查询
    # 只 select(News) 返回纯新闻对象，方便 jsonable_encoder 直接序列化
    stmt = (
        select(News)
        .join(Favorite, Favorite.news_id == News.id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    news_list = (await db.execute(stmt)).scalars().all()
    return news_list, total
