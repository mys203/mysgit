from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, or_, select, update
from sqlalchemy.orm import Session

from app.models.entities import (
    AIExecutionLog,
    AIChatMessage,
    AIChatSession,
    AITask,
    Candidate,
    InterviewParticipant,
    InterviewQuestion,
    InterviewSchedule,
    JobApplication,
    JobCategory,
    JobMatchResult,
    JobPosition,
    OperationLog,
    Resume,
    ResumeParseRecord,
    SysDepartment,
    SysPermission,
    SysRole,
    SysRolePermission,
    SysUser,
    SysUserRole,
    VectorDocument,
)

ModelT = TypeVar("ModelT")


class BaseDAO(Generic[ModelT]):
    def __init__(self, db: Session, model: type[ModelT]) -> None:
        self.db = db
        self.model = model

    def get(self, item_id: int) -> ModelT | None:
        return self.db.get(self.model, item_id)

    def first(self, **filters: Any) -> ModelT | None:
        statement = select(self.model)
        for field, value in filters.items():
            statement = statement.where(getattr(self.model, field) == value)
        return self.db.scalars(statement.limit(1)).first()

    def list_all(self, limit: int = 1000, **filters: Any) -> list[ModelT]:
        statement = self._apply_filters(select(self.model), filters)
        return list(self.db.scalars(statement.limit(limit)).all())

    def paginate(
        self,
        page: int,
        page_size: int,
        *,
        filters: dict[str, Any] | None = None,
        search: str | None = None,
        search_fields: tuple[str, ...] = (),
        order_by: Any = None,
        statement: Select[Any] | None = None,
    ) -> tuple[list[ModelT], int]:
        base = statement if statement is not None else select(self.model)
        base = self._apply_filters(base, filters or {})
        if search and search_fields:
            conditions = [
                getattr(self.model, field).ilike(f"%{search.strip()}%")
                for field in search_fields
            ]
            base = base.where(or_(*conditions))
        count_statement = select(func.count()).select_from(base.order_by(None).subquery())
        total = int(self.db.scalar(count_statement) or 0)
        if order_by is not None:
            base = base.order_by(order_by)
        elif hasattr(self.model, "id"):
            base = base.order_by(self.model.id.desc())
        rows = self.db.scalars(base.offset((page - 1) * page_size).limit(page_size)).all()
        return list(rows), total

    def create(self, values: dict[str, Any]) -> ModelT:
        instance = self.model(**values)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update(self, instance: ModelT, values: dict[str, Any]) -> ModelT:
        for field, value in values.items():
            setattr(instance, field, value)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, instance: ModelT) -> None:
        self.db.delete(instance)
        self.db.commit()

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def count(self, **filters: Any) -> int:
        statement = select(func.count()).select_from(self.model)
        for field, value in filters.items():
            statement = statement.where(getattr(self.model, field) == value)
        return int(self.db.scalar(statement) or 0)

    def _apply_filters(self, statement: Select[Any], filters: dict[str, Any]) -> Select[Any]:
        for field, value in filters.items():
            if isinstance(value, (list, tuple, set)):
                statement = statement.where(getattr(self.model, field).in_(value))
            else:
                statement = statement.where(getattr(self.model, field) == value)
        return statement


class DepartmentDAO(BaseDAO[SysDepartment]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, SysDepartment)

    def get_by_code(self, code: str) -> SysDepartment | None:
        return self.first(code=code, is_deleted=False)

    def list_options(self, search: str | None = None, limit: int = 100):
        statement = select(SysDepartment).where(
            SysDepartment.is_deleted.is_(False),
            SysDepartment.status == "ACTIVE",
        )
        if search:
            statement = statement.where(
                or_(
                    SysDepartment.name.ilike(f"%{search.strip()}%"),
                    SysDepartment.code.ilike(f"%{search.strip()}%"),
                )
            )
        return list(
            self.db.scalars(statement.order_by(SysDepartment.name).limit(limit)).all()
        )


