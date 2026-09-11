from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_config import get_db
from crud import users
from models.users import User


async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从请求头取 token 并校验，返回当前登录用户，供路由通过 Depends 注入。

    用法：async def xxx(user: User = Depends(get_current_user), ...)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或登录已过期")
    token = authorization.replace("Bearer ", "").strip()
    user = await users.get_user_token(db, token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或登录已过期")
    return user
