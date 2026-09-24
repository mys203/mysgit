from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.exceptions import ConflictError, NotFoundError
from app.dao.repositories import ApplicationDAO, CandidateDAO, JobDAO, ResumeDAO
from app.schemas.applications import ApplicationCreate, ApplicationStageUpdate
from app.schemas.candidates import CandidateCreate, CandidateUpdate
from app.security.dependencies import UserPrincipal
from app.services.helpers import model_dict, record_operation


class RecruitmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.candidates = CandidateDAO(db)
        self.jobs = JobDAO(db)
        self.resumes = ResumeDAO(db)
        self.applications = ApplicationDAO(db)

    def list_candidates(
        self,
        page: int,
        page_size: int,
        search: str | None,
        status: str | None,
    ):
        filters = {"status": status} if status else {}
        rows, total = self.candidates.paginate(
            page,
            page_size,
            filters=filters,
            search=search,
            search_fields=("name", "email", "phone", "current_company", "current_title"),
        )
        return [model_dict(item) for item in rows], total

    def get_candidate(self, candidate_id: int) -> dict:
        candidate = self.candidates.get(candidate_id)
        if not candidate:
            raise NotFoundError("候选人不存在")
        return model_dict(candidate)

    def create_candidate(self, payload: CandidateCreate, user: UserPrincipal) -> dict:
        if self.candidates.find_duplicate(payload.email, payload.phone):
            raise ConflictError("候选人邮箱或手机号已存在")
        candidate = self.candidates.create({**payload.model_dump(), "created_by": user.id})
        record_operation(
            self.db,
            user,
            method="POST",
            path="/api/v1/candidates",
            action="CREATE",
            resource_type="candidate",
            resource_id=candidate.id,
        )
        return model_dict(candidate)

    def update_candidate(
        self, candidate_id: int, payload: CandidateUpdate, user: UserPrincipal
    ) -> dict:
        candidate = self.candidates.get(candidate_id)
        if not candidate:
            raise NotFoundError("候选人不存在")
        result = model_dict(
            self.candidates.update(candidate, payload.model_dump(exclude_unset=True))
        )
        record_operation(
            self.db,
            user,
            method="PATCH",
            path=f"/api/v1/candidates/{candidate_id}",
            action="UPDATE",
            resource_type="candidate",
            resource_id=candidate_id,
        )
        return result

    def delete_candidate(self, candidate_id: int, user: UserPrincipal) -> None:
        candidate = self.candidates.get(candidate_id)
        if not candidate:
            raise NotFoundError("候选人不存在")
        self.candidates.delete(candidate)
        record_operation(
            self.db,
            user,
            method="DELETE",
            path=f"/api/v1/candidates/{candidate_id}",
            action="DELETE",
            resource_type="candidate",
            resource_id=candidate_id,
        )

    def list_applications(
        self,
        page: int,
        page_size: int,
        job_id: int | None,
        candidate_id: int | None,
        stage: str | None,
    ):
        filters = {}
        if job_id:
            filters["job_id"] = job_id
        if candidate_id:
            filters["candidate_id"] = candidate_id
        if stage:
            filters["stage"] = stage
        rows, total = self.applications.paginate(page, page_size, filters=filters)
        return [model_dict(item) for item in rows], total

    def get_application(self, application_id: int) -> dict:
        application = self.applications.get(application_id)
        if not application:
            raise NotFoundError("应聘记录不存在")
        return model_dict(application)

    def create_application(self, payload: ApplicationCreate, user: UserPrincipal) -> dict:
        if not self.jobs.get(payload.job_id):
            raise NotFoundError("岗位不存在")
        if not self.candidates.get(payload.candidate_id):
            raise NotFoundError("候选人不存在")
        if payload.resume_id and not self.resumes.get(payload.resume_id):
            raise NotFoundError("简历不存在")
        if self.applications.get_by_job_candidate(payload.job_id, payload.candidate_id):
            raise ConflictError("该候选人已应聘此岗位")
        application = self.applications.create(
            {**payload.model_dump(), "stage": "APPLIED", "updated_by": user.id}
        )
        record_operation(
            self.db,
            user,
            method="POST",
            path="/api/v1/applications",
            action="CREATE",
            resource_type="application",
            resource_id=application.id,
        )
        return model_dict(application)

    def update_stage(
        self,
        application_id: int,
        payload: ApplicationStageUpdate,
        user: UserPrincipal,
    ) -> dict:
        application = self.applications.get(application_id)
        if not application:
            raise NotFoundError("应聘记录不存在")
        detail = {"previous_stage": application.stage}
        if payload.reason:
            detail["reason"] = payload.reason
        application = self.applications.update(
            application,
            {"stage": payload.stage, "updated_by": user.id},
        )
        record_operation(
            self.db,
            user,
            method="PATCH",
            path=f"/api/v1/applications/{application_id}/stage",
            action="UPDATE_STAGE",
            resource_type="application",
            resource_id=application_id,
            detail=detail,
        )
        return {**model_dict(application), "transition": detail}
