from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.common import ORMSchema, StrictSchema


class ResumeResponse(ORMSchema):
    id: int
    candidate_id: int | None
    filename: str
    file_hash: str
    file_type: str
    file_size: int
    status: str
    uploaded_by: int | None
    created_at: datetime
    updated_at: datetime


class ResumeDetailResponse(ResumeResponse):
    pass


class ParseRecordResponse(ORMSchema):
    id: int
    resume_id: int
    task_id: int | None
    status: str
    parsed_data: dict[str, Any]
    confidence: float
    confirmed_by: int | None
    confirmed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ParseResultResponse(StrictSchema):
    parse_record: ParseRecordResponse
    task_no: str
    degraded: bool


class CandidateOverride(StrictSchema):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    education: str | None = Field(default=None, max_length=100)
    work_years: float | None = Field(default=None, ge=0, le=80)
    current_company: str | None = Field(default=None, max_length=200)
    current_title: str | None = Field(default=None, max_length=200)
    skills: list[str] | None = Field(default=None, max_length=100)
    summary: str | None = Field(default=None, max_length=20000)


class ParseConfirmRequest(StrictSchema):
    candidate_id: int | None = None
    job_position_id: int | None = None
    candidate_override: CandidateOverride | None = None


class ParseConfirmResponse(StrictSchema):
    resume_id: int
    parse_record_id: int
    candidate_id: int
    application_id: int | None
    status: str
