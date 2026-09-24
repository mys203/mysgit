from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.exceptions import AppError
from app.common.response import error

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return error(exc.message, exc.code, exc.status_code, exc.data)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError):
        errors = []
        for item in exc.errors():
            location = ".".join(str(part) for part in item.get("loc", []))
            errors.append({"field": location, "message": item.get("msg", "参数错误")})
        return error("请求参数校验失败", 42200, 422, errors)

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(_: Request, exc: IntegrityError):
        logger.warning("数据库约束冲突：%s", exc)
        return error("数据已存在或违反约束", 40901, 409)

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_: Request, exc: StarletteHTTPException):
        return error(str(exc.detail), exc.status_code * 100, exc.status_code)

    @app.exception_handler(Exception)
    async def unexpected_error_handler(_: Request, exc: Exception):
        logger.exception("未处理异常", exc_info=exc)
        return error("服务器内部错误", 50000, 500)
