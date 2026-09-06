
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.users import User
from schemas.users import UserRequest
from utils import security


#根据用户名查询用户是否存在


async def get_user_name( db:AsyncSession,user_name : str):
    query= select(User).where(User.username==user_name)
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


