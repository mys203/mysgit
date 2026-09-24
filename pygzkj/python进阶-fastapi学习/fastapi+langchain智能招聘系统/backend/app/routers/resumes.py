from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.common.exceptions import ConflictError
from app.common.response import success
from app.config.database import get_db
from app.schemas.resumes import ParseConfirmRequest
from app.security.dependencies import require_permissions
from app.security.rate_limit import rate_limit
from app.services.resume_service import ResumeService, run_resume_parse_task

router = APIRouter(tags=["简历"])
DbSession = Annotated[Session, Depends(get_db)]
ResumeReader = Annotated[object, Depends(require_permissions("resumes:read"))]
ResumeWriter = Annotated[object, Depends(require_permissions("resumes:write"))]


@router.post("/resumes/upload", dependencies=[Depends(rate_limit("resumes:upload", 30))])
async def upload_resume(
    db: DbSession,
    user: ResumeWriter,
    file: UploadFile = File(...),
):
    if not file.filename:
        raise ConflictError("文件名不能为空")
    content = await file.read()
    item = ResumeService(db).upload(file.filename, file.content_type or "", content, user)
    return success(item, status_code=201 if not item.get("duplicated") else 200)


@router.get("/resumes", dependencies=[Depends(rate_limit("resumes:list", 120))])
def list_resumes(
    db: DbSession,
    user: ResumeReader,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    status: str | None = Query(None, max_length=30),
):
    items, total = ResumeService(db).list_resumes(page, page_size, search, status)
    return success({"items": items, "total": total, "page": page, "page_size": page_size})


@router.get("/resumes/{resume_id}")
def get_resume(resume_id: int, db: DbSession, user: ResumeReader):
    return success(ResumeService(db).get_resume(resume_id))


@router.post("/resumes/{resume_id}/parse")
def parse_resume(
    resume_id: int,
    background_tasks: BackgroundTasks,
    db: DbSession,
    user: ResumeWriter,
):
    result = ResumeService(db).prepare_parse(resume_id, user)
    background_tasks.add_task(
        run_resume_parse_task,
        result["task_no"],
        resume_id,
        result["parse_record"]["id"],
        user.id,
    )
    return success(result, status_code=202)


@router.get("/resumes/{resume_id}/parse-records")
def list_parse_records(
    resume_id: int,
    db: DbSession,
    user: ResumeReader,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = ResumeService(db).list_parse_records(resume_id, page, page_size)
    return success({"items": items, "total": total, "page": page, "page_size": page_size})


@router.get("/parse-records/{record_id}")
def get_parse_record(record_id: int, db: DbSession, user: ResumeReader):
    return success(ResumeService(db).get_parse_record(record_id))


@router.post("/parse-records/{record_id}/confirm")
def confirm_parse_record(
    record_id: int,
    payload: ParseConfirmRequest,
    db: DbSession,
    user: ResumeWriter,
):
    return success(ResumeService(db).confirm(record_id, payload, user))
