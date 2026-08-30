from contextlib import asynccontextmanager

from fastapi import FastAPI, Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase

app = FastAPI()
#ORM 的大概建表步骤:
#创建异步引xin
ASYNC_DATABASE_URL = "mysql+aiomysql://user:203522@localhost:3306/mydb"
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True, #输出SQL日志
    pool_size=10, #设置连接池活跃的连接数
    max_overflow=20, #允许额外的连接数
)
#基类
class Base(DeclarativeBase):
    pass

class book(Base):
    pass

#建表:定义函数建表 —> FastAPI 启动的时候调用建表函数
async def create_tables(book_id: int):
    #获取异步引xin，创建事务 —> 建表
    pass
@asynccontextmanager("starlette")
async def star_even():
    await create_tables()

@app.get("/")
async def root():
    return {"message": "Hello World666"}
