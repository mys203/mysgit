from __future__ import annotations

from datetime import date, datetime

from pydantic import Field, field_validator

from app.schemas.common import ORMSchema, StrictSchema


class CandidateCreate(StrictSchema):
    name: str = Field(min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    gender: str | None = Field(default=None, pattern=r"^(MALE|FEMALE|OTHER|UNKNOWN)$")
    birth_date: date | None = None
    education: str | None = Field(default=None, max_length=100)
    work_years: float | None = Field(default=None, ge=0, le=80)
    current_company: str | None = Field(default=None, max_length=200)
    current_title: str | None = Field(default=None, max_length=200)
    skills: list[str] = Field(default_factory=list, max_length=100)
    summary: str | None = Field(default=None, max_length=20000)
    source: str | None = Field(default=None, max_length=100)
    status: str = Field(default="ACTIVE", pattern=r"^(ACTIVE|INACTIVE|BLACKLIST)$")

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value and ("@" not in value or value.startswith("@") or value.endswith("@")):
            raise ValueError("邮箱格式不正确")
        return value


class CandidateUpdate(StrictSchema):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    gender: str | None = Field(default=None, pattern=r"^(MALE|FEMALE|OTHER|UNKNOWN)$")
    birth_date: date | None = None
    education: str | None = Field(default=None, max_length=100)
    work_years: float | None = Field(default=None, ge=0, le=80)
    current_company: str | None = Field(default=None, max_length=200)
    current_title: str | None = Field(default=None, max_length=200)
    skills: list[str] | None = Field(default=None, max_length=100)
    summary: str | None = Field(default=None, max_length=20000)
    source: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, pattern=r"^(ACTIVE|INACTIVE|BLACKLIST)$")


class CandidateResponse(ORMSchema):
    id: int
    name: str
    email: str | None
    phone: str | None
    gender: str | None
    birth_date: date | None
    education: str | None
    work_years: float | None
    current_company: str | None
    current_title: str | None
    skills: list[str]
    summary: str | None
    source: str | None
    status: str
    created_by: int | None
    created_at: datetime
    updated_at: datetime

