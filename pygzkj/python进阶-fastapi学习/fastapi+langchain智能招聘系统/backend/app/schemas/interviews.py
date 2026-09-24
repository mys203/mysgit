from __future__ import annotations

from datetime import datetime

from pydantic import Field, model_validator

from app.schemas.common import ORMSchema, StrictSchema


class InterviewCreate(StrictSchema):
    job_id: int
    candidate_id: int
    application_id: int | None = None
    interviewer_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    round_no: int = Field(default=1, ge=1, le=20)
    mode: str = Field(default="OFFLINE", pattern=r"^(OFFLINE|VIDEO|PHONE)$")
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=15, le=720)
    location: str | None = Field(default=None, max_length=255)
    meeting_url: str | None = Field(default=None, max_length=500)


class InterviewUpdate(StrictSchema):
    interviewer_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    round_no: int | None = Field(default=None, ge=1, le=20)
    mode: str | None = Field(default=None, pattern=r"^(OFFLINE|VIDEO|PHONE)$")
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=15, le=720)
    location: str | None = Field(default=None, max_length=255)
    meeting_url: str | None = Field(default=None, max_length=500)
    status: str | None = Field(
        default=None, pattern=r"^(SCHEDULED|IN_PROGRESS|COMPLETED|CANCELLED)$"
    )


class InterviewResponse(ORMSchema):
    id: int
    job_id: int
    candidate_id: int
    application_id: int | None
    interviewer_id: int | None
    title: str
    round_no: int
    mode: str
    scheduled_at: datetime
    duration_minutes: int
    location: str | None
    meeting_url: str | None
    status: str
    created_by: int | None
    created_at: datetime
    updated_at: datetime


class InterviewCancelRequest(StrictSchema):
    reason: str = Field(min_length=1, max_length=1000)


class ParticipantCreate(StrictSchema):
    user_id: int
    participant_role: str = Field(
        default="INTERVIEWER", pattern=r"^(INTERVIEWER|OBSERVER|COORDINATOR)$"
    )


class ParticipantResponse(ORMSchema):
    id: int
    interview_id: int
    user_id: int
    participant_role: str
    feedback: str | None
    score: float | None
    status: str
    created_at: datetime
    updated_at: datetime


class FeedbackRequest(StrictSchema):
    feedback: str = Field(min_length=1, max_length=10000)
    score: float | None = Field(default=None, ge=0, le=100)
    status: str = Field(default="COMPLETED", pattern=r"^(INVITED|CONFIRMED|COMPLETED|DECLINED)$")


class InterviewQuestionUpdate(StrictSchema):
    question: str | None = Field(default=None, min_length=1, max_length=5000)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    reference_answer: str | None = Field(default=None, max_length=10000)
    score_weight: float | None = Field(default=None, ge=0.1, le=10.0)
    status: str | None = Field(default=None, pattern=r"^(DRAFT|APPROVED|REJECTED)$")


class QuestionResponse(ORMSchema):
    id: int
    interview_id: int | None
    job_id: int
    candidate_id: int | None
    question: str
    category: str
    reference_answer: str | None
    score_weight: float
    status: str
    generated_by: str
    approved_by: int | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class QuestionApproveRequest(StrictSchema):
    question_ids: list[int] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def unique_ids(self) -> "QuestionApproveRequest":
        self.question_ids = list(dict.fromkeys(self.question_ids))
        return self

