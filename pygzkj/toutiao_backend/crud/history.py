from datetime import datetime, timedelta

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.history import History
from models.news import News


async def add_news_history(
        db:AsyncSession,
        news_id:int,
        user_id:int,
):
    #是否有看过，有就更新时间
    query = select(History).where(History.user_id == user_id, History.news_id == news_id)
    news_history = await db.execute(query)
    add_way = news_history.scalars().one_or_none()
    #这个是更新时间的方法的
    view_time = datetime.now()

    if add_way:
        add_way = History(view_time=view_time)
        await db.commit()
        await db.refresh(add_way)
        return add_way

    history = History(user_id=user_id, news_id=news_id,view_time=view_time)
    db.add(history)
    await db.commit()
    await db.refresh(history)
    return history


async def get_list_history(
        db:AsyncSession,
        page_size:int,
        page:int ,
        user_id:int,
):
    #查询历史的总量
    count_query = select(func.count()).where(History.user_id == user_id)
    total = (await db.execute(count_query)).scalar_one()

    # 联表查询,类似收藏也是
    # 只 select(News) 返回纯新闻对象，方便 jsonable_encoder 直接序列化
    stmt = (
        select(News,History.view_time)
        .join(History, History.news_id == News.id)
        .where(History.user_id == user_id)
        .order_by(History.view_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).all()
    news_list = []
    for news, view_time in rows:
        news.view_time = view_time
        news_list.append(news)
    return news_list, total


async def delete_histories(
        db:AsyncSession,
        news_id:int,
        user_id:int,
):
    #类似收藏的删除
    stmt=delete(History).where(History.user_id == user_id, History.news_id == news_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0
