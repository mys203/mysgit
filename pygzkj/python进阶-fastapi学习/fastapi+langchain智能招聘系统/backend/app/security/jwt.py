from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import BaseModel, Field

from app.common.exceptions import AuthenticationError
from app.config.settings import settings

TokenType = Literal["access", "refresh"]


class TokenPayload(BaseModel):
    sub: int
    type: TokenType
    jti: str
    roles: list[str] = Field(default_factory=list)
    sv: int = Field(default=0, ge=0)
    iat: int
    exp: int
    iss: str


def _secret() -> str:
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY 未配置")
    return settings.jwt_secret_key.get_secret_value()


def create_token(
    user_id: int,
    roles: list[str],
    token_type: TokenType,
    session_version: int = 0,
) -> tuple[str, str, int]:
    now = datetime.now(timezone.utc)
    if token_type == "access":
        expires = now + timedelta(minutes=settings.jwt_access_token_minutes)
    else:
        expires = now + timedelta(days=settings.jwt_refresh_token_days)
    jti = uuid4().hex
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": token_type,
        "jti": jti,
        "roles": roles,
        "sv": session_version,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "iss": settings.jwt_issuer,
    }
    token = jwt.encode(payload, _secret(), algorithm=settings.jwt_algorithm)
    ttl = int((expires - now).total_seconds())
    return token, jti, ttl


def decode_token(token: str, expected_type: TokenType | None = None) -> TokenPayload:
    try:
        raw = jwt.decode(
            token,
            _secret(),
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
        )
        payload = TokenPayload.model_validate(raw)
    except ExpiredSignatureError as exc:
        raise AuthenticationError("登录凭证已过期") from exc
    except (JWTError, ValueError) as exc:
        raise AuthenticationError("登录凭证无效") from exc
    if expected_type and payload.type != expected_type:
        raise AuthenticationError("登录凭证类型错误")
    return payload
