from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import success
from app.config.database import get_db
from app.schemas.interviews import (
    FeedbackRequest,
    InterviewCancelRequest,
    InterviewCreate,
    InterviewUpdate,
    ParticipantCreate,
)
from app.security.dependencies import require_permissions, require_role_and_permission
from app.security.rate_limit import rate_limit
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interviews", tags=["面试"])
DbSession = Annotated[Session, Depends(get_db)]
InterviewReader = Annotated[object, Depends(require_permissions("interviews:read"))]
InterviewWriter = Annotated[object, Depends(require_permissions("interviews:write"))]
InterviewScheduler = Annotated[
    object, Depends(require_permissions("interviews:schedule"))
]
InterviewManager = Annotated[
    object,
    Depends(require_role_and_permission("HR_MANAGER", "interviews:manage")),
]


@router.get("", dependencies=[Depends(rate_limit("interviews:list", 120))])
def list_interviews(
    db: DbSession,
    user: InterviewReader,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, max_length=30),
):
    items, total = InterviewService(db).list_interviews(page, page_size, status)
    return success({"items": items, "total": total, "page": page, "page_size": page_size})


@router.post("")
def create_interview(payload: InterviewCreate, db: DbSession, user: InterviewScheduler):
    return success(InterviewService(db).create_interview(payload, user), status_code=201)


@router.get("/{interview_id}")
def get_interview(interview_id: int, db: DbSession, user: InterviewReader):
    return success(InterviewService(db).get_interview(interview_id))


@router.patch("/{interview_id}")
def update_interview(
    interview_id: int, payload: InterviewUpdate, db: DbSession, user: InterviewManager
):
    return success(InterviewService(db).update_interview(interview_id, payload, user))


@router.post("/{interview_id}/cancel")
def cancel_interview(
    interview_id: int,
    payload: InterviewCancelRequest,
    db: DbSession,
    user: InterviewManager,
):
    return success(InterviewService(db).cancel(interview_id, payload.reason, user))


@router.post("/{interview_id}/participants")
def add_participant(
    interview_id: int, payload: ParticipantCreate, db: DbSession, user: InterviewScheduler
):
    return success(
        InterviewService(db).add_participant(interview_id, payload, user), status_code=201
    )


@router.post("/{interview_id}/feedback")
def submit_feedback(
    interview_id: int, payload: FeedbackRequest, db: DbSession, user: InterviewWriter
):
    return success(InterviewService(db).feedback(interview_id, payload, user))
