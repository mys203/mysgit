from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Request
from sqlalchemy.orm import Session

from app.common.exceptions import AuthenticationError
from app.config.redis import redis_manager
from app.dao.repositories import UserDAO
from app.schemas.auth import LoginRequest, UserIdentity
from app.security.dependencies import UserPrincipal
from app.security.jwt import TokenPayload, create_token, decode_token
from app.security.password import verify_password
from app.security.sessions import bump_session_version, get_session_version
from app.services.helpers import record_operation


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserDAO(db)

    def login(self, payload: LoginRequest, request: Request | None = None) -> dict:
        user = self.users.get_by_username(payload.username)
        if not user or user.status != "ACTIVE" or not verify_password(payload.password, user.password_hash):
            raise AuthenticationError("用户名或密码错误")
        roles = self.users.get_roles(user.id)
        session_version = get_session_version(user.id)
        access_token, access_jti, access_ttl = create_token(
            user.id, roles, "access", session_version
        )
        refresh_token, refresh_jti, refresh_ttl = create_token(
            user.id, roles, "refresh", session_version
        )
        redis_manager.set(f"recruit:session:{user.id}:{access_jti}", "1", access_ttl + 60)
        redis_manager.set(f"recruit:session:{user.id}:refresh:{refresh_jti}", "1", refresh_ttl)
        user.last_login_at = datetime.now(timezone.utc)
        self.users.commit()
        record_operation(
            self.db,
            None,
            method="POST",
            path=str(request.url.path) if request else "/api/v1/auth/login",
            action="LOGIN",
            resource_type="user",
            resource_id=user.id,
            request=request,
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": access_ttl,
        }

    def refresh(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token, expected_type="refresh")
        if payload.sv != get_session_version(payload.sub):
            raise AuthenticationError("刷新会话已被全端撤销")
        if redis_manager.exists(f"recruit:token:blacklist:{payload.jti}"):
            raise AuthenticationError("刷新凭证已失效")
        if not redis_manager.exists(f"recruit:session:{payload.sub}:refresh:{payload.jti}"):
            raise AuthenticationError("刷新会话已失效，请重新登录")
        user = self.users.get(payload.sub)
        if not user or user.status != "ACTIVE" or user.is_deleted:
            raise AuthenticationError("用户不存在或已停用")
        self._blacklist(payload)
        redis_manager.delete(f"recruit:session:{user.id}:refresh:{payload.jti}")
        roles = self.users.get_roles(user.id)
        access_token, access_jti, access_ttl = create_token(
            user.id, roles, "access", payload.sv
        )
        new_refresh, refresh_jti, refresh_ttl = create_token(
            user.id, roles, "refresh", payload.sv
        )
        redis_manager.set(f"recruit:session:{user.id}:{access_jti}", "1", access_ttl + 60)
        redis_manager.set(f"recruit:session:{user.id}:refresh:{refresh_jti}", "1", refresh_ttl)
        return {
            "access_token": access_token,
            "refresh_token": new_refresh,
            "token_type": "Bearer",
            "expires_in": access_ttl,
        }

    def logout(
        self,
        user: UserPrincipal,
        refresh_token: str | None = None,
        all_devices: bool = False,
        request: Request | None = None,
    ) -> dict[str, str]:
        token_payload = user.token
        refresh_payload: TokenPayload | None = None
        if refresh_token:
            try:
                refresh_payload = decode_token(refresh_token, expected_type="refresh")
            except AuthenticationError as exc:
                raise AuthenticationError("refresh_token 无效或已过期") from exc
            if refresh_payload.sub != user.id:
                raise AuthenticationError("refresh_token 不属于当前用户")
        self._blacklist(token_payload)
        if refresh_payload:
            self._blacklist(refresh_payload)
            redis_manager.delete(
                f"recruit:session:{refresh_payload.sub}:refresh:{refresh_payload.jti}"
            )
        if all_devices:
            bump_session_version(user.id)
        redis_manager.delete(f"recruit:session:{user.id}:{token_payload.jti}")
        record_operation(
            self.db,
            user,
            method="POST",
            path=str(request.url.path) if request else "/api/v1/auth/logout",
            action="LOGOUT",
            resource_type="user",
            resource_id=user.id,
            request=request,
        )
        return {
            "message": "已退出全部设备" if all_devices else "已退出当前设备",
            "all_devices": all_devices,
            "refresh_revoked": bool(refresh_payload or all_devices),
        }

    def identity(self, user: UserPrincipal) -> UserIdentity:
        return UserIdentity(
            id=user.id,
            username=user.username,
            real_name=user.real_name,
            email=user.email,
            department_id=user.department_id,
            roles=user.roles,
            permissions=user.permissions,
        )

    @staticmethod
    def _blacklist(payload: TokenPayload) -> None:
        remaining = max(1, payload.exp - int(datetime.now(timezone.utc).timestamp()))
        redis_manager.set(f"recruit:token:blacklist:{payload.jti}", "1", remaining)
