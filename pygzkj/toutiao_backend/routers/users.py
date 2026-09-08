from fastapi import APIRouter, Depends, Header
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
    token = await users.create_token(db, user.id)

    return {
        "code": 200,
        "msg": "register success",
        "data": {
            "token": token,
            "userinfo":{
                "id": user.id,
                "username": user.username,
                "bio": user.bio,
                "avatar": user.avatar,
            }
    }
    }

@router.post("/login")
async def login(user_date: UserRequest, db: AsyncSession = Depends(get_db)):
    # 登录逻辑:校验用户名密码 -> 生成token -> 响应
    user = await users.authenticate_user(db, user_date.username, user_date.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或密码错误")

    token = await users.create_token(db, user.id)

    return {
        "code": 200,
        "msg": "login success",
        "data": {
            "token": token,
            "userinfo": {
                "id": user.id,
                "username": user.username,
                "bio": user.bio,
                "avatar": user.avatar,
                "gender": user.gender,
                "phone": user.phone,
            }
        }
    }

#个人信息接口
@router.get("/info")
async def info(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    # 从请求头取出 token，前端统一通过 Authorization: Bearer <token> 携带
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或登录已过期")
    token = authorization.replace("Bearer ", "").strip()

    # 用 token 查用户，顺带校验是否过期
    user = await users.get_user_token(db, token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或登录已过期")

    return {
        "code": 200,
        "msg": "info success",
        "data": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "gender": user.gender,
            "bio": user.bio,
        }
    }