class UserDAO(BaseDAO[SysUser]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, SysUser)

    def get_by_username(self, username: str) -> SysUser | None:
        statement = select(SysUser).where(
            SysUser.username == username,
            SysUser.is_deleted.is_(False),
        )
        return self.db.scalars(statement.limit(1)).first()

    def get_roles(self, user_id: int) -> list[str]:
        statement = (
            select(SysRole.code)
            .join(SysUserRole, SysUserRole.role_id == SysRole.id)
            .where(SysUserRole.user_id == user_id, SysRole.status == "ACTIVE")
            .order_by(SysRole.code)
        )
        return list(self.db.scalars(statement).all())

    def get_permissions(self, user_id: int) -> list[str]:
        statement = (
            select(SysPermission.code)
            .join(
                SysRolePermission,
                SysRolePermission.permission_id == SysPermission.id,
            )
            .join(SysRole, SysRole.id == SysRolePermission.role_id)
            .join(SysUserRole, SysUserRole.role_id == SysRole.id)
            .where(SysUserRole.user_id == user_id, SysRole.status == "ACTIVE")
            .distinct()
            .order_by(SysPermission.code)
        )
        return list(self.db.scalars(statement).all())

    def count_active_admins(self, exclude_user_id: int | None = None) -> int:
        statement = (
            select(func.count(func.distinct(SysUser.id)))
            .select_from(SysUser)
            .join(SysUserRole, SysUserRole.user_id == SysUser.id)
            .join(SysRole, SysRole.id == SysUserRole.role_id)
            .where(
                SysUser.is_deleted.is_(False),
                SysUser.status == "ACTIVE",
                SysRole.code == "ADMIN",
                SysRole.status == "ACTIVE",
            )
        )
        if exclude_user_id is not None:
            statement = statement.where(SysUser.id != exclude_user_id)
        return int(self.db.scalar(statement) or 0)

    def replace_roles(self, user_id: int, role_codes: list[str]) -> None:
        self.db.query(SysUserRole).filter(SysUserRole.user_id == user_id).delete()
        if role_codes:
            roles = self.db.scalars(
                select(SysRole).where(SysRole.code.in_(role_codes), SysRole.status == "ACTIVE")
            ).all()
            role_map = {role.code: role.id for role in roles}
            missing = set(role_codes) - set(role_map)
            if missing:
                raise ValueError(f"角色不存在：{', '.join(sorted(missing))}")
            self.db.add_all(
                [SysUserRole(user_id=user_id, role_id=role_map[code]) for code in role_codes]
            )
        self.db.commit()

    def list_options(
        self,
        search: str | None = None,
        role_code: str | None = None,
        limit: int = 100,
    ) -> list[SysUser]:
        statement = select(SysUser).where(
            SysUser.is_deleted.is_(False),
            SysUser.status == "ACTIVE",
        )
        if search:
            statement = statement.where(
                or_(
                    SysUser.username.ilike(f"%{search.strip()}%"),
                    SysUser.real_name.ilike(f"%{search.strip()}%"),
                )
            )
        if role_code:
            statement = (
                statement.join(SysUserRole, SysUserRole.user_id == SysUser.id)
                .join(SysRole, SysRole.id == SysUserRole.role_id)
                .where(SysRole.code == role_code, SysRole.status == "ACTIVE")
            )
        statement = statement.distinct().order_by(SysUser.real_name).limit(limit)
        return list(self.db.scalars(statement).all())


class RoleDAO(BaseDAO[SysRole]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, SysRole)

    def get_by_code(self, code: str) -> SysRole | None:
        return self.first(code=code)


class PermissionDAO(BaseDAO[SysPermission]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, SysPermission)


class RolePermissionDAO(BaseDAO[SysRolePermission]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, SysRolePermission)


class JobCategoryDAO(BaseDAO[JobCategory]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, JobCategory)

    def get_by_code(self, code: str) -> JobCategory | None:
        return self.first(code=code)


class JobDAO(BaseDAO[JobPosition]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, JobPosition)

    def get_by_code(self, code: str) -> JobPosition | None:
        return self.first(code=code)

    def find_by_ids(self, ids: list[int]) -> list[JobPosition]:
        if not ids:
            return []
        return list(self.db.scalars(select(JobPosition).where(JobPosition.id.in_(ids))).all())

    def status_counts(self) -> dict[str, int]:
        statement = select(JobPosition.status, func.count()).group_by(JobPosition.status)
        return {status: int(count) for status, count in self.db.execute(statement).all()}


