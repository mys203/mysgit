from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.common import ORMSchema, StrictSchema


class OperationLogResponse(ORMSchema):
    id: int
    user_id: int | None
    username: str | None
    method: str
    path: str
    action: str
    resource_type: str | None
    resource_id: str | None
    status_code: int
    ip: str | None
    user_agent: str | None
    request_id: str | None
    detail: dict[str, Any]
    duration_ms: float | None
    created_at: datetime


class DashboardSummary(StrictSchema):
    jobs: dict[str, int]
    candidates: dict[str, int]
    applications: dict[str, int]
    interviews: dict[str, int]
    ai_tasks: dict[str, int]
    generated_at: datetime


class AuditLogCreate(StrictSchema):
    method: str = Field(max_length=10)
    path: str = Field(max_length=500)
    action: str = Field(max_length=100)
    resource_type: str | None = Field(default=None, max_length=100)
    resource_id: str | None = Field(default=None, max_length=64)
    status_code: int = 200
    detail: dict[str, Any] = Field(default_factory=dict)

