from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

# 数据库URL
ASYNC_DATABASE_URL = "mysql+aiomysql://root:203522@localhost:3306/news_app?charset=utf8mb4"

# 创建异步引擎
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,  # 可选：输出SQL日志
    pool_size=10,  # 设置连接池中保持的持久连接数
    max_overflow=20  # 设置连接池允许创建的额外连接数
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 依赖项，用于获取数据库会话，重要
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