class CandidateDAO(BaseDAO[Candidate]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Candidate)

    def find_by_ids(self, ids: list[int]) -> list[Candidate]:
        if not ids:
            return []
        return list(self.db.scalars(select(Candidate).where(Candidate.id.in_(ids))).all())

    def find_duplicate(self, email: str | None, phone: str | None) -> Candidate | None:
        conditions = []
        if email:
            conditions.append(Candidate.email == email)
        if phone:
            conditions.append(Candidate.phone == phone)
        if not conditions:
            return None
        return self.db.scalars(select(Candidate).where(or_(*conditions)).limit(1)).first()

    def status_counts(self) -> dict[str, int]:
        statement = select(Candidate.status, func.count()).group_by(Candidate.status)
        return {status: int(count) for status, count in self.db.execute(statement).all()}


class ResumeDAO(BaseDAO[Resume]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Resume)

    def get_by_hash(self, file_hash: str) -> Resume | None:
        return self.first(file_hash=file_hash)


class ResumeParseDAO(BaseDAO[ResumeParseRecord]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ResumeParseRecord)

    def latest_for_resume(self, resume_id: int) -> ResumeParseRecord | None:
        statement = (
            select(ResumeParseRecord)
            .where(ResumeParseRecord.resume_id == resume_id)
            .order_by(ResumeParseRecord.id.desc())
            .limit(1)
        )
        return self.db.scalars(statement).first()


class ApplicationDAO(BaseDAO[JobApplication]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, JobApplication)

    def get_by_job_candidate(self, job_id: int, candidate_id: int) -> JobApplication | None:
        return self.first(job_id=job_id, candidate_id=candidate_id)

    def stage_counts(self) -> dict[str, int]:
        statement = select(JobApplication.stage, func.count()).group_by(JobApplication.stage)
        return {stage: int(count) for stage, count in self.db.execute(statement).all()}


class AITaskDAO(BaseDAO[AITask]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, AITask)

    def get_by_task_no(self, task_no: str) -> AITask | None:
        return self.first(task_no=task_no)

    def status_counts(self) -> dict[str, int]:
        statement = select(AITask.status, func.count()).group_by(AITask.status)
        return {status: int(count) for status, count in self.db.execute(statement).all()}

    def fail_incomplete_tasks(self, message: str, cutoff: datetime) -> int:
        statement = (
            update(AITask)
            .where(
                or_(
                    (AITask.status == "PENDING") & (AITask.created_at < cutoff),
                    (AITask.status == "RUNNING")
                    & (AITask.started_at.is_not(None))
                    & (AITask.started_at < cutoff),
                    (AITask.status == "RUNNING")
                    & (AITask.started_at.is_(None))
                    & (AITask.created_at < cutoff),
                )
            )
            .values(
                status="FAILED",
                error_message=message,
                degraded=True,
                finished_at=datetime.now(timezone.utc),
            )
        )
        result = self.db.execute(statement)
        self.db.commit()
        return int(result.rowcount or 0)


