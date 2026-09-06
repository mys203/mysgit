from fastapi import APIRouter, Depends
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from joblib import numpy_pickle
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_config import get_db
from crud import users
from schemas.users import UserRequest

router = APIRouter(prefix="/api/user", tags=["users"])


@router.post("/register")
#新建user路由区分新闻与用户分开。
#导入结构体UserRequest以方便对接数据库。
async def register(user_date: UserRequest  , db: AsyncSession = Depends(get_db)):
    # 注册逻辑:验证用户是否存在 —> 创建用户 —> 生成token -> 响应给数据库进行操作
    exist_username=await users.get_user_name(db, user_date.username) #这个是数据库查询就用await
    if exist_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="输入的用户名已存在")
    user = await users.get_user_register(db, user_date)

    return {
        "code": 200,
        "msg": "register success",
        "data": {
            "token": "用户的访问令牌",
            "userinfo":{
                "id": user.id,
                "username": user.username,
                "bio": user.bio,
                "avatar": user.avatar,
            }
    }
    }

@router.post("/login")
async def login(user_date : UserRequest ,db: AsyncSession = Depends(get_db)):
    user = await users.get_user_register(db, user_date)

    return {
        "code": 200,
        "msg": "register success",
        "data": {
            "token": "用户的访问令牌",
            "userinfo":{
                "id": user.id,
                "username": user.username,
                "bio": user.bio,
                "avatar": user.avatar,
                "gender": user.gender,
                "phone_number": user.phone,
            }
    }
    }
