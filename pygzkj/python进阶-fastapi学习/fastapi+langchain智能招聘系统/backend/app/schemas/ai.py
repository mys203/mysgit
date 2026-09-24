from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from app.schemas.common import ORMSchema, StrictSchema


class AITaskResponse(ORMSchema):
    id: int
    task_no: str
    task_type: str
    status: str
    provider: str
    model_name: str | None
    output_payload: dict[str, Any] | None
    error_message: str | None
    degraded: bool
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ResumeParsedData(StrictSchema):
    name: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    gender: str | None = Field(default=None, max_length=20)
    education: str | None = Field(default=None, max_length=100)
    work_years: float | None = Field(default=None, ge=0, le=80)
    current_company: str | None = Field(default=None, max_length=200)
    current_title: str | None = Field(default=None, max_length=200)
    skills: list[str] = Field(default_factory=list, max_length=100)
    summary: str | None = Field(default=None, max_length=5000)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class MatchRequest(StrictSchema):
    job_id: int
    candidate_ids: list[int] | None = Field(default=None, max_length=200)
    top_k: int = Field(default=20, ge=1, le=100)
    force_refresh: bool = False


class MatchItem(StrictSchema):
    id: int | None = None
    job_id: int
    candidate_id: int
    application_id: int | None
    score: float
    rule_score: float
    vector_score: float | None
    llm_score: float | None
    level: str
    reasons: list[str]
    detail: dict[str, Any]
    degraded: bool


class MatchResponse(StrictSchema):
    task_no: str
    algorithm_version: str
    prompt_version: str
    degraded: bool
    items: list[MatchItem]


class MatchResultResponse(ORMSchema):
    id: int
    job_id: int
    candidate_id: int
    application_id: int | None
    score: float
    rule_score: float
    vector_score: float | None
    llm_score: float | None
    level: str
    reasons: list[str]
    detail: dict[str, Any]
    algorithm_version: str
    prompt_version: str
    degraded: bool
    created_at: datetime


class InterviewQuestionGenerateRequest(StrictSchema):
    job_id: int
    candidate_id: int | None = None
    interview_id: int | None = None
    count: int = Field(default=5, ge=1, le=20)
    categories: list[str] = Field(
        default_factory=lambda: ["专业知识", "项目经历", "行为面试"], min_length=1, max_length=10
    )

    @field_validator("categories")
    @classmethod
    def clean_categories(cls, values: list[str]) -> list[str]:
        cleaned = [item.strip() for item in values if item.strip()]
        if not cleaned:
            raise ValueError("面试题分类不能为空")
        return cleaned


class GeneratedQuestion(StrictSchema):
    question: str = Field(min_length=1, max_length=5000)
    category: str = Field(min_length=1, max_length=50)
    reference_answer: str | None = Field(default=None, max_length=10000)
    score_weight: float = Field(default=1.0, ge=0.1, le=10.0)


class QuestionGenerationResponse(StrictSchema):
    task_no: str
    degraded: bool
    questions: list[dict[str, Any]]