class AIChatSessionDAO(BaseDAO[AIChatSession]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, AIChatSession)

    def get_owned(self, session_id: int, user_id: int) -> AIChatSession | None:
        statement = select(AIChatSession).where(
            AIChatSession.id == session_id,
            AIChatSession.user_id == user_id,
            AIChatSession.is_deleted.is_(False),
        )
        return self.db.scalars(statement.limit(1)).first()

    def paginate_owned(
        self,
        user_id: int,
        page: int,
        page_size: int,
        keyword: str | None = None,
    ) -> tuple[list[AIChatSession], int]:
        statement = select(AIChatSession).where(
            AIChatSession.user_id == user_id,
            AIChatSession.is_deleted.is_(False),
        )
        if keyword:
            statement = statement.where(
                AIChatSession.title.ilike(f"%{keyword.strip()}%")
            )
        count_statement = select(func.count()).select_from(statement.subquery())
        total = int(self.db.scalar(count_statement) or 0)
        rows = self.db.scalars(
            statement.order_by(
                AIChatSession.last_message_at.desc(),
                AIChatSession.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return list(rows), total

    def soft_delete(self, session: AIChatSession) -> AIChatSession:
        session.is_deleted = True
        session.deleted_at = datetime.now(timezone.utc)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session


class AIChatMessageDAO(BaseDAO[AIChatMessage]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, AIChatMessage)

    def get_owned(
        self,
        message_id: int,
        user_id: int,
    ) -> AIChatMessage | None:
        statement = (
            select(AIChatMessage)
            .join(
                AIChatSession,
                AIChatSession.id == AIChatMessage.session_id,
            )
            .where(
                AIChatMessage.id == message_id,
                AIChatSession.user_id == user_id,
                AIChatSession.is_deleted.is_(False),
            )
        )
        return self.db.scalars(statement.limit(1)).first()

    def next_sequence_no(self, session_id: int) -> int:
        statement = select(func.max(AIChatMessage.sequence_no)).where(
            AIChatMessage.session_id == session_id
        )
        return int(self.db.scalar(statement) or 0) + 1

    def recent_for_session(
        self,
        session_id: int,
        limit: int,
    ) -> list[AIChatMessage]:
        statement = (
            select(AIChatMessage)
            .where(AIChatMessage.session_id == session_id)
            .order_by(AIChatMessage.sequence_no.desc())
            .limit(limit)
        )
        return list(reversed(list(self.db.scalars(statement).all())))

    def page_for_session(
        self,
        session_id: int,
        *,
        before_sequence: int | None,
        page_size: int,
    ) -> tuple[list[AIChatMessage], bool]:
        statement = select(AIChatMessage).where(
            AIChatMessage.session_id == session_id
        )
        if before_sequence is not None:
            statement = statement.where(
                AIChatMessage.sequence_no < before_sequence
            )
        rows = list(
            self.db.scalars(
                statement.order_by(AIChatMessage.sequence_no.desc()).limit(
                    page_size + 1
                )
            ).all()
        )
        has_more = len(rows) > page_size
        items = list(reversed(rows[:page_size]))
        return items, has_more

    def get_by_idempotency(
        self,
        session_id: int,
        idempotency_key: str,
    ) -> AIChatMessage | None:
        statement = (
            select(AIChatMessage)
            .where(
                AIChatMessage.session_id == session_id,
                AIChatMessage.idempotency_key == idempotency_key,
            )
            .order_by(AIChatMessage.sequence_no.asc())
            .limit(1)
        )
        return self.db.scalars(statement).first()

    def latest_match(
        self,
        job_id: int,
        candidate_id: int,
    ) -> JobMatchResult | None:
        statement = (
            select(JobMatchResult)
            .where(
                JobMatchResult.job_id == job_id,
                JobMatchResult.candidate_id == candidate_id,
            )
            .order_by(JobMatchResult.id.desc())
            .limit(1)
        )
        return self.db.scalars(statement).first()

    def latest_resume(self, candidate_id: int) -> Resume | None:
        statement = (
            select(Resume)
            .where(Resume.candidate_id == candidate_id)
            .order_by(Resume.id.desc())
            .limit(1)
        )
        return self.db.scalars(statement).first()

    def related_questions(
        self,
        job_id: int,
        candidate_id: int | None,
        limit: int,
    ) -> list[InterviewQuestion]:
        statement = select(InterviewQuestion).where(
            InterviewQuestion.job_id == job_id
        )
        if candidate_id is None:
            statement = statement.where(
                InterviewQuestion.candidate_id.is_(None)
            )
        else:
            statement = statement.where(
                or_(
                    InterviewQuestion.candidate_id == candidate_id,
                    InterviewQuestion.candidate_id.is_(None),
                )
            )
        statement = statement.order_by(InterviewQuestion.id.desc()).limit(limit)
        return list(self.db.scalars(statement).all())

    def transition_assistant_status(
        self,
        message_id: int,
        allowed_statuses: set[str],
        values: dict[str, Any],
    ) -> AIChatMessage | None:
        statement = (
            update(AIChatMessage)
            .where(
                AIChatMessage.id == message_id,
                AIChatMessage.role == "ASSISTANT",
                AIChatMessage.status.in_(allowed_statuses),
            )
            .values(**values)
        )
        self.db.execute(statement)
        self.db.commit()
        self.db.expire_all()
        return self.get(message_id)

    def fail_incomplete_assistants(
        self,
        message: str,
        cutoff: datetime,
    ) -> int:
        statement = (
            update(AIChatMessage)
            .where(
                AIChatMessage.role == "ASSISTANT",
                AIChatMessage.status.in_(["PENDING", "STREAMING"]),
                AIChatMessage.created_at < cutoff,
            )
            .values(
                status="FAILED",
                error_message=message,
                updated_at=datetime.now(timezone.utc),
            )
        )
        result = self.db.execute(statement)
        self.db.commit()
        return int(result.rowcount or 0)


class AIExecutionLogDAO(BaseDAO[AIExecutionLog]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, AIExecutionLog)


class VectorDocumentDAO(BaseDAO[VectorDocument]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, VectorDocument)

    def get_by_hash(self, content_hash: str) -> VectorDocument | None:
        return self.first(content_hash=content_hash)


class MatchResultDAO(BaseDAO[JobMatchResult]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, JobMatchResult)

    def replace_for_job_candidates(self, job_id: int, candidate_ids: list[int]) -> None:
        if not candidate_ids:
            return
        self.db.query(JobMatchResult).filter(
            JobMatchResult.job_id == job_id,
            JobMatchResult.candidate_id.in_(candidate_ids),
        ).delete(synchronize_session=False)
        self.db.commit()

    def top_for_job(self, job_id: int, limit: int) -> list[JobMatchResult]:
        statement = (
            select(JobMatchResult)
            .where(JobMatchResult.job_id == job_id)
            .order_by(JobMatchResult.score.desc(), JobMatchResult.id.desc())
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())


class InterviewDAO(BaseDAO[InterviewSchedule]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, InterviewSchedule)

    def status_counts(self) -> dict[str, int]:
        statement = select(InterviewSchedule.status, func.count()).group_by(
            InterviewSchedule.status
        )
        return {status: int(count) for status, count in self.db.execute(statement).all()}


class InterviewParticipantDAO(BaseDAO[InterviewParticipant]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, InterviewParticipant)


class InterviewQuestionDAO(BaseDAO[InterviewQuestion]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, InterviewQuestion)

    def find_by_ids(self, ids: list[int]) -> list[InterviewQuestion]:
        if not ids:
            return []
        return list(
            self.db.scalars(select(InterviewQuestion).where(InterviewQuestion.id.in_(ids))).all()
        )

    def approve(self, ids: list[int], approver_id: int) -> int:
        questions = self.find_by_ids(ids)
        now = datetime.now()
        for question in questions:
            question.status = "APPROVED"
            question.approved_by = approver_id
            question.approved_at = now
        self.db.commit()
        return len(questions)


class OperationLogDAO(BaseDAO[OperationLog]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, OperationLog)

    def search(
        self,
        page: int,
        page_size: int,
        *,
        user_id: int | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[OperationLog], int]:
        statement = select(OperationLog)
        if user_id is not None:
            statement = statement.where(OperationLog.user_id == user_id)
        if action:
            statement = statement.where(OperationLog.action == action)
        if resource_type:
            statement = statement.where(OperationLog.resource_type == resource_type)
        if start_time:
            statement = statement.where(OperationLog.created_at >= start_time)
        if end_time:
            statement = statement.where(OperationLog.created_at <= end_time)
        count_statement = select(func.count()).select_from(statement.subquery())
        total = int(self.db.scalar(count_statement) or 0)
        rows = self.db.scalars(
            statement.order_by(OperationLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return list(rows), total


class DashboardDAO:
    def __init__(self, db: Session) -> None:
        self.db = db

    def summary(self) -> dict[str, dict[str, int]]:
        return {
            "jobs": JobDAO(self.db).status_counts(),
            "candidates": CandidateDAO(self.db).status_counts(),
            "applications": ApplicationDAO(self.db).stage_counts(),
            "interviews": InterviewDAO(self.db).status_counts(),
            "ai_tasks": AITaskDAO(self.db).status_counts(),
        }
