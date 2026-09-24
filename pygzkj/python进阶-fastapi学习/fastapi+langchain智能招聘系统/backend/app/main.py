from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.exception_handlers import register_exception_handlers
from app.common.middleware import RequestIdMiddleware
from app.common.response import success
from app.config.database import initialize_database
from app.config.redis import redis_manager
from app.config.seed import initialize_seed_data, recover_incomplete_ai_tasks
from app.config.settings import settings
from app.routers import ai, auth, interviews, jobs, operations, recruitment, resumes, system

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    redis_manager.initialize()
    if redis_manager.degraded:
        logger.warning("Redis 降级为进程内存储，仅允许开发或测试环境使用")
    initialize_database()
    initialize_seed_data()
    recovered_tasks = recover_incomplete_ai_tasks()
    if recovered_tasks:
        logger.warning(
            "已将 %s 个超时 AI 任务或聊天消息标记为失败，可重新提交",
            recovered_tasks,
        )
    logger.info("后端启动完成，环境：%s", settings.app_env)
    yield
    redis_manager.close()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
register_exception_handlers(app)

for api_router in (
    auth.router,
    system.router,
    jobs.router,
    resumes.router,
    recruitment.router,
    ai.router,
    interviews.router,
    operations.router,
):
    app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health", tags=["健康检查"])
def health():
    return success(
        {
            "status": "ok",
            "environment": settings.app_env,
            "redis_degraded": redis_manager.degraded,
            "ai_degraded": not settings.llm_configured,
        }
    )
