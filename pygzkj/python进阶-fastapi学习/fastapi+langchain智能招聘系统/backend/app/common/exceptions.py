from __future__ import annotations

from typing import Any


class AppError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: int = 40000,
        status_code: int = 400,
        data: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.data = data


class AuthenticationError(AppError):
    def __init__(self, message: str = "认证失败") -> None:
        super().__init__(message, code=40100, status_code=401)


class PermissionDeniedError(AppError):
    def __init__(self, message: str = "无权执行此操作") -> None:
        super().__init__(message, code=40300, status_code=403)


class NotFoundError(AppError):
    def __init__(self, message: str = "资源不存在") -> None:
        super().__init__(message, code=40400, status_code=404)


class ConflictError(AppError):
    def __init__(self, message: str = "资源冲突") -> None:
        super().__init__(message, code=40900, status_code=409)


class RateLimitError(AppError):
    def __init__(self, message: str = "请求过于频繁，请稍后重试") -> None:
        super().__init__(message, code=42900, status_code=429)


class AIUnavailableError(AppError):
    def __init__(self, message: str = "AI 服务暂时不可用") -> None:
        super().__init__(message, code=50200, status_code=502)

