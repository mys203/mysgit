from __future__ import annotations

from collections.abc import Callable

from fastapi import Request

from app.common.exceptions import RateLimitError
from app.config.redis import redis_manager
from app.config.settings import settings


def rate_limit(scope: str, limit: int | None = None) -> Callable[[Request], None]:
    allowed = limit or settings.rate_limit_default_requests

    def dependency(request: Request) -> None:
        client_host = request.client.host if request.client else "unknown"
        key = f"recruit:ratelimit:{scope}:{client_host}"
        count = redis_manager.increment(key, settings.rate_limit_window_seconds)
        if count > allowed:
            raise RateLimitError()

    return dependency

