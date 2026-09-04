
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_config import get_db
from crud import news
#创建APIRouter实例，tags 是分组标签，让docs更清晰。
router = APIRouter(prefix="/api/news",tags=["news"])
#实现第一个接口编写文档从routers创路由news—>models.news模型类创建—>把类导入crud封装查询方法—>然后又回来到路由调用获取结果
# —>最后在main里挂载/注册app.include_router(news.router)就完成了一次调用
@router.get("/categories")
async def get_categories(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    # 获取数据库里面新闻分类数据，1.得先定义模型类 ，2.再封装查询数据的方法,3.在路由里调用方法得到结果再输出。
    categories = await news.get_news_category(db, skip, limit)
    return {

        "code": 200,
        "msg": "获取新闻分类成功success",
        #前端要的数据date。
        "data": categories
    }

#第二轮编写接口
@router.get("/list")
async def get_list(
        category_id: int = Query(...,alias="categoryId"),
        page: int = 1 ,
        page_size: int = Query(10, alias="pageSize",le=100),
        db: AsyncSession = Depends(get_db)):
    #计算总量，代入数据库方法操作保存结果在news_list在发送给前端
    offset = (page-1)*page_size
    news_list= await news.get_news_list(db, category_id, offset, page_size)
    return {
        "code": 200,
        "msg": "success",
        "data": {
            "List": news_list,
        }
    }


@router.get("/detail")
async def get_news_detail(
        news_id: int = Query(...,alias="id"),
        db: AsyncSession = Depends(get_db)
):
    #第三轮编写，导入新闻内容数据让用户查看，并且浏览量加1，因为模型类在第二轮的时候已经编写所以可以直接用它做数据库操作。
    news_detail = await news.get_news_detail(db, news_id)
    if not news_detail:
        raise HTTPException(status_code=404,detail="输入的数据id不存在")#如果用户输入的错误或者没有这个id就

    view_res = await news.increase_news_views(db, news_id)
    if not view_res:
        raise HTTPException(status_code=404,detail="输入的数据id不存在")

    relate_news = await news.get_related_news(db, news_detail.id, news_detail.category_id)
    if not view_res:
        raise HTTPException(status_code=404, detail="输入的数据id不存在")
    return {
        "code": 200,
        "msg": "success",
        "data": {
            "id": news_id,
            "title": news_detail.title,
            "content":news_detail.content,
            "image":news_detail.image,
            "author":news_detail.author,
            "publishTime":news_detail.publish_time,
            "categoryId":news_detail.category_id,
            "views":news_detail.views,
            "relater": relate_news
        }
    }


