import datetime

from fastapi import FastAPI, APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_config import get_db
from crud import history
from crud.history import add_news_history
from dependencies import get_current_user
from models.users import User
from schemas.history import HistoryAddResponse
from schemas.users import success_response

router = APIRouter(prefix="/api/history", tags=["history"])

#接下来开始写历史列表接口，因为跟收藏大概相似都是对数据库表进行增删查改所以可以借鉴收藏
@router.post("/add")
async def add(
        date : HistoryAddResponse,
        db:AsyncSession = Depends(get_db),
        user:User = Depends(get_current_user),
):
        history = await add_news_history(db, date.news_id,user.id)

        return success_response(message="添加成功",date={"news_id":history.news_id})

@router.get("/list")
async def list(
        db:AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, alias="pageSize", le=100),
        user: User = Depends(get_current_user),
):
        news_list, total = await history.get_list_history(db, page_size, page,user.id)
        has_more = total > page * page_size
        return success_response(massage="获取历史列表成功",date={"List": news_list, "total": total, "hasMore": has_more})