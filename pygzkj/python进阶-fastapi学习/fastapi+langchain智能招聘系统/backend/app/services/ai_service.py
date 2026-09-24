from __future__ import annotations

import hashlib
import json
import logging
import math
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.fallback import generate_questions_locally, parse_resume_locally, rule_match
from app.ai.prompts import (
    INTERVIEW_SYSTEM_PROMPT,
    MATCH_SYSTEM_PROMPT,
    RESUME_PARSE_SYSTEM_PROMPT,
    detect_prompt_injection,
)
from app.ai.provider import langchain_provider
from app.common.exceptions import AppError, NotFoundError
from app.config.database import SessionLocal
from app.config.redis import redis_manager
from app.config.settings import settings
from app.dao.repositories import (
    AIExecutionLogDAO,
    AITaskDAO,
    ApplicationDAO,
    CandidateDAO,
    JobDAO,
    MatchResultDAO,
    ResumeParseDAO,
    VectorDocumentDAO,
)
from app.schemas.ai import (
    AITaskResponse,
    GeneratedQuestion,
    MatchRequest,
    MatchResultResponse,
    ResumeParsedData,
)
from app.schemas.resumes import ParseRecordResponse
from app.services.helpers import model_dict

logger = logging.getLogger(__name__)


class LLMMatchOutput(BaseModel):
    score: float = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list, max_length=10)


class GeneratedQuestionList(BaseModel):
    questions: list[GeneratedQuestion] = Field(min_length=1, max_length=20)


