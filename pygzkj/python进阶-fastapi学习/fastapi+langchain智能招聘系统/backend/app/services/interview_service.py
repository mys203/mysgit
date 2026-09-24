from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.common.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.dao.repositories import (
    ApplicationDAO,
    CandidateDAO,
    InterviewDAO,
    InterviewParticipantDAO,
    InterviewQuestionDAO,
    JobDAO,
)
from app.schemas.ai import InterviewQuestionGenerateRequest
from app.schemas.interviews import (
    FeedbackRequest,
    InterviewCreate,
    InterviewQuestionUpdate,
    InterviewUpdate,
    ParticipantCreate,
)
from app.security.dependencies import UserPrincipal
from app.services.helpers import model_dict, record_operation


class InterviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.interviews = InterviewDAO(db)
        self.participants = InterviewParticipantDAO(db)
        self.questions = InterviewQuestionDAO(db)
        self.jobs = JobDAO(db)
        self.candidates = CandidateDAO(db)
        self.applications = ApplicationDAO(db)

    def list_interviews(self, page: int, page_size: int, status: str | None):
        filters = {"status": status} if status else {}
        rows, total = self.interviews.paginate(page, page_size, filters=filters)
        return [model_dict(item) for item in rows], total

    def get_interview(self, interview_id: int) -> dict:
        interview = self.interviews.get(interview_id)
        if not interview:
            raise NotFoundError("面试不存在")
        return model_dict(interview)

    def create_interview(self, payload: InterviewCreate, user: UserPrincipal) -> dict:
        if not self.jobs.get(payload.job_id):
            raise NotFoundError("岗位不存在")
        if not self.candidates.get(payload.candidate_id):
            raise NotFoundError("候选人不存在")
        if payload.application_id and not self.applications.get(payload.application_id):
            raise NotFoundError("应聘记录不存在")
        interview = self.interviews.create({**payload.model_dump(), "created_by": user.id})
        if payload.interviewer_id:
            self.participants.create(
                {
                    "interview_id": interview.id,
                    "user_id": payload.interviewer_id,
                    "participant_role": "INTERVIEWER",
                }
            )
        record_operation(
            self.db,
            user,
            method="POST",
            path="/api/v1/interviews",
            action="CREATE",
            resource_type="interview",
            resource_id=interview.id,
        )
        return model_dict(interview)

    def update_interview(
        self, interview_id: int, payload: InterviewUpdate, user: UserPrincipal
    ) -> dict:
        interview = self.interviews.get(interview_id)
        if not interview:
            raise NotFoundError("面试不存在")
        if "interviewer_id" in payload.model_fields_set:
            self._sync_default_interviewer(
                interview_id,
                interview.interviewer_id,
                payload.interviewer_id,
            )
        result = model_dict(
            self.interviews.update(interview, payload.model_dump(exclude_unset=True))
        )
        record_operation(
            self.db,
            user,
            method="PATCH",
            path=f"/api/v1/interviews/{interview_id}",
            action="UPDATE",
            resource_type="interview",
            resource_id=interview_id,
        )
        return result

    def _sync_default_interviewer(
        self, interview_id: int, old_user_id: int | None, new_user_id: int | None
    ) -> None:
        if old_user_id == new_user_id:
            return
        if old_user_id:
            old_participant = self.participants.first(
                interview_id=interview_id,
                user_id=old_user_id,
            )
            if (
                old_participant
                and old_participant.status in {"INVITED", "CONFIRMED"}
                and old_participant.feedback is None
                and old_participant.score is None
            ):
                self.participants.delete(old_participant)
        if new_user_id:
            participant = self.participants.first(
                interview_id=interview_id,
                user_id=new_user_id,
            )
            if participant:
                updates = {"participant_role": "INTERVIEWER"}
                if participant.status == "DECLINED":
                    updates.update({"status": "INVITED", "feedback": None, "score": None})
                self.participants.update(participant, updates)
            else:
                self.participants.create(
                    {
                        "interview_id": interview_id,
                        "user_id": new_user_id,
                        "participant_role": "INTERVIEWER",
                        "status": "INVITED",
                    }
                )

    def cancel(self, interview_id: int, reason: str, user: UserPrincipal) -> dict:
        interview = self.interviews.get(interview_id)
        if not interview:
            raise NotFoundError("面试不存在")
        result = model_dict(
            self.interviews.update(
                interview,
                {"status": "CANCELLED", "updated_at": datetime.now(timezone.utc)},
            )
        )
        record_operation(
            self.db,
            user,
            method="POST",
            path=f"/api/v1/interviews/{interview_id}/cancel",
            action="CANCEL",
            resource_type="interview",
            resource_id=interview_id,
            detail={"reason": reason},
        )
        return result

    def add_participant(
        self, interview_id: int, payload: ParticipantCreate, user: UserPrincipal
    ) -> dict:
        if not self.interviews.get(interview_id):
            raise NotFoundError("面试不存在")
        participant = self.participants.create(
            {"interview_id": interview_id, **payload.model_dump()}
        )
        record_operation(
            self.db,
            user,
            method="POST",
            path=f"/api/v1/interviews/{interview_id}/participants",
            action="ADD_PARTICIPANT",
            resource_type="interview_participant",
            resource_id=participant.id,
        )
        return model_dict(participant)

    def feedback(self, interview_id: int, payload: FeedbackRequest, user: UserPrincipal) -> dict:
        if not self.interviews.get(interview_id):
            raise NotFoundError("面试不存在")
        participant = self.participants.first(interview_id=interview_id, user_id=user.id)
        if not participant:
            raise PermissionDeniedError("当前用户不是该面试的参与人")
        if participant.status not in {"INVITED", "CONFIRMED"}:
            raise ConflictError("当前参与状态不允许提交反馈")
        result = model_dict(self.participants.update(participant, payload.model_dump()))
        record_operation(
            self.db,
            user,
            method="POST",
            path=f"/api/v1/interviews/{interview_id}/feedback",
            action="SUBMIT_FEEDBACK",
            resource_type="interview_participant",
            resource_id=participant.id,
            detail={"score": payload.score},
        )
        return result

    def list_questions(self, interview_id: int):
        if not self.interviews.get(interview_id):
            raise NotFoundError("面试不存在")
        return [
            model_dict(item)
            for item in self.questions.list_all(limit=200, interview_id=interview_id)
        ]

    def list_global_questions(
        self,
        page: int,
        page_size: int,
        status: str | None = None,
        category: str | None = None,
    ):
        filters = {}
        if status:
            filters["status"] = status
        if category:
            filters["category"] = category
        rows, total = self.questions.paginate(page, page_size, filters=filters)
        return [model_dict(item) for item in rows], total

    def prepare_generation(
        self, payload: InterviewQuestionGenerateRequest, user: UserPrincipal
    ):
        if payload.interview_id and not self.interviews.get(payload.interview_id):
            raise NotFoundError("面试不存在")
        from app.services.ai_service import AIService

        return AIService(self.db).prepare_question_task(
            job_id=payload.job_id,
            candidate_id=payload.candidate_id,
            interview_id=payload.interview_id,
            count=payload.count,
            categories=payload.categories,
            user_id=user.id,
        )

    def update_question(
        self, question_id: int, payload: InterviewQuestionUpdate, user: UserPrincipal
    ) -> dict:
        question = self.questions.get(question_id)
        if not question:
            raise NotFoundError("面试题不存在")
        result = model_dict(
            self.questions.update(question, payload.model_dump(exclude_unset=True))
        )
        record_operation(
            self.db,
            user,
            method="PATCH",
            path=f"/api/v1/interview-questions/{question_id}",
            action="UPDATE",
            resource_type="interview_question",
            resource_id=question_id,
        )
        return result

    def approve(self, question_ids: list[int], user: UserPrincipal) -> dict:
        count = self.questions.approve(question_ids, user.id)
        if count != len(question_ids):
            raise NotFoundError("部分面试题不存在")
        record_operation(
            self.db,
            user,
            method="POST",
            path="/api/v1/interview-questions/approve",
            action="APPROVE",
            resource_type="interview_question",
            detail={"question_ids": question_ids},
        )
        return {"approved_count": count, "question_ids": question_ids}


def persist_question_task_result(
    db: Session, payload: dict, result: dict
) -> list[dict]:
    service = InterviewService(db)
    saved = []
    for item in result["questions"]:
        question = service.questions.create(
            {
                "interview_id": payload.get("interview_id"),
                "job_id": int(payload["job_id"]),
                "candidate_id": payload.get("candidate_id"),
                "question": item["question"],
                "category": item["category"],
                "reference_answer": item.get("reference_answer"),
                "score_weight": item.get("score_weight", 1.0),
                "status": "DRAFT",
                "generated_by": (
                    "LOCAL_FALLBACK" if result.get("degraded") else "LANGCHAIN"
                ),
            }
        )
        saved.append(model_dict(question))
    return saved
