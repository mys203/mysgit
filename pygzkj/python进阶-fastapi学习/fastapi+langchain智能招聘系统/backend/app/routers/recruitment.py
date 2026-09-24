from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import success
from app.config.database import get_db
from app.schemas.applications import ApplicationCreate, ApplicationStageUpdate
from app.schemas.candidates import CandidateCreate, CandidateUpdate
from app.security.dependencies import require_permissions
from app.security.rate_limit import rate_limit
from app.services.recruitment_service import RecruitmentService

router = APIRouter(tags=["候选人与应聘"])
DbSession = Annotated[Session, Depends(get_db)]
CandidateReader = Annotated[object, Depends(require_permissions("candidates:read"))]
CandidateWriter = Annotated[object, Depends(require_permissions("candidates:write"))]
ApplicationReader = Annotated[object, Depends(require_permissions("applications:read"))]
ApplicationWriter = Annotated[object, Depends(require_permissions("applications:write"))]


@router.get("/candidates", dependencies=[Depends(rate_limit("candidates:list", 180))])
def list_candidates(
    db: DbSession,
    user: CandidateReader,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    status: str | None = Query(None, max_length=30),
):
    items, total = RecruitmentService(db).list_candidates(page, page_size, search, status)
    return success({"items": items, "total": total, "page": page, "page_size": page_size})


@router.post("/candidates")
def create_candidate(payload: CandidateCreate, db: DbSession, user: CandidateWriter):
    return success(RecruitmentService(db).create_candidate(payload, user), status_code=201)


@router.get("/candidates/{candidate_id}")
def get_candidate(candidate_id: int, db: DbSession, user: CandidateReader):
    return success(RecruitmentService(db).get_candidate(candidate_id))


@router.patch("/candidates/{candidate_id}")
def update_candidate(
    candidate_id: int, payload: CandidateUpdate, db: DbSession, user: CandidateWriter
):
    return success(RecruitmentService(db).update_candidate(candidate_id, payload, user))


@router.delete("/candidates/{candidate_id}")
def delete_candidate(candidate_id: int, db: DbSession, user: CandidateWriter):
    RecruitmentService(db).delete_candidate(candidate_id, user)
    return success({"id": candidate_id, "deleted": True})


@router.get("/applications")
def list_applications(
    db: DbSession,
    user: ApplicationReader,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    job_id: int | None = None,
    candidate_id: int | None = None,
    stage: str | None = Query(None, max_length=30),
):
    items, total = RecruitmentService(db).list_applications(
        page, page_size, job_id, candidate_id, stage
    )
    return success({"items": items, "total": total, "page": page, "page_size": page_size})


@router.post("/applications")
def create_application(payload: ApplicationCreate, db: DbSession, user: ApplicationWriter):
    return success(RecruitmentService(db).create_application(payload, user), status_code=201)


@router.get("/applications/{application_id}")
def get_application(application_id: int, db: DbSession, user: ApplicationReader):
    return success(RecruitmentService(db).get_application(application_id))


@router.patch("/applications/{application_id}/stage")
def update_application_stage(
    application_id: int,
    payload: ApplicationStageUpdate,
    db: DbSession,
    user: ApplicationWriter,
):
    return success(RecruitmentService(db).update_stage(application_id, payload, user))
