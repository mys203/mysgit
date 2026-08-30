from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import String, Float, Integer, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 1. 创建异步引擎(连接 MySQL 数据库)
#    mysql+aiomysql://用户名:密码@地址:端口/数据库名
ASYNC_DATABASE_URL = "mysql+aiomysql://root:203522@localhost:3306/mydb"
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,       # 输出 SQL 日志,方便看生成的语句
    pool_size=10,    # 连接池中活跃的连接数
    max_overflow=20, # 允许额外创建的连接数
)


# 3. 定义基类:所有 ORM 模型类都要继承它
class Base(DeclarativeBase):
    pass


# 4. 定义"图书"表对应的模型类
class Book(Base):
    __tablename__ = "book"  # 数据库中实际的表名
    # 编号 id:主键,自增,每本书唯一
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 书名:必填,最长 100 个字符
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="书名")
    # 作者:最长 50 个字符
    author: Mapped[str] = mapped_column(String(50), comment="作者")
    # 价格:浮点数(真实项目里金额更推荐用 Decimal/Numeric,这里为了简单用 Float)
    price: Mapped[float] = mapped_column(Float, comment="价格")
    # 出版社(可自行添加的字段示例)。
    publisher: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="出版社")


# 5. 创建"会话"工厂:用会话(Session)来执行数据库操作。
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


# 6. 应用生命周期:FastAPI 启动时自动建表
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时:建表(表不存在才创建,已存在则跳过)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 关闭时:释放数据库连接
    await async_engine.dispose()


app = FastAPI(lifespan=lifespan)


# 7. 新增一本书(核心:ORM 的"增"操作)
async def add_book():
    # 用 async with 打开一个会话,结束后自动关闭
    async with async_session() as session:
        # 创建一个 Book 对象 = 准备插入的一条数据(还没写入数据库)
        book = Book(
            name="三国演义",
            author="罗贯中",
            price=59.9,
            publisher="人民文学出版社",
        )
        session.add(book)          # 把对象加入会话,标记为"待新增"
        await session.commit()     # 提交事务,真正写入数据库
        await session.refresh(book)  # 刷新对象,拿到数据库自动生成的 id
        print(f"新增成功! 编号 id = {book.id}")
        return book


# 8. 提供接口:POST 请求时新增一本书
@app.post("/books/add")
async def create_book():
    book = await add_book()
    return {"message": "新增成功", "book": {
        "id": book.id,
        "name": book.name,
        "author": book.author,
        "price": book.price,
    }}


# 9. 提供一个查询接口,方便验证新增的结果
@app.get("/books")
async def list_books():
    async with async_session() as session:
        # 用 ORM 方式查询整张表的所有书
        result = await session.execute(select(Book))
        books = result.scalars().all()
        return {"books": [
            {"id": b.id, "name": b.name, "author": b.author, "price": b.price}
            for b in books
        ]}


@app.get("/")
async def root():
    return {"message": "Hello World666"}
