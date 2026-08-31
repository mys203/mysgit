
from fastapi import APIRouter

#创建APIRouter实例，tags 是分组标签，让docs更清晰。
router = APIRouter(prefix="/api/news",tags=["news"])

@router.get("/categories")
async def get_categories():
    return {"mys":"获取分类成功"}

