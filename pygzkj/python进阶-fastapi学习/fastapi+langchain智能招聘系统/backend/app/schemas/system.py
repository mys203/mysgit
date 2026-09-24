from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from app.schemas.common import ORMSchema, StrictSchema


USERNAME_PATTERN = r"^[a-zA-Z0-9_.-]{3,64}$"
ROLE_CODES = {"ADMIN", "HR_MANAGER", "RECRUITER", "INTERVIEWER", "VIEWER"}


class DepartmentCreate(StrictSchema):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=2, max_length=64)
    parent_id: int | None = None
    description: str | None = Field(default=None, max_length=500)
    status: str = Field(default="ACTIVE", pattern=r"^(ACTIVE|INACTIVE)$")


class DepartmentUpdate(StrictSchema):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    parent_id: int | None = None
    description: str | None = Field(default=None, max_length=500)
    status: str | None = Field(default=None, pattern=r"^(ACTIVE|INACTIVE)$")


class DepartmentResponse(ORMSchema):
    id: int
    name: str
    code: str
    parent_id: int | None
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class RoleCreate(StrictSchema):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=2, max_length=64)
    description: str | None = Field(default=None, max_length=500)
    status: str = Field(default="ACTIVE", pattern=r"^(ACTIVE|INACTIVE)$")

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in ROLE_CODES:
            raise ValueError(f"角色编码必须是：{', '.join(sorted(ROLE_CODES))}")
        return normalized


class RoleUpdate(StrictSchema):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    status: str | None = Field(default=None, pattern=r"^(ACTIVE|INACTIVE)$")


class RoleResponse(ORMSchema):
    id: int
    name: str
    code: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class UserCreate(StrictSchema):
    username: str = Field(min_length=3, max_length=64, pattern=USERNAME_PATTERN)
    password: str = Field(min_length=8, max_length=128)
    real_name: str = Field(min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    department_id: int | None = None
    role_codes: list[str] = Field(default_factory=lambda: ["VIEWER"], min_length=1, max_length=5)
    status: str = Field(default="ACTIVE", pattern=r"^(ACTIVE|INACTIVE)$")

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("role_codes")
    @classmethod
    def validate_roles(cls, values: list[str]) -> list[str]:
        normalized = [value.upper() for value in values]
        invalid = set(normalized) - ROLE_CODES
        if invalid:
            raise ValueError(f"非法角色编码：{', '.join(sorted(invalid))}")
        return list(dict.fromkeys(normalized))

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value and ("@" not in value or value.startswith("@") or value.endswith("@")):
            raise ValueError("邮箱格式不正确")
        return value


class UserUpdate(StrictSchema):
    real_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    department_id: int | None = None
    role_codes: list[str] | None = Field(default=None, min_length=1, max_length=5)
    status: str | None = Field(default=None, pattern=r"^(ACTIVE|INACTIVE)$")
    password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("role_codes")
    @classmethod
    def validate_roles(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        normalized = [value.upper() for value in values]
        invalid = set(normalized) - ROLE_CODES
        if invalid:
            raise ValueError(f"非法角色编码：{', '.join(sorted(invalid))}")
        return list(dict.fromkeys(normalized))


class UserResponse(ORMSchema):
    id: int
    username: str
    real_name: str
    email: str | None
    phone: str | None
    department_id: int | None
    status: str
    roles: list[str]
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CategoryCreate(StrictSchema):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=2, max_length=64)
    parent_id: int | None = None
    sort_order: int = Field(default=0, ge=0, le=100000)
    status: str = Field(default="ACTIVE", pattern=r"^(ACTIVE|INACTIVE)$")


class CategoryUpdate(StrictSchema):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    parent_id: int | None = None
    sort_order: int | None = Field(default=None, ge=0, le=100000)
    status: str | None = Field(default=None, pattern=r"^(ACTIVE|INACTIVE)$")


class CategoryResponse(ORMSchema):
    id: int
    name: str
    code: str
    parent_id: int | None
    sort_order: int
    status: str
    created_at: datetime
    updated_at: datetime


class SystemActionResponse(StrictSchema):
    id: int
    status: str


class PermissionResponse(ORMSchema):
    id: int
    name: str
    code: str
    resource: str
    action: str


class UserRoleUpdate(StrictSchema):
    role_codes: list[str] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def validate_roles(self) -> "UserRoleUpdate":
        invalid = set(self.role_codes) - ROLE_CODES
        if invalid:
            raise ValueError(f"非法角色编码：{', '.join(sorted(invalid))}")
        return self