class AIService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.tasks = AITaskDAO(db)
        self.logs = AIExecutionLogDAO(db)
        self.jobs = JobDAO(db)
        self.candidates = CandidateDAO(db)
        self.applications = ApplicationDAO(db)
        self.matches = MatchResultDAO(db)
        self.parse_records = ResumeParseDAO(db)
        self.vector_documents = VectorDocumentDAO(db)

    def prepare_resume_parse_task(self, resume_id: int, user_id: int) -> AITaskResponse:
        task = self._start_task(
            "RESUME_PARSE",
            {"resume_id": resume_id},
            user_id,
            status="PENDING",
        )
        return AITaskResponse.model_validate(task)

    def execute_resume_parse_task(
        self,
        task_no: str,
        text: str,
        *,
        resume_id: int,
        record_id: int,
        user_id: int,
    ) -> tuple[ParseRecordResponse, dict[str, Any], bool]:
        task = self.tasks.get_by_task_no(task_no)
        if not task:
            raise NotFoundError("AI 任务不存在")
        safety = detect_prompt_injection(text)
        self.tasks.update(
            task,
            {
                "status": "RUNNING",
                "started_at": datetime.now(timezone.utc),
                "input_payload": {
                    "resume_id": resume_id,
                    "prompt_safety": safety,
                },
            },
        )
        degraded = not langchain_provider.configured
        if langchain_provider.configured:
            try:
                parsed = langchain_provider.invoke_structured(
                    RESUME_PARSE_SYSTEM_PROMPT,
                    {"resume_text": text},
                    ResumeParsedData,
                )
            except Exception as exc:
                logger.warning(
                    "LangChain 简历解析失败，切换本地降级：%s",
                    settings.redact_secrets(exc),
                )
                parsed = parse_resume_locally(text)
                degraded = True
        else:
            parsed = parse_resume_locally(text)
        parsed_data = parsed.model_dump(mode="json")
        output = {"parsed_data": parsed_data, "prompt_safety": safety}
        record = self.parse_records.get(record_id)
        if not record:
            raise NotFoundError("简历解析记录不存在")
        record = self.parse_records.update(
            record,
            {
                "status": "PARSED",
                "parsed_data": parsed_data,
                "confidence": parsed.confidence,
            },
        )
        return ParseRecordResponse.model_validate(record), output, degraded

    def complete_task(
        self,
        task_no: str,
        output: dict[str, Any],
        degraded: bool,
        input_data: Any = None,
    ) -> None:
        task = self.tasks.get_by_task_no(task_no)
        if not task:
            raise NotFoundError("AI 任务不存在")
        safe_output = json.loads(json.dumps(output, ensure_ascii=False, default=str))
        self._write_execution_log(
            task, success=True, degraded=degraded, input_data=input_data, output_data=safe_output
        )
        self.tasks.update(
            task,
            {
                "status": "SUCCEEDED",
                "output_payload": safe_output,
                "degraded": degraded,
                "error_message": None,
                "finished_at": datetime.now(timezone.utc),
            },
        )

    def fail_task(self, task_no: str, error: str, input_data: Any = None) -> None:
        task = self.tasks.get_by_task_no(task_no)
        if not task or task.status in {"SUCCEEDED", "FAILED"}:
            return
        safe_error = settings.redact_secrets(error)[:2000]
        try:
            self._write_execution_log(
                task,
                success=False,
                degraded=True,
                input_data=input_data,
                output_data=None,
                error=safe_error,
            )
        except Exception:
            logger.exception("写入 AI 失败执行日志时出错：%s", task_no)
        self.tasks.update(
            task,
            {
                "status": "FAILED",
                "degraded": True,
                "error_message": safe_error,
                "finished_at": datetime.now(timezone.utc),
            },
        )

    def prepare_match_task(self, payload: MatchRequest, user_id: int) -> AITaskResponse:
        job = self.jobs.get(payload.job_id)
        if not job:
            raise NotFoundError("岗位不存在")
        candidates = self._resolve_candidates(payload.candidate_ids, payload.top_k)
        input_payload = {
            "job_id": payload.job_id,
            "candidate_ids": [item.id for item in candidates],
            "top_k": payload.top_k,
            "force_refresh": payload.force_refresh,
            "prompt_safety": detect_prompt_injection(
                {"job": model_dict(job), "candidates": [model_dict(item) for item in candidates]}
            ),
        }
        task = self._start_task("JOB_MATCH", input_payload, user_id, status="PENDING")
        return AITaskResponse.model_validate(task)

    def execute_match_task(
        self, task_no: str, payload: dict[str, Any], user_id: int
    ) -> dict[str, Any] | None:
        task = self.tasks.get_by_task_no(task_no)
        if not task:
            logger.error("后台匹配任务不存在：%s", task_no)
            return None
        if task.status == "SUCCEEDED":
            return None
        self.tasks.update(
            task,
            {"status": "RUNNING", "started_at": datetime.now(timezone.utc)},
        )
        degraded = not langchain_provider.configured
        job_data: dict[str, Any] = {}
        try:
            job = self.jobs.get(int(payload["job_id"]))
            if not job:
                raise NotFoundError("岗位不存在")
            candidates = self._resolve_candidates(
                payload.get("candidate_ids"), int(payload.get("top_k", 20))
            )
            job_data = model_dict(job)
            safety = payload.get("prompt_safety") or detect_prompt_injection(job_data)
            cache_key = self._match_cache_key(job.id, candidates)
            if not payload.get("force_refresh"):
                cached = redis_manager.get(cache_key)
                if cached:
                    result = json.loads(cached)
                    cached_items = result.get("items") or []
                    result_ids = [item.get("id") for item in cached_items]
                    if result_ids and all(
                        item_id is not None and self.matches.get(int(item_id))
                        for item_id in result_ids
                    ):
                        result["task_no"] = task.task_no
                        result["prompt_safety"] = safety
                        self.complete_task(
                            task.task_no,
                            result,
                            bool(result.get("degraded")),
                            job_data,
                        )
                        return result

            items: list[dict[str, Any]] = []
            for candidate in candidates:
                candidate_data = model_dict(candidate)
                item = self._match_candidate(
                    job_data, candidate_data, job.id, candidate.id, user_id, safety
                )
                if item["degraded"]:
                    degraded = True
                items.append(item)
            items.sort(key=lambda item: item["score"], reverse=True)
            result = {
                "task_no": task.task_no,
                "algorithm_version": settings.ai_algorithm_version,
                "prompt_version": settings.ai_prompt_version,
                "degraded": degraded,
                "prompt_safety": safety,
                "items": items,
            }
            redis_manager.set(
                cache_key,
                json.dumps(result, ensure_ascii=False, default=str),
                settings.ai_cache_ttl_seconds,
            )
            self.complete_task(task.task_no, result, degraded, job_data)
            return result
        except Exception as exc:
            self.tasks.rollback()
            self.fail_task(task.task_no, settings.redact_secrets(exc), job_data)
            logger.error(
                "后台人岗匹配失败，任务：%s，异常类型：%s",
                task_no,
                type(exc).__name__,
            )
            return None

    def latest_matches(self, job_id: int, limit: int = 20) -> list[dict[str, Any]]:
        return [model_dict(item) for item in self.matches.top_for_job(job_id, limit)]

    def get_match_result(self, result_id: int) -> MatchResultResponse:
        result = self.matches.get(result_id)
        if not result:
            raise NotFoundError("匹配结果不存在")
        return MatchResultResponse.model_validate(result)

    def get_task(self, task_no: str) -> AITaskResponse:
        task = self.tasks.get_by_task_no(task_no)
        if not task:
            raise NotFoundError("AI 任务不存在")
        return AITaskResponse.model_validate(task)

    def prepare_question_task(
        self,
        *,
        job_id: int,
        candidate_id: int | None,
        interview_id: int | None,
        count: int,
        categories: list[str],
        user_id: int,
    ) -> AITaskResponse:
        job = self.jobs.get(job_id)
        if not job:
            raise NotFoundError("岗位不存在")
        candidate = self.candidates.get(candidate_id) if candidate_id else None
        if candidate_id and not candidate:
            raise NotFoundError("候选人不存在")
        input_payload = {
            "job_id": job_id,
            "candidate_id": candidate_id,
            "interview_id": interview_id,
            "count": count,
            "categories": categories,
            "prompt_safety": detect_prompt_injection(
                {"job": model_dict(job), "candidate": model_dict(candidate) if candidate else None}
            ),
        }
        task = self._start_task(
            "INTERVIEW_QUESTION", input_payload, user_id, status="PENDING"
        )
        return AITaskResponse.model_validate(task)

    def execute_question_task(
        self, task_no: str, payload: dict[str, Any], user_id: int
    ) -> dict[str, Any] | None:
        task = self.tasks.get_by_task_no(task_no)
        if not task:
            logger.error("后台面试题任务不存在：%s", task_no)
            return None
        if task.status == "SUCCEEDED":
            return None
        self.tasks.update(
            task, {"status": "RUNNING", "started_at": datetime.now(timezone.utc)}
        )
        degraded = not langchain_provider.configured
        input_data: dict[str, Any] = payload
        try:
            job = self.jobs.get(int(payload["job_id"]))
            if not job:
                raise NotFoundError("岗位不存在")
            candidate = (
                self.candidates.get(int(payload["candidate_id"]))
                if payload.get("candidate_id")
                else None
            )
            if payload.get("candidate_id") and not candidate:
                raise NotFoundError("候选人不存在")
            job_data = model_dict(job)
            candidate_data = model_dict(candidate) if candidate else None
            safety = payload.get("prompt_safety") or detect_prompt_injection(
                {"job": job_data, "candidate": candidate_data}
            )
            if langchain_provider.configured:
                try:
                    generated = langchain_provider.invoke_structured(
                        INTERVIEW_SYSTEM_PROMPT,
                        {
                            "job": job_data,
                            "candidate": candidate_data,
                            "count": int(payload["count"]),
                            "categories": payload["categories"],
                        },
                        GeneratedQuestionList,
                    ).questions
                except Exception as exc:
                    logger.warning(
                        "LangChain 面试题生成失败，切换本地降级：%s",
                        settings.redact_secrets(exc),
                    )
                    generated = generate_questions_locally(
                        job_data,
                        candidate_data,
                        int(payload["count"]),
                        payload["categories"],
                    )
                    degraded = True
            else:
                generated = generate_questions_locally(
                    job_data,
                    candidate_data,
                    int(payload["count"]),
                    payload["categories"],
                )
            result = {
                "task_no": task.task_no,
                "degraded": degraded,
                "prompt_safety": safety,
                "questions": [
                    item.model_dump(mode="json") for item in generated[: int(payload["count"])]
                ],
            }
            return result
        except Exception as exc:
            self.tasks.rollback()
            self.fail_task(task.task_no, settings.redact_secrets(exc), input_data)
            logger.error(
                "后台面试题生成失败，任务：%s，异常类型：%s",
                task_no,
                type(exc).__name__,
            )
            return None

    def _match_candidate(
        self,
        job_data: dict[str, Any],
        candidate_data: dict[str, Any],
        job_id: int,
        candidate_id: int,
        user_id: int,
        safety: dict[str, Any],
    ) -> dict[str, Any]:
        rule_score, reasons = rule_match(job_data, candidate_data)
        score = rule_score
        vector_score = None
        llm_score = None
        detail: dict[str, Any] = {"prompt_safety": safety}
        degraded = not langchain_provider.configured
        if langchain_provider.embedding_configured:
            try:
                job_text = self._content_text(job_data)
                candidate_text = self._content_text(candidate_data)
                job_vector, candidate_vector = langchain_provider.embed_texts(
                    [job_text, candidate_text]
                )
                vector_score = round(
                    self._cosine_similarity(job_vector, candidate_vector) * 100, 2
                )
                score = self._bounded_adjustment(rule_score, vector_score, 0.15, 8.0)
                self._store_vector("job", job_id, job_text, job_vector)
                self._store_vector("candidate", candidate_id, candidate_text, candidate_vector)
            except Exception as exc:
                degraded = True
                detail["vector_fallback_reason"] = settings.redact_secrets(exc)[:300]
        if langchain_provider.configured:
            try:
                llm_result = langchain_provider.invoke_structured(
                    MATCH_SYSTEM_PROMPT,
                    {"job": job_data, "candidate": candidate_data},
                    LLMMatchOutput,
                )
                llm_score = llm_result.score
                score = self._bounded_adjustment(score, llm_score, 0.15, 8.0)
                reasons = list(dict.fromkeys(reasons + llm_result.reasons))[:10]
            except Exception as exc:
                degraded = True
                detail["llm_fallback_reason"] = settings.redact_secrets(exc)[:300]
        application = self.applications.get_by_job_candidate(job_id, candidate_id)
        record = self.matches.create(
            {
                "job_id": job_id,
                "candidate_id": candidate_id,
                "application_id": application.id if application else None,
                "score": score,
                "rule_score": rule_score,
                "vector_score": vector_score,
                "llm_score": llm_score,
                "level": self._level(score),
                "reasons": reasons,
                "detail": detail,
                "algorithm_version": settings.ai_algorithm_version,
                "prompt_version": settings.ai_prompt_version,
                "degraded": degraded,
                "created_by": user_id,
            }
        )
        return model_dict(record)

    def _resolve_candidates(self, candidate_ids: list[int] | None, top_k: int):
        if not candidate_ids:
            return self.candidates.list_all(limit=top_k, status="ACTIVE")
        found = {item.id: item for item in self.candidates.find_by_ids(candidate_ids)}
        missing = sorted(set(candidate_ids) - set(found))
        if missing:
            raise AppError(
                "部分候选人不存在",
                code=40401,
                status_code=404,
                data={"missing_candidate_ids": missing},
            )
        return [found[item_id] for item_id in candidate_ids if item_id in found]

    def _start_task(
        self,
        task_type: str,
        payload: dict[str, Any],
        user_id: int,
        *,
        status: str,
    ):
        started_at = datetime.now(timezone.utc) if status == "RUNNING" else None
        return self.tasks.create(
            {
                "task_no": f"AI-{datetime.now(timezone.utc):%Y%m%d%H%M%S}-{uuid4().hex[:10].upper()}",
                "task_type": task_type,
                "status": status,
                "provider": langchain_provider.provider_name,
                "model_name": langchain_provider.model_name,
                "input_payload": payload,
                "started_at": started_at,
                "created_by": user_id,
            }
        )

    def _write_execution_log(
        self,
        task,
        *,
        success: bool,
        degraded: bool,
        input_data: Any,
        output_data: Any,
        error: str | None = None,
    ) -> None:
        self.logs.create(
            {
                "task_id": task.id,
                "provider": langchain_provider.provider_name,
                "model_name": langchain_provider.model_name,
                "prompt_version": settings.ai_prompt_version,
                "algorithm_version": settings.ai_algorithm_version,
                "success": success,
                "degraded": degraded,
                "latency_ms": self._task_latency_ms(task),
                "error_message": error,
                "input_digest": self._digest(input_data),
                "output_digest": self._digest(output_data),
            }
        )

    @staticmethod
    def _task_latency_ms(task) -> float:
        if not task.started_at:
            return 0.0
        started_at = task.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        return round(
            max(
                0.0,
                (datetime.now(timezone.utc) - started_at).total_seconds() * 1000,
            ),
            2,
        )

    @staticmethod
    def _digest(value: Any) -> str:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _match_cache_key(self, job_id: int, candidates: list) -> str:
        ids = sorted(item.id for item in candidates)
        digest = self._digest(ids)[:24]
        return (
            f"recruit:ai:match:{job_id}:"
            f"{settings.ai_algorithm_version}:{settings.ai_prompt_version}:{digest}"
        )

    def _store_vector(
        self, source_type: str, source_id: int, content: str, embedding: list[float]
    ) -> None:
        digest = hashlib.sha256(
            f"{source_type}:{source_id}:{settings.ai_algorithm_version}:{content}".encode("utf-8")
        ).hexdigest()
        existing = self.vector_documents.get_by_hash(digest)
        if existing:
            return
        self.vector_documents.create(
            {
                "source_type": source_type,
                "source_id": source_id,
                "content": content[:50000],
                "embedding": embedding,
                "extra_data": {"model": settings.embedding_model},
                "algorithm_version": settings.ai_algorithm_version,
                "content_hash": digest,
            }
        )

    @staticmethod
    def _content_text(data: dict[str, Any]) -> str:
        parts = [
            str(data.get("title") or data.get("name") or ""),
            str(data.get("requirements") or data.get("summary") or ""),
            " ".join(data.get("skills") or []),
            str(data.get("current_title") or ""),
        ]
        return "\n".join(part for part in parts if part)

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if not left_norm or not right_norm:
            return 0.0
        return max(0.0, min(1.0, numerator / (left_norm * right_norm)))

    @staticmethod
    def _bounded_adjustment(base: float, signal: float, factor: float, limit: float) -> float:
        adjustment = max(-limit, min(limit, (signal - base) * factor))
        return round(max(0.0, min(100.0, base + adjustment)), 2)

    @staticmethod
    def _level(score: float) -> str:
        if score >= 85:
            return "EXCELLENT"
        if score >= 70:
            return "HIGH"
        if score >= 55:
            return "MEDIUM"
        return "LOW"


def run_match_task(task_no: str, payload: dict[str, Any], user_id: int) -> None:
    try:
        with SessionLocal() as db:
            AIService(db).execute_match_task(task_no, payload, user_id)
    except Exception:
        logger.exception("AI 匹配后台任务异常：%s", task_no)


def run_question_task(task_no: str, payload: dict[str, Any], user_id: int) -> None:
    try:
        from app.services.interview_service import persist_question_task_result

        with SessionLocal() as db:
            ai_service = AIService(db)
            try:
                result = ai_service.execute_question_task(task_no, payload, user_id)
                if not result:
                    return
                saved = persist_question_task_result(db, payload, result)
                result["questions"] = saved
                result["question_ids"] = [item["id"] for item in saved]
                ai_service.complete_task(
                    task_no,
                    result,
                    bool(result.get("degraded")),
                    payload,
                )
            except Exception as exc:
                db.rollback()
                ai_service.fail_task(task_no, str(exc), payload)
                raise
    except Exception:
        logger.exception("AI 面试题后台任务异常：%s", task_no)
