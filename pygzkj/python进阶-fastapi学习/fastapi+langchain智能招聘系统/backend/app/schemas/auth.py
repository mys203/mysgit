from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from app.schemas.common import StrictSchema


class LoginRequest(StrictSchema):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()


class RefreshRequest(StrictSchema):
    refresh_token: str = Field(min_length=20, max_length=4096)


class LogoutRequest(StrictSchema):
    refresh_token: str | None = Field(default=None, max_length=4096)
    all_devices: bool = False

    @model_validator(mode="after")
    def require_refresh_token_for_current_device(self) -> "LogoutRequest":
        if not self.all_devices and not self.refresh_token:
            raise ValueError("当前设备注销必须提供 refresh_token")
        return self


class TokenPair(StrictSchema):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class UserIdentity(StrictSchema):
    id: int
    username: str
    real_name: str
    email: str | None = None
    department_id: int | None = None
    roles: list[str]
    permissions: list[str]
