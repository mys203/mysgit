from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import success
from app.config.database import get_db
from app.schemas.jobs import JobCreate, JobUpdate
from app.security.dependencies import require_permissions
from app.security.rate_limit import rate_limit
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["岗位"])
DbSession = Annotated[Session, Depends(get_db)]
JobReader = Annotated[object, Depends(require_permissions("jobs:read"))]
JobWriter = Annotated[object, Depends(require_permissions("jobs:write"))]


@router.get("", dependencies=[Depends(rate_limit("jobs:list", 180))])
def list_jobs(
    db: DbSession,
    user: JobReader,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    status: str | None = Query(None, max_length=30),
    category_id: int | None = None,
    department_id: int | None = None,
):
    items, total = JobService(db).list_jobs(
        page, page_size, search, status, category_id, department_id
    )
    return success({"items": items, "total": total, "page": page, "page_size": page_size})


@router.post("", dependencies=[Depends(rate_limit("jobs:create", 60))])
def create_job(payload: JobCreate, db: DbSession, user: JobWriter):
    return success(JobService(db).create_job(payload, user), status_code=201)


@router.get("/{job_id}")
def get_job(job_id: int, db: DbSession, user: JobReader):
    return success(JobService(db).get_job(job_id))


@router.patch("/{job_id}")
def update_job(job_id: int, payload: JobUpdate, db: DbSession, user: JobWriter):
    return success(JobService(db).update_job(job_id, payload, user))


@router.delete("/{job_id}")
def delete_job(job_id: int, db: DbSession, user: JobWriter):
    JobService(db).delete_job(job_id, user)
    return success({"id": job_id, "deleted": True})


@router.post("/{job_id}/publish")
def publish_job(job_id: int, db: DbSession, user: JobWriter):
    return success(JobService(db).publish_job(job_id, user))


@router.post("/{job_id}/close")
def close_job(job_id: int, db: DbSession, user: JobWriter):
    return success(JobService(db).close_job(job_id, user))


@router.get("/{job_id}/matches")
def job_matches(job_id: int, db: DbSession, user: JobReader):
    return success(JobService(db).get_matches(job_id))
