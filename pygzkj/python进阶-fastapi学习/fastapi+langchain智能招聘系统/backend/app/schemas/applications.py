from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import ORMSchema, StrictSchema


class ApplicationCreate(StrictSchema):
    job_id: int
    candidate_id: int
    resume_id: int | None = None
    source: str | None = Field(default=None, max_length=100)


class ApplicationStageUpdate(StrictSchema):
    stage: str = Field(
        pattern=r"^(APPLIED|SCREENING|INTERVIEW|OFFER|HIRED|REJECTED|WITHDRAWN)$"
    )
    reason: str | None = Field(default=None, max_length=1000)


class ApplicationResponse(ORMSchema):
    id: int
    job_id: int
    candidate_id: int
    resume_id: int | None
    stage: str
    status: str
    source: str | None
    applied_at: datetime
    updated_by: int | None
    created_at: datetime
    updated_at: datetime

