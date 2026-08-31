from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import String, Float, Integer, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 1. 连接同一个数据库 mydb(和 27.py 保持一致,这样才能操作同一张表)
#    mysql+aiomysql://用户名:密码@地址:端口/数据库名
ASYNC_DATABASE_URL = "mysql+aiomysql://root:203522@localhost:3306/mydb"
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,       # 输出 SQL 日志,方便看生成的语句
    pool_size=10,    # 连接池中活跃的连接数
    max_overflow=20, # 允许额外创建的连接数
)


# 2. 定义基类:所有 ORM 模型类都要继承它
class Base(DeclarativeBase):
    pass


# 3. 定义"图书"表对应的模型类(和 27.py 定义的是同一张 book 表)
class Book(Base):
    __tablename__ = "book"  # 数据库中实际的表名
    # 编号 id:主键,自增,每本书唯一
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 书名:必填,最长 100 个字符
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="书名")
    # 作者:最长 50 个字符
    author: Mapped[str] = mapped_column(String(50), comment="作者")
    # 价格:浮点数
    price: Mapped[float] = mapped_column(Float, comment="价格")
    # 出版社
    publisher: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="出版社")


# 4. 创建"会话"工厂
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


# 5. 应用生命周期:FastAPI 启动时建表(表已存在则跳过)
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await async_engine.dispose()


app = FastAPI(lifespan=lifespan)


# 6. 查询所有书(方便删除后验证结果)
@app.get("/books")
async def list_books():
    async with async_session() as session:
        result = await session.execute(select(Book))
        books = result.scalars().all()
        return {"books": [
            {"id": b.id, "name": b.name, "author": b.author, "price": b.price}
            for b in books
        ]}


# 7. 按 id 删除一本书(核心:ORM 的"删"操作)
@app.delete("/books/{book_id}")
async def delete_book(book_id: int):
    async with async_session() as session:
        # 先按 id 把这本书查出来
        result = await session.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        # 查不到就返回提示,不报错
        if book is None:
            return {"message": "没有找到这本书", "id": book_id}
        # 标记为"待删除",提交事务后真正从数据库删掉
        await session.delete(book)
        await session.commit()
        return {"message": "删除成功", "id": book_id}
