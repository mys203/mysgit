
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from models.users import User, UserToken
from schemas.users import UserRequest, UpdateRequest
from utils import security


#根据用户名查询用户是否存在


async def get_user_name( db:AsyncSession,user_name : str):
    query= select(User).where(User.username==user_name)
    result= await db.execute(query)  #执行结果
    return result.scalars().one_or_none()   #有可能有，有可能没有所以用one_or_none

async def get_user_date( db:AsyncSession,user_id : int):
    query= select(User).where(User.id==user_id)
    result= await db.execute(query)  #执行结果
    return result.scalars().one_or_none()   #有可能有，有可能没有所以用one_or_none

#创建用户的方法，得用passlib 用哈希算法加密密码
async def get_user_register( db:AsyncSession,user_name : UserRequest):
    #导入utils的密码加密方法，加密密码
    hash_password =security.get_password_hash(user_name.password)
    user = User(username=user_name.username, password=hash_password)#创建对象
    db.add(user) #提交到数据库新增
    await db.commit()
    await db.refresh(user) #读从数据库读回最新user
    return user

#登录验证：根据用户名查询用户并校验密码，成功返回用户对象，失败返回None
async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user_name(db, username)
    if not user:
        return None
    if not security.verify_password(password, user.password):
        return None
    return user

#创建token的方法
async def create_token( db:AsyncSession,user_id : int):
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(minutes=10)
    query = select(UserToken).where(UserToken.user_id==user_id)
    result= await db.execute(query)
    user_token = result.scalars().one_or_none()

    if user_token :
        user_token.token = token
        user_token.expires_at = expires_at
    else:
        user_token = UserToken(user_id=user_id, token=token, expires_at=expires_at)
        db.add(user_token)

    await db.commit()
    return token

# 根据Token 查询用户 : 验证Token
async def get_user_token( db:AsyncSession,token: str):
    query= select(UserToken).where(UserToken.token==token)
    result= await db.execute(query)
    db_token = result.scalars().one_or_none()

    if not db_token or db_token.expires_at < datetime.now() :
        return None

    query = select(User).where(User.id== db_token.user_id)
    result= await db.execute(query)
    return result.scalars().one_or_none()


async def update_user(db: AsyncSession, users_date: UpdateRequest):
    # 从请求体取出 username 确定要更新哪个用户
    username = users_date.username
    # 把 users_date 转成字典作为要更新的字段值，排除掉 username 本身
    query = update(User).where(User.username == username).values(**users_date.model_dump(
        # 只更新前端传了的字段，没传的保持原样
        exclude_unset=True,
        exclude_none=True,
        exclude={"username"},
    ))
    result = await db.execute(query)
    await db.commit()

    # 获取更新后的用户，最终还是改了
    update_after = await get_user_name(db, username)
    return update_after


async def change_password(db: AsyncSession, user:User,old_password: str,new_password: str):
    #判断密码是否正确
    if not security.verify_password(old_password, user.password):
        return False
    else:
        hashed_password = security.get_password_hash(new_password)
        user.password = hashed_password
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return True