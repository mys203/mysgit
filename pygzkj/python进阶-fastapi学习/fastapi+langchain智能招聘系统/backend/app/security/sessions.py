from __future__ import annotations

from app.config.redis import redis_manager
from app.config.settings import settings


def session_version_key(user_id: int) -> str:
    return f"recruit:session:version:{user_id}"


def session_version_ttl() -> int:
    return max(
        settings.jwt_refresh_token_days * 86400,
        settings.jwt_access_token_minutes * 60,
    ) + 3600


def get_session_version(user_id: int) -> int:
    value = redis_manager.get(session_version_key(user_id))
    return int(value) if value and value.isdigit() else 0


def bump_session_version(user_id: int) -> int:
    return redis_manager.increment(session_version_key(user_id), session_version_ttl())

