from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_config import get_db
from crud.favorite import add_favorite, add_news_favorite
from dependencies import get_current_user
from models.users import User
from schemas.favorite import FavoriteResponse, FavoriteAddResponse
from schemas.users import success_response

router = APIRouter(prefix="/api/favorite", tags=["favorite"])

@router.get("/check")
async def check(new_id: int = Query(..., alias="newsId"),
                user: User = Depends(get_current_user),
                db: AsyncSession = Depends(get_db)):
    # add_favorite 参数顺序是 (db, user_id, news_id)，别传反了
    is_favorite = await add_favorite(db, user.id, new_id)
    # 得到的结果转成 FavoriteResponse 模型类对象再响应给前端
    return success_response(massage="检查收藏成功", date=FavoriteResponse(isFavorite=is_favorite))


@router.post("/add")
async def add(
        payload: FavoriteAddResponse,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    result = await add_news_favorite(db, user.id, payload.news_id)
    # 不直接返回 ORM 对象，只返回前端需要的字段
    return success_response(massage="收藏成功", date={"news_id": result.news_id})