from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_config import get_db
from crud import favorite, news
from crud.favorite import check_favorite, add_news_favorite
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
    is_favorite = await check_favorite(db, user.id, new_id)
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

@router.delete("/remove")
async def remove(
        new_id: int=Query(..., alias="newsId"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result=await favorite.remove_favorite(db, user.id, new_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="收藏记录不存在")
    return success_response(massage="删除收藏成功",)


@router.get("/list")
async def favorite_list(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, alias="pageSize", le=100),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
    news_list, total = await favorite.get_favorite_list(db, user.id, page, page_size)
    has_more = total > page * page_size
    return success_response(massage="获取收藏列表成功", date={"List": news_list, "total": total, "hasMore": has_more})

