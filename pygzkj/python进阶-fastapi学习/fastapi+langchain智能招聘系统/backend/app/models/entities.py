from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base

ID_TYPE = BigInteger().with_variant(Integer, "sqlite")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class SysDepartment(Base, TimestampMixin):
    __tablename__ = "sys_department"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_department.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class SysUser(Base, TimestampMixin):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    real_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True)
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_department.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", index=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class SysRole(Base, TimestampMixin):
    __tablename__ = "sys_role"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")


class SysUserRole(Base):
    __tablename__ = "sys_user_role"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("sys_role.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SysPermission(Base, TimestampMixin):
    __tablename__ = "sys_permission"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)


class SysRolePermission(Base):
    __tablename__ = "sys_role_permission"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(
        ForeignKey("sys_role.id", ondelete="CASCADE"), nullable=False, index=True
    )
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("sys_permission.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class JobCategory(Base, TimestampMixin):
    __tablename__ = "job_category"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_category.id", ondelete="SET NULL")
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")


class JobPosition(Base, TimestampMixin):
    __tablename__ = "job_position"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_category.id", ondelete="SET NULL")
    )
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_department.id", ondelete="SET NULL")
    )
    recruiter_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL")
    )
    description: Mapped[str] = mapped_column(Text, default="")
    requirements: Mapped[str] = mapped_column(Text, default="")
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    location: Mapped[str | None] = mapped_column(String(200))
    employment_type: Mapped[str] = mapped_column(String(50), default="FULL_TIME")
    salary_min: Mapped[float | None] = mapped_column(Float)
    salary_max: Mapped[float | None] = mapped_column(Float)
    headcount: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL")
    )


class Candidate(Base, TimestampMixin):
    __tablename__ = "candidate"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(32), index=True)
    gender: Mapped[str | None] = mapped_column(String(20))
    birth_date: Mapped[date | None] = mapped_column(Date)
    education: Mapped[str | None] = mapped_column(String(100))
    work_years: Mapped[float | None] = mapped_column(Float)
    current_company: Mapped[str | None] = mapped_column(String(200))
    current_title: Mapped[str | None] = mapped_column(String(200))
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    summary: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", index=True)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL")
    )


class Resume(Base, TimestampMixin):
    __tablename__ = "resume"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate.id", ondelete="SET NULL"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="UPLOADED", index=True)
    uploaded_by: Mapped[int | None] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL")
    )


class AITask(Base, TimestampMixin):
    __tablename__ = "ai_task"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    task_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", index=True)
    provider: Mapped[str] = mapped_column(String(50), default="local")
    model_name: Mapped[str | None] = mapped_column(String(100))
    input_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    output_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)
    degraded: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL")
    )


class AIChatSession(Base, TimestampMixin):
    __tablename__ = "ai_chat_session"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    session_no: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    job_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_position.id", ondelete="SET NULL"), index=True
    )
    candidate_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate.id", ondelete="SET NULL"), index=True
    )
    resume_id: Mapped[int | None] = mapped_column(
        ForeignKey("resume.id", ondelete="SET NULL"), index=True
    )
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    last_message_preview: Mapped[str | None] = mapped_column(String(500))
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AIChatMessage(Base, TimestampMixin):
    __tablename__ = "ai_chat_message"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "sequence_no",
            name="uq_ai_chat_message_session_sequence",
        ),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    message_no: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    session_id: Mapped[int] = mapped_column(
        ForeignKey("ai_chat_session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"), index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    context_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    provider: Mapped[str] = mapped_column(String(50), default="local")
    model_name: Mapped[str | None] = mapped_column(String(100))
    latency_ms: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), index=True)
    retry_of_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_chat_message.id", ondelete="SET NULL")
    )


class ResumeParseRecord(Base, TimestampMixin):
    __tablename__ = "resume_parse_record"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resume.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[int | None] = mapped_column(ForeignKey("ai_task.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(30), default="PARSED", index=True)
    parsed_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    confirmed_by: Mapped[int | None] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL")
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class JobApplication(Base, TimestampMixin):
    __tablename__ = "job_application"
    __table_args__ = (
        UniqueConstraint("job_id", "candidate_id", name="uq_job_candidate_application"),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("job_position.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidate.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_id: Mapped[int | None] = mapped_column(
        ForeignKey("resume.id", ondelete="SET NULL")
    )
    stage: Mapped[str] = mapped_column(String(30), default="APPLIED", index=True)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", index=True)
    source: Mapped[str | None] = mapped_column(String(100))
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_by: Mapped[int | None] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL")
    )


class VectorDocument(Base, TimestampMixin):
    __tablename__ = "vector_document"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(JSON, default=list)
    extra_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    algorithm_version: Mapped[str] = mapped_column(String(50), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)


class JobMatchResult(Base, TimestampMixin):
    __tablename__ = "job_match_result"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("job_position.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidate.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_application.id", ondelete="SET NULL")
    )
    score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    rule_score: Mapped[float] = mapped_column(Float, default=0.0)
    vector_score: Mapped[float | None] = mapped_column(Float)
    llm_score: Mapped[float | None] = mapped_column(Float)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    algorithm_version: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    degraded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL")
    )


class InterviewSchedule(Base, TimestampMixin):
    __tablename__ = "interview_schedule"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("job_position.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidate.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_application.id", ondelete="SET NULL")
    )
    interviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    round_no: Mapped[int] = mapped_column(Integer, default=1)
    mode: Mapped[str] = mapped_column(String(30), default="OFFLINE")
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    location: Mapped[str | None] = mapped_column(String(255))
    meeting_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="SCHEDULED", index=True)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL")
    )


class InterviewParticipant(Base, TimestampMixin):
    __tablename__ = "interview_participant"
    __table_args__ = (
        UniqueConstraint("interview_id", "user_id", name="uq_interview_participant"),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    interview_id: Mapped[int] = mapped_column(
        ForeignKey("interview_schedule.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    participant_role: Mapped[str] = mapped_column(String(30), default="INTERVIEWER")
    feedback: Mapped[str | None] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30), default="INVITED")


class InterviewQuestion(Base, TimestampMixin):
    __tablename__ = "interview_question"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    interview_id: Mapped[int | None] = mapped_column(
        ForeignKey("interview_schedule.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("job_position.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate.id", ondelete="CASCADE"), index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="GENERAL")
    reference_answer: Mapped[str | None] = mapped_column(Text)
    score_weight: Mapped[float] = mapped_column(Float, default=1.0)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", index=True)
    generated_by: Mapped[str] = mapped_column(String(50), default="AI")
    approved_by: Mapped[int | None] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OperationLog(Base):
    __tablename__ = "operation_log"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"), index=True
    )
    username: Mapped[str | None] = mapped_column(String(64), index=True)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), index=True)
    resource_id: Mapped[str | None] = mapped_column(String(64))
    status_code: Mapped[int] = mapped_column(Integer, default=200)
    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    request_id: Mapped[str | None] = mapped_column(String(64), index=True)
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    duration_ms: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )


class AIExecutionLog(Base):
    __tablename__ = "ai_execution_log"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_task.id", ondelete="SET NULL"), index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(50), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    degraded: Mapped[bool] = mapped_column(Boolean, default=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    input_digest: Mapped[str | None] = mapped_column(String(64))
    output_digest: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
