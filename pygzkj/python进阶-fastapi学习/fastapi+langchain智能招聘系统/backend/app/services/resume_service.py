from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.common.exceptions import ConflictError, NotFoundError
from app.config.database import SessionLocal
from app.config.settings import settings
from app.dao.repositories import (
    ApplicationDAO,
    CandidateDAO,
    JobDAO,
    ResumeDAO,
    ResumeParseDAO,
)
from app.schemas.resumes import ParseConfirmRequest
from app.security.dependencies import UserPrincipal
from app.services.helpers import model_dict, record_operation

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/octet-stream",
}
RESUME_RESPONSE_FIELDS = {
    "id",
    "candidate_id",
    "filename",
    "file_hash",
    "file_type",
    "file_size",
    "status",
    "uploaded_by",
    "created_at",
    "updated_at",
}
CANDIDATE_MERGE_FIELDS = {
    "name",
    "email",
    "phone",
    "education",
    "work_years",
    "current_company",
    "current_title",
    "skills",
    "summary",
}


class ResumeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.resumes = ResumeDAO(db)
        self.records = ResumeParseDAO(db)
        self.candidates = CandidateDAO(db)
        self.applications = ApplicationDAO(db)
        self.jobs = JobDAO(db)

    def upload(self, filename: str, content_type: str, content: bytes, user: UserPrincipal) -> dict:
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise ConflictError("仅支持 PDF、DOCX、TXT 简历")
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            raise ConflictError("文件类型不受支持")
        max_size = settings.max_upload_mb * 1024 * 1024
        if not content:
            raise ConflictError("上传文件为空")
        if len(content) > max_size:
            raise ConflictError(f"简历大小不能超过 {settings.max_upload_mb}MB")
        digest = hashlib.sha256(content).hexdigest()
        existing = self.resumes.get_by_hash(digest)
        if existing:
            return {**self._resume_dict(existing), "duplicated": True}
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(filename).name
        path = settings.upload_dir / f"{digest}{suffix}"
        path.write_bytes(content)
        resume = self.resumes.create(
            {
                "filename": safe_name,
                "file_path": str(path),
                "file_hash": digest,
                "file_type": suffix.lstrip("."),
                "file_size": len(content),
                "status": "UPLOADED",
                "uploaded_by": user.id,
            }
        )
        record_operation(
            self.db,
            user,
            method="POST",
            path="/api/v1/resumes/upload",
            action="UPLOAD",
            resource_type="resume",
            resource_id=resume.id,
        )
        return {**self._resume_dict(resume), "duplicated": False}

    def list_resumes(
        self,
        page: int,
        page_size: int,
        search: str | None = None,
        status: str | None = None,
    ):
        filters = {"status": status} if status else {}
        rows, total = self.resumes.paginate(
            page,
            page_size,
            filters=filters,
            search=search,
            search_fields=("filename", "file_hash"),
        )
        return [self._resume_dict(item) for item in rows], total

    def get_resume(self, resume_id: int) -> dict:
        resume = self.resumes.get(resume_id)
        if not resume:
            raise NotFoundError("简历不存在")
        return self._resume_dict(resume)

    def prepare_parse(self, resume_id: int, user: UserPrincipal) -> dict:
        resume = self.resumes.get(resume_id)
        if not resume:
            raise NotFoundError("简历不存在")
        if not Path(resume.file_path).exists():
            raise NotFoundError("简历文件不存在")
        from app.services.ai_service import AIService

        task = AIService(self.db).prepare_resume_parse_task(resume.id, user.id)
        record = self.records.create(
            {
                "resume_id": resume.id,
                "task_id": task.id,
                "status": "PENDING",
                "parsed_data": {},
                "confidence": 0.0,
            }
        )
        record_operation(
            self.db,
            user,
            method="POST",
            path=f"/api/v1/resumes/{resume_id}/parse",
            action="SUBMIT_PARSE",
            resource_type="resume",
            resource_id=resume_id,
            detail={"task_no": task.task_no, "parse_record_id": record.id},
        )
        return {
            "parse_record": self._parse_record_dict(record),
            "task_no": task.task_no,
            "degraded": False,
            "status": "PENDING",
        }

    def execute_parse_task(
        self,
        task_no: str,
        *,
        resume_id: int,
        record_id: int,
        user_id: int,
    ) -> None:
        resume = self.resumes.get(resume_id)
        record = self.records.get(record_id)
        if not resume or not record:
            from app.services.ai_service import AIService

            AIService(self.db).fail_task(task_no, "简历或解析记录不存在")
            return
        text = ""
        try:
            text = self._extract_text(resume.file_path, resume.file_type)
            if not text.strip():
                raise ConflictError("未能从文件中提取到文本")
            self.resumes.update(resume, {"raw_text": text, "status": "PARSING"})
            from app.services.ai_service import AIService

            ai_service = AIService(self.db)
            _, output, degraded = ai_service.execute_resume_parse_task(
                task_no,
                text,
                resume_id=resume.id,
                record_id=record.id,
                user_id=user_id,
            )
            self.resumes.update(resume, {"status": "PARSED"})
            ai_service.complete_task(
                task_no,
                {
                    **output,
                    "resume_id": resume.id,
                    "parse_record_id": record.id,
                    "parse_status": "PARSED",
                    "resume_status": "PARSED",
                },
                degraded,
                text,
            )
        except Exception as exc:
            self.db.rollback()
            try:
                self.records.update(
                    record,
                    {"status": "FAILED", "parsed_data": {"error": str(exc)[:500]}},
                )
                self.resumes.update(resume, {"status": "FAILED"})
            except Exception:
                self.db.rollback()
                logger.exception("写入简历解析失败状态时出错：%s", task_no)
            from app.services.ai_service import AIService

            AIService(self.db).fail_task(task_no, str(exc), text)
            logger.exception("后台简历解析失败：%s", task_no)

    def list_parse_records(self, resume_id: int, page: int, page_size: int):
        if not self.resumes.get(resume_id):
            raise NotFoundError("简历不存在")
        rows, total = self.records.paginate(page, page_size, filters={"resume_id": resume_id})
        return [model_dict(item) for item in rows], total

    def get_parse_record(self, record_id: int) -> dict:
        record = self.records.get(record_id)
        if not record:
            raise NotFoundError("解析记录不存在")
        return model_dict(record)

    def confirm(self, record_id: int, payload: ParseConfirmRequest, user: UserPrincipal) -> dict:
        record = self.records.get(record_id)
        if not record:
            raise NotFoundError("解析记录不存在")
        if record.status == "CONFIRMED":
            raise ConflictError("解析记录已确认")
        if payload.job_position_id and not self.jobs.get(payload.job_position_id):
            raise NotFoundError("岗位不存在")
        resume = self.resumes.get(record.resume_id)
        if not resume:
            raise NotFoundError("简历不存在")
        data = dict(record.parsed_data or {})
        override_data: dict = {}
        if payload.candidate_override:
            override_data = payload.candidate_override.model_dump(
                exclude_unset=True, exclude_none=True
            )
            data.update(override_data)
        candidate = self.candidates.get(payload.candidate_id) if payload.candidate_id else None
        if payload.candidate_id and not candidate:
            raise NotFoundError("候选人不存在")
        if candidate is None:
            candidate = self.candidates.find_duplicate(data.get("email"), data.get("phone"))
        if candidate is not None:
            candidate_updates: dict = {}
            for field in CANDIDATE_MERGE_FIELDS:
                if field in override_data:
                    candidate_updates[field] = override_data[field]
                    continue
                current_value = getattr(candidate, field)
                parsed_value = data.get(field)
                if current_value in (None, "", []) and parsed_value not in (None, "", []):
                    candidate_updates[field] = parsed_value
            if candidate_updates:
                candidate = self.candidates.update(candidate, candidate_updates)
        if candidate is None:
            candidate = self.candidates.create(
                {
                    "name": data.get("name") or Path(resume.filename).stem,
                    "email": data.get("email"),
                    "phone": data.get("phone"),
                    "education": data.get("education"),
                    "work_years": data.get("work_years"),
                    "current_company": data.get("current_company"),
                    "current_title": data.get("current_title"),
                    "skills": data.get("skills") or [],
                    "summary": data.get("summary"),
                    "source": "RESUME",
                    "created_by": user.id,
                }
            )
        record_operation(
            self.db,
            user,
            method="POST",
            path=f"/api/v1/parse-records/{record_id}/confirm",
            action="CONFIRM_PARSE",
            resource_type="resume_parse_record",
            resource_id=record_id,
            detail={"candidate_id": candidate.id, "job_position_id": payload.job_position_id},
        )
        self.resumes.update(resume, {"candidate_id": candidate.id, "status": "CONFIRMED"})
        self.records.update(
            record,
            {
                "status": "CONFIRMED",
                "confirmed_by": user.id,
                "confirmed_at": model_datetime_now(),
            },
        )
        application = None
        if payload.job_position_id:
            application = self.applications.get_by_job_candidate(
                payload.job_position_id, candidate.id
            )
            if application is None:
                application = self.applications.create(
                    {
                        "job_id": payload.job_position_id,
                        "candidate_id": candidate.id,
                        "resume_id": resume.id,
                        "stage": "APPLIED",
                        "source": "RESUME",
                        "updated_by": user.id,
                    }
                )
        return {
            "resume_id": resume.id,
            "parse_record_id": record.id,
            "candidate_id": candidate.id,
            "application_id": application.id if application else None,
            "status": "CONFIRMED",
        }

    @staticmethod
    def _resume_dict(resume) -> dict:
        return {
            key: value
            for key, value in model_dict(resume).items()
            if key in RESUME_RESPONSE_FIELDS
        }

    @staticmethod
    def _parse_record_dict(record) -> dict:
        return model_dict(record)

    @staticmethod
    def _extract_text(file_path: str, file_type: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise NotFoundError("简历文件不存在")
        if file_type == "txt":
            raw = path.read_bytes()
            try:
                return raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                return raw.decode("gb18030", errors="ignore")
        if file_type == "pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        if file_type == "docx":
            from docx import Document

            document = Document(str(path))
            return "\n".join(paragraph.text for paragraph in document.paragraphs)
        raise ConflictError("不支持的文件类型")


def model_datetime_now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)


def run_resume_parse_task(
    task_no: str, resume_id: int, record_id: int, user_id: int
) -> None:
    try:
        with SessionLocal() as db:
            ResumeService(db).execute_parse_task(
                task_no,
                resume_id=resume_id,
                record_id=record_id,
                user_id=user_id,
            )
    except Exception:
        logger.exception("简历解析后台任务异常：%s", task_no)
