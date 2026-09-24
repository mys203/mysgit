from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.common.exceptions import ConflictError, NotFoundError
from app.config.redis import redis_manager
from app.config.settings import settings
from app.dao.repositories import JobDAO
from app.schemas.ai import MatchRequest
from app.schemas.jobs import JobCreate, JobUpdate
from app.security.dependencies import UserPrincipal
from app.services.helpers import model_dict, record_operation


class JobService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.jobs = JobDAO(db)

    def list_jobs(
        self,
        page: int,
        page_size: int,
        search: str | None = None,
        status: str | None = None,
        category_id: int | None = None,
        department_id: int | None = None,
    ) -> tuple[list[dict], int]:
        cache_key = self._list_cache_key(page, page_size, search, status, category_id, department_id)
        cached = redis_manager.get(cache_key)
        if cached:
            payload = json.loads(cached)
            return payload["items"], payload["total"]
        filters = {}
        if status:
            filters["status"] = status
        if category_id:
            filters["category_id"] = category_id
        if department_id:
            filters["department_id"] = department_id
        rows, total = self.jobs.paginate(
            page, page_size, filters=filters, search=search, search_fields=("title", "code", "location")
        )
        items = [self._job_dict(item) for item in rows]
        redis_manager.set(
            cache_key,
            json.dumps({"items": items, "total": total}, ensure_ascii=False, default=str),
            settings.cache_ttl_seconds,
        )
        return items, total

    def get_job(self, job_id: int) -> dict:
        cache_key = f"recruit:cache:job:{job_id}"
        cached = redis_manager.get(cache_key)
        if cached:
            return json.loads(cached)
        job = self.jobs.get(job_id)
        if not job:
            raise NotFoundError("岗位不存在")
        result = self._job_dict(job)
        redis_manager.set(
            cache_key,
            json.dumps(result, ensure_ascii=False, default=str),
            settings.cache_ttl_seconds,
        )
        return result

    def create_job(self, payload: JobCreate, user: UserPrincipal) -> dict:
        if self.jobs.get_by_code(payload.code):
            raise ConflictError("岗位编码已存在")
        values = payload.model_dump()
        values["created_by"] = user.id
        job = self.jobs.create(values)
        self._invalidate_list_cache()
        record_operation(
            self.db, user, method="POST", path="/api/v1/jobs", action="CREATE",
            resource_type="job", resource_id=job.id,
        )
        return self._job_dict(job)

    def update_job(self, job_id: int, payload: JobUpdate, user: UserPrincipal) -> dict:
        job = self.jobs.get(job_id)
        if not job:
            raise NotFoundError("岗位不存在")
        if job.status in {"PUBLISHED", "CLOSED"} and payload.skills is not None:
            raise ConflictError("已发布或已关闭岗位不可直接修改技能要求")
        updated = self.jobs.update(job, payload.model_dump(exclude_unset=True))
        self._invalidate_job_cache(job_id)
        record_operation(
            self.db, user, method="PATCH", path=f"/api/v1/jobs/{job_id}", action="UPDATE",
            resource_type="job", resource_id=job_id,
        )
        return self._job_dict(updated)

    def delete_job(self, job_id: int, user: UserPrincipal) -> None:
        job = self.jobs.get(job_id)
        if not job:
            raise NotFoundError("岗位不存在")
        self.jobs.delete(job)
        self._invalidate_job_cache(job_id)
        record_operation(
            self.db, user, method="DELETE", path=f"/api/v1/jobs/{job_id}", action="DELETE",
            resource_type="job", resource_id=job_id,
        )

    def publish_job(self, job_id: int, user: UserPrincipal) -> dict:
        job = self.jobs.get(job_id)
        if not job:
            raise NotFoundError("岗位不存在")
        if job.status == "PUBLISHED":
            raise ConflictError("岗位已发布")
        job = self.jobs.update(
            job, {"status": "PUBLISHED", "published_at": datetime.now(timezone.utc), "closed_at": None}
        )
        self._invalidate_job_cache(job_id)
        record_operation(
            self.db, user, method="POST", path=f"/api/v1/jobs/{job_id}/publish",
            action="PUBLISH", resource_type="job", resource_id=job_id,
        )
        return self._job_dict(job)

    def close_job(self, job_id: int, user: UserPrincipal) -> dict:
        job = self.jobs.get(job_id)
        if not job:
            raise NotFoundError("岗位不存在")
        job = self.jobs.update(
            job, {"status": "CLOSED", "closed_at": datetime.now(timezone.utc)}
        )
        self._invalidate_job_cache(job_id)
        record_operation(
            self.db, user, method="POST", path=f"/api/v1/jobs/{job_id}/close",
            action="CLOSE", resource_type="job", resource_id=job_id,
        )
        return self._job_dict(job)

    def get_matches(self, job_id: int):
        if not self.jobs.get(job_id):
            raise NotFoundError("岗位不存在")
        from app.services.ai_service import AIService

        return AIService(self.db).latest_matches(job_id)

    def _invalidate_job_cache(self, job_id: int) -> None:
        redis_manager.delete(f"recruit:cache:job:{job_id}")
        self._invalidate_list_cache()

    @staticmethod
    def _invalidate_list_cache() -> None:
        redis_manager.increment(
            "recruit:cache:jobs:version",
            max(settings.cache_ttl_seconds, 300),
        )

    @staticmethod
    def _job_dict(job) -> dict:
        return model_dict(job)

    @staticmethod
    def _list_cache_key(page: int, page_size: int, search, status, category_id, department_id) -> str:
        raw = json.dumps(
            {
                "page": page,
                "page_size": page_size,
                "search": search,
                "status": status,
                "category_id": category_id,
                "department_id": department_id,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
        version = redis_manager.get("recruit:cache:jobs:version") or "0"
        return f"recruit:cache:jobs:list:{version}:{digest}"
