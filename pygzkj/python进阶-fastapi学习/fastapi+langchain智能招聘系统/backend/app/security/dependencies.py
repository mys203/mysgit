from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.common.exceptions import AuthenticationError, PermissionDeniedError
from app.config.database import get_db
from app.config.redis import redis_manager
from app.dao.repositories import UserDAO
from app.security.jwt import TokenPayload, decode_token
from app.security.sessions import get_session_version

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class UserPrincipal:
    id: int
    username: str
    real_name: str
    email: str | None
    department_id: int | None
    roles: list[str]
    permissions: list[str]
    token: TokenPayload


def get_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("请提供 Bearer Access Token")
    return credentials.credentials


def get_token_payload(token: Annotated[str, Depends(get_bearer_token)]) -> TokenPayload:
    payload = decode_token(token, expected_type="access")
    if redis_manager.exists(f"recruit:token:blacklist:{payload.jti}"):
        raise AuthenticationError("登录凭证已注销")
    if payload.sv != get_session_version(payload.sub):
        raise AuthenticationError("登录会话已被全端撤销")
    if not redis_manager.exists(f"recruit:session:{payload.sub}:{payload.jti}"):
        raise AuthenticationError("用户会话已失效，请重新登录")
    return payload


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> UserPrincipal:
    user_dao = UserDAO(db)
    user = user_dao.get(payload.sub)
    if not user or user.is_deleted or user.status != "ACTIVE":
        raise AuthenticationError("用户不存在或已停用")
    roles = user_dao.get_roles(user.id)
    permissions = user_dao.get_permissions(user.id)
    return UserPrincipal(
        id=user.id,
        username=user.username,
        real_name=user.real_name,
        email=user.email,
        department_id=user.department_id,
        roles=roles,
        permissions=permissions,
        token=payload,
    )


CurrentUser = Annotated[UserPrincipal, Depends(get_current_user)]


def require_roles(*allowed_roles: str):
    def dependency(user: CurrentUser) -> UserPrincipal:
        if "ADMIN" in user.roles:
            return user
        if not set(allowed_roles).intersection(user.roles):
            raise PermissionDeniedError()
        return user

    return dependency


def require_permissions(*required_permissions: str):
    def dependency(user: CurrentUser) -> UserPrincipal:
        if "ADMIN" in user.roles:
            return user
        if not set(required_permissions).issubset(set(user.permissions)):
            raise PermissionDeniedError()
        return user

    return dependency


def require_any_permissions(*allowed_permissions: str):
    def dependency(user: CurrentUser) -> UserPrincipal:
        if "ADMIN" in user.roles:
            return user
        if not set(allowed_permissions).intersection(user.permissions):
            raise PermissionDeniedError()
        return user

    return dependency


def require_role_and_permission(role_code: str, permission_code: str):
    def dependency(user: CurrentUser) -> UserPrincipal:
        if "ADMIN" in user.roles:
            return user
        if role_code not in user.roles or permission_code not in user.permissions:
            raise PermissionDeniedError()
        return user

    return dependency
