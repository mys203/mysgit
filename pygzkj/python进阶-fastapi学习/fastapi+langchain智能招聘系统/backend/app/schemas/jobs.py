from __future__ import annotations

from datetime import datetime

from pydantic import Field, model_validator

from app.schemas.common import ORMSchema, StrictSchema


class JobCreate(StrictSchema):
    title: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=2, max_length=64)
    category_id: int | None = None
    department_id: int | None = None
    recruiter_id: int | None = None
    description: str = Field(default="", max_length=50000)
    requirements: str = Field(default="", max_length=50000)
    skills: list[str] = Field(default_factory=list, max_length=50)
    location: str | None = Field(default=None, max_length=200)
    employment_type: str = Field(
        default="FULL_TIME", pattern=r"^(FULL_TIME|PART_TIME|CONTRACT|INTERN)$"
    )
    salary_min: float | None = Field(default=None, ge=0, le=100000000)
    salary_max: float | None = Field(default=None, ge=0, le=100000000)
    headcount: int = Field(default=1, ge=1, le=10000)

    @model_validator(mode="after")
    def validate_salary(self) -> "JobCreate":
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_max < self.salary_min
        ):
            raise ValueError("最高薪资不能低于最低薪资")
        return self


class JobUpdate(StrictSchema):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    category_id: int | None = None
    department_id: int | None = None
    recruiter_id: int | None = None
    description: str | None = Field(default=None, max_length=50000)
    requirements: str | None = Field(default=None, max_length=50000)
    skills: list[str] | None = Field(default=None, max_length=50)
    location: str | None = Field(default=None, max_length=200)
    employment_type: str | None = Field(
        default=None, pattern=r"^(FULL_TIME|PART_TIME|CONTRACT|INTERN)$"
    )
    salary_min: float | None = Field(default=None, ge=0, le=100000000)
    salary_max: float | None = Field(default=None, ge=0, le=100000000)
    headcount: int | None = Field(default=None, ge=1, le=10000)

    @model_validator(mode="after")
    def validate_salary(self) -> "JobUpdate":
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_max < self.salary_min
        ):
            raise ValueError("最高薪资不能低于最低薪资")
        return self


class JobResponse(ORMSchema):
    id: int
    title: str
    code: str
    category_id: int | None
    department_id: int | None
    recruiter_id: int | None
    description: str
    requirements: str
    skills: list[str]
    location: str | None
    employment_type: str
    salary_min: float | None
    salary_max: float | None
    headcount: int
    status: str
    published_at: datetime | None
    closed_at: datetime | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime


class JobStatusResponse(StrictSchema):
    id: int
    status: str

