from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.common import ORMSchema, StrictSchema


class ChatContext(StrictSchema):
    job_id: int | None = Field(default=None, ge=1)
    candidate_id: int | None = Field(default=None, ge=1)


class ChatSessionCreate(StrictSchema):
    title: str | None = Field(default=None, max_length=200)
    context: ChatContext = Field(default_factory=ChatContext)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ChatSessionRename(StrictSchema):
    title: str = Field(min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("会话标题不能为空")
        return cleaned


class ChatContextUpdate(StrictSchema):
    job_id: int | None = Field(default=None, ge=1)
    candidate_id: int | None = Field(default=None, ge=1)


class ChatMessageCreate(StrictSchema):
    content: str = Field(min_length=1, max_length=4000)
    stream: bool = False
    context: ChatContext | None = None

    @field_validator("content")
    @classmethod
    def clean_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("消息内容不能为空")
        return cleaned


class ChatMessageRetry(StrictSchema):
    stream: bool = False


class ChatCitation(StrictSchema):
    source_type: str = Field(min_length=1, max_length=50)
    source_id: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    excerpt: str = Field(min_length=1, max_length=1000)
    route: str = Field(min_length=1, max_length=500)


class ChatSessionResponse(ORMSchema):
    id: int
    session_no: str
    user_id: int
    title: str
    job_id: int | None
    candidate_id: int | None
    resume_id: int | None
    message_count: int
    last_message_preview: str | None
    last_message_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ChatMessageResponse(ORMSchema):
    id: int
    message_no: str
    session_id: int
    role: Literal["USER", "ASSISTANT"]
    status: str
    sequence_no: int
    content: str
    citations: list[dict[str, Any]]
    context_snapshot: dict[str, Any]
    provider: str
    model_name: str | None
    latency_ms: float | None
    error_message: str | None
    idempotency_key: str | None
    retry_of_message_id: int | None
    created_at: datetime
    updated_at: datetime


class ChatMessageSendResponse(StrictSchema):
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    degraded: bool = False


class ChatMessageStopResponse(StrictSchema):
    assistant_id: int
    status: str
    stopped: bool
