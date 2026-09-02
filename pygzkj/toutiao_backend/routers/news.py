
from fastapi import APIRouter,Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_config import get_db
from crud import news
#创建APIRouter实例，tags 是分组标签，让docs更清晰。
router = APIRouter(prefix="/api/news",tags=["news"])

@router.get("/categories")
async def get_categories(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    # 获取数据库里面新闻分类数据，1.得先定义模型类 ，2.再封装查询数据的方法,3.在路由里调用方法得到结果再输出。
    categories = await news.get_news_category(db, skip, limit)
    return {

        "code": 200,
        "msg": "获取新闻分类成功success",
        "data": categories
    }

