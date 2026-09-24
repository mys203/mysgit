from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import time
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import Request
from sqlalchemy.orm import Session

from app.ai.fallback import (
    answer_chat_locally,
    chat_injection_response,
)
from app.ai.prompts import (
    CHAT_SYSTEM_PROMPT,
    detect_prompt_injection,
)
from app.ai.provider import LangChainProvider, langchain_provider
from app.common.exceptions import (
    AIUnavailableError,
    AppError,
    ConflictError,
    NotFoundError,
)
from app.config.database import SessionLocal
from app.config.redis import redis_manager
from app.config.settings import settings
from app.dao.repositories import (
    AIChatMessageDAO,
    AIChatSessionDAO,
    CandidateDAO,
    JobDAO,
    ResumeParseDAO,
)
from app.schemas.ai_chat import (
    ChatContext,
    ChatContextUpdate,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatMessageSendResponse,
    ChatMessageStopResponse,
    ChatSessionCreate,
    ChatSessionRename,
    ChatSessionResponse,
)

logger = logging.getLogger(__name__)

_CITATION_GROUP = re.compile(r"\[([^\]]*S\d+[^\]]*)\]", flags=re.IGNORECASE)
_CITATION_INDEX = re.compile(r"S(\d+)", flags=re.IGNORECASE)
_IDEMPOTENCY_TTL_SECONDS = 86400
_STOP_FLAG_MIN_TTL_SECONDS = 600
_SEQUENCE_LOCK_TTL_SECONDS = 15
_SEQUENCE_LOCK_WAIT_SECONDS = 8.0
_TERMINAL_MESSAGE_STATUSES = {
    "COMPLETED",
    "FAILED",
    "STOPPED",
    "CANCELLED",
}


@dataclass(slots=True)
class RetrievedContext:
    snapshot: dict[str, Any]
    sources: list[dict[str, Any]]
    has_business_data: bool


@dataclass(slots=True)
class ChatTurn:
    session_id: int
    session_no: str
    user_id: int
    user_message_id: int
    assistant_id: int
    content: str
    history: list[dict[str, str]]
    context_snapshot: dict[str, Any]
    sources: list[dict[str, Any]]
    prompt_safety: dict[str, Any]
    provider: str
    model_name: str | None
    idempotency_key: str | None = None
    replay: bool = False
    existing_status: str | None = None
    existing_content: str = ""
    existing_citations: list[dict[str, Any]] = field(default_factory=list)
    existing_degraded: bool = False
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AIChatService:
    def __init__(
        self,
        db: Session,
        provider: LangChainProvider | None = None,
    ) -> None:
        self.db = db
        self.provider = provider or langchain_provider
        self.sessions = AIChatSessionDAO(db)
        self.messages = AIChatMessageDAO(db)
        self.jobs = JobDAO(db)
        self.candidates = CandidateDAO(db)
        self.parse_records = ResumeParseDAO(db)

    def create_session(
        self,
        payload: ChatSessionCreate,
        user_id: int,
    ) -> ChatSessionResponse:
        context = payload.context
        job, candidate, resume = self._validate_context(
            context.job_id,
            context.candidate_id,
        )
        session = self.sessions.create(
            {
                "session_no": self._new_no("CHAT"),
                "user_id": user_id,
                "title": payload.title or "新对话",
                "job_id": job.id if job else None,
                "candidate_id": candidate.id if candidate else None,
                "resume_id": resume.id if resume else None,
                "message_count": 0,
            }
        )
        self._bump_cache_version(user_id)
        return ChatSessionResponse.model_validate(session)

    def list_sessions(
        self,
        user_id: int,
        page: int,
        page_size: int,
        keyword: str | None = None,
    ) -> dict[str, Any]:
        cache_key = self._session_list_cache_key(
            user_id,
            page,
            page_size,
            keyword,
        )
        cached = redis_manager.get(cache_key)
        if cached:
            return json.loads(cached)
        items, total = self.sessions.paginate_owned(
            user_id,
            page,
            page_size,
            keyword,
        )
        result = {
            "items": [
                ChatSessionResponse.model_validate(item).model_dump(mode="json")
                for item in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if page_size else 0,
        }
        redis_manager.set(
            cache_key,
            json.dumps(result, ensure_ascii=False),
            settings.cache_ttl_seconds,
        )
        return result

    def get_session(
        self,
        session_id: int,
        user_id: int,
    ) -> ChatSessionResponse:
        cache_key = self._session_detail_cache_key(session_id, user_id)
        cached = redis_manager.get(cache_key)
        if cached:
            return ChatSessionResponse.model_validate_json(cached)
        session = self._require_session(session_id, user_id)
        response = ChatSessionResponse.model_validate(session)
        redis_manager.set(
            cache_key,
            response.model_dump_json(),
            settings.cache_ttl_seconds,
        )
        return response

    def rename_session(
        self,
        session_id: int,
        payload: ChatSessionRename,
        user_id: int,
    ) -> ChatSessionResponse:
        session = self._require_session(session_id, user_id)
        updated = self.sessions.update(session, {"title": payload.title})
        self._bump_cache_version(user_id)
        return ChatSessionResponse.model_validate(updated)

    def update_context(
        self,
        session_id: int,
        payload: ChatContextUpdate,
        user_id: int,
    ) -> ChatSessionResponse:
        session = self._require_session(session_id, user_id)
        provided = payload.model_fields_set
        job_id = payload.job_id if "job_id" in provided else session.job_id
        candidate_id = (
            payload.candidate_id
            if "candidate_id" in provided
            else session.candidate_id
        )
        job, candidate, resume = self._validate_context(job_id, candidate_id)
        updated = self.sessions.update(
            session,
            {
                "job_id": job.id if job else None,
                "candidate_id": candidate.id if candidate else None,
                "resume_id": resume.id if resume else None,
            },
        )
        self._bump_cache_version(user_id)
        return ChatSessionResponse.model_validate(updated)

    def delete_session(self, session_id: int, user_id: int) -> dict[str, Any]:
        session = self._require_session(session_id, user_id)
        deleted = self.sessions.soft_delete(session)
        self._bump_cache_version(user_id)
        return {
            "id": deleted.id,
            "session_no": deleted.session_no,
            "is_deleted": True,
        }

    def list_messages(
        self,
        session_id: int,
        user_id: int,
        *,
        before_sequence: int | None,
        page_size: int,
    ) -> dict[str, Any]:
        self._require_session(session_id, user_id)
        items, has_more = self.messages.page_for_session(
            session_id,
            before_sequence=before_sequence,
            page_size=page_size,
        )
        return {
            "items": [
                ChatMessageResponse.model_validate(item).model_dump(mode="json")
                for item in items
            ],
            "has_more": has_more,
            "next_before_sequence": (
                items[0].sequence_no if has_more and items else None
            ),
        }

    def prepare_message(
        self,
        session_id: int,
        payload: ChatMessageCreate,
        user_id: int,
        *,
        idempotency_key: str | None = None,
    ) -> ChatTurn:
        session = self._require_session(session_id, user_id)
        normalized_key = self._normalize_idempotency_key(idempotency_key)
        if normalized_key:
            existing = self._get_idempotent_turn(
                session_id,
                user_id,
                normalized_key,
            )
            if existing:
                return existing

        context = self._merge_context(session, payload.context)
        retrieved = self._retrieve_context(
            context.job_id,
            context.candidate_id,
        )
        retrieved.snapshot["session_no"] = session.session_no
        prompt_safety = detect_prompt_injection(
            {
                "user_content": payload.content,
                "business_data": retrieved.snapshot,
                "sources": retrieved.sources,
            }
        )
        marker_key = (
            self._idempotency_key(user_id, normalized_key)
            if normalized_key
            else None
        )
        sequence_lock_token: str | None = None
        try:
            if normalized_key:
                acquired = redis_manager.set_nx(
                    marker_key,
                    json.dumps(
                        {"state": "processing"},
                        ensure_ascii=False,
                    ),
                    _IDEMPOTENCY_TTL_SECONDS,
                )
                if not acquired:
                    existing = self._get_idempotent_turn(
                        session_id,
                        user_id,
                        normalized_key,
                    )
                    if existing:
                        return existing
                    raise self._idempotency_conflict()
            sequence_lock_token = self._acquire_sequence_lock(session.id)
            next_sequence = self.messages.next_sequence_no(session.id)
            now = datetime.now(timezone.utc)
            user_message = self.messages.create(
                {
                    "message_no": self._new_no("MSG"),
                    "session_id": session.id,
                    "user_id": user_id,
                    "role": "USER",
                    "status": "COMPLETED",
                    "sequence_no": next_sequence,
                    "content": payload.content,
                    "citations": [],
                    "context_snapshot": retrieved.snapshot,
                    "provider": "user",
                    "model_name": None,
                    "idempotency_key": normalized_key,
                }
            )
            assistant = self.messages.create(
                {
                    "message_no": self._new_no("MSG"),
                    "session_id": session.id,
                    "user_id": user_id,
                    "role": "ASSISTANT",
                    "status": "PENDING",
                    "sequence_no": next_sequence + 1,
                    "content": "",
                    "citations": [],
                    "context_snapshot": retrieved.snapshot,
                    "provider": self.provider.provider_name,
                    "model_name": self.provider.model_name,
                    "idempotency_key": normalized_key,
                }
            )
            self.sessions.update(
                session,
                {
                    "message_count": session.message_count + 2,
                    "last_message_preview": payload.content[:500],
                    "last_message_at": now,
                },
            )
            if normalized_key:
                redis_manager.set(
                    marker_key,
                    json.dumps(
                        {
                            "state": "processing",
                            "session_id": session.id,
                            "user_message_id": user_message.id,
                            "assistant_id": assistant.id,
                        },
                        ensure_ascii=False,
                    ),
                    _IDEMPOTENCY_TTL_SECONDS,
                )
        except Exception:
            if marker_key:
                redis_manager.delete(marker_key)
            self.db.rollback()
            raise
        finally:
            if sequence_lock_token:
                self._release_sequence_lock(
                    session.id,
                    sequence_lock_token,
                )
        self._bump_cache_version(user_id)
        history = self._history_for_prompt(
            session.id,
            exclude_message_id=user_message.id,
        )
        return ChatTurn(
            session_id=session.id,
            session_no=session.session_no,
            user_id=user_id,
            user_message_id=user_message.id,
            assistant_id=assistant.id,
            content=payload.content,
            history=history,
            context_snapshot=retrieved.snapshot,
            sources=retrieved.sources,
            prompt_safety=prompt_safety,
            provider=assistant.provider,
            model_name=assistant.model_name,
            idempotency_key=normalized_key,
            started_at=now,
        )

    def complete_turn(self, turn: ChatTurn) -> ChatMessageSendResponse:
        if turn.replay:
            return self._existing_turn_response(turn)
        assistant = self.messages.get_owned(turn.assistant_id, turn.user_id)
        if not assistant:
            raise NotFoundError("助手消息不存在")
        try:
            if turn.prompt_safety.get("suspicious"):
                answer = chat_injection_response()
                degraded = True
            elif not self.provider.configured:
                answer = answer_chat_locally(
                    turn.content,
                    turn.sources,
                    no_context_message=not bool(turn.sources),
                )
                degraded = True
            else:
                started = time.perf_counter()
                answer = self.provider.invoke_text(
                    CHAT_SYSTEM_PROMPT,
                    self._provider_payload(turn),
                    turn.history,
                )
                degraded = False
            cleaned, citations = self._validate_citations(
                answer,
                turn.sources,
            )
            if not cleaned.strip():
                raise RuntimeError("模型返回了空回答")
            latency_ms = self._elapsed_ms(turn.started_at)
            assistant = self._save_assistant(
                assistant,
                content=cleaned,
                status="COMPLETED",
                citations=citations,
                latency_ms=latency_ms,
                error_message=None,
            )
            self._update_session_after_assistant(
                turn.session_id,
                assistant.content,
            )
            self._mark_idempotency_terminal(turn, assistant.status)
            self._bump_cache_version(turn.user_id)
            user = self.messages.get_owned(turn.user_message_id, turn.user_id)
            assistant = self.messages.get_owned(turn.assistant_id, turn.user_id)
            if not user or not assistant:
                raise NotFoundError("聊天消息不存在")
            return ChatMessageSendResponse(
                user_message=ChatMessageResponse.model_validate(user),
                assistant_message=ChatMessageResponse.model_validate(assistant),
                degraded=degraded,
            )
        except Exception as exc:
            self.db.rollback()
            safe_error = f"模型调用失败（{type(exc).__name__}）"
            assistant = self._save_assistant(
                assistant,
                content=assistant.content,
                status="FAILED",
                citations=assistant.citations or [],
                latency_ms=self._elapsed_ms(turn.started_at),
                error_message=safe_error or "AI 回答生成失败",
            )
            self._mark_idempotency_terminal(turn, assistant.status)
            self._bump_cache_version(turn.user_id)
            logger.warning(
                "AI 招聘问答生成失败，会话：%s，异常类型：%s",
                turn.session_id,
                type(exc).__name__,
            )
            raise AIUnavailableError("AI 回答生成失败，可稍后重试") from exc

    async def stream_events(
        self,
        turn: ChatTurn,
        request: Request,
    ) -> AsyncIterator[str]:
        with SessionLocal() as stream_db:
            stream_service = AIChatService(stream_db, self.provider)
            async for event in stream_service._stream_events(turn, request):
                yield event

    async def _stream_events(
        self,
        turn: ChatTurn,
        request: Request,
    ) -> AsyncIterator[str]:
        assistant = self.messages.get_owned(turn.assistant_id, turn.user_id)
        if not assistant:
            yield self._sse(
                "error",
                {"code": 40400, "message": "助手消息不存在"},
            )
            return
        if turn.replay:
            async for event in self._replay_events(turn):
                yield event
            return

        yield self._sse(
            "meta",
            {
                "session_id": turn.session_id,
                "session_no": turn.session_no,
                "user_message_id": turn.user_message_id,
                "assistant_id": turn.assistant_id,
                "provider": turn.provider,
                "model": turn.model_name,
            },
        )
        yield self._sse(
            "progress",
            {
                "stage": "context",
                "message": (
                    "已加载关联业务资料"
                    if turn.sources
                    else "当前没有关联业务资料"
                ),
                "source_count": len(turn.sources),
            },
        )

        buffer = ""
        emitted_citations: set[int] = set()
        iterator: AsyncIterator[str] | None = None
        terminal = False
        stop_requested = False
        disconnected = False
        try:
            if turn.prompt_safety.get("suspicious"):
                answer = chat_injection_response()
                for chunk in self._chunk_text(answer):
                    buffer += chunk
                    yield self._sse("delta", {"content": chunk})
                cleaned, citations = answer, []
                degraded = True
            elif not self.provider.configured:
                answer = answer_chat_locally(
                    turn.content,
                    turn.sources,
                    no_context_message=not bool(turn.sources),
                )
                for chunk in self._chunk_text(answer):
                    buffer += chunk
                    yield self._sse("delta", {"content": chunk})
                cleaned, citations = self._validate_citations(answer, turn.sources)
                degraded = True
            else:
                iterator = self.provider.astream_text(
                    CHAT_SYSTEM_PROMPT,
                    self._provider_payload(turn),
                    turn.history,
                ).__aiter__()
                while True:
                    if await request.is_disconnected():
                        disconnected = True
                        break
                    if self._stop_requested(turn.assistant_id):
                        stop_requested = True
                        break
                    try:
                        text = await asyncio.wait_for(
                            iterator.__anext__(),
                            timeout=settings.llm_timeout_seconds,
                        )
                    except StopAsyncIteration:
                        break
                    text = str(text)
                    if not text:
                        continue
                    buffer += text
                    yield self._sse("delta", {"content": text})
                    for _source_index, citation in self._newly_cited_sources(
                        buffer,
                        turn.sources,
                        emitted_citations,
                    ):
                        yield self._sse("citation", citation)
                if disconnected:
                    self._mark_partial(
                        turn,
                        buffer,
                        status="CANCELLED",
                        error_message="客户端已断开连接",
                    )
                    terminal = True
                    return
                if stop_requested:
                    self._mark_partial(
                        turn,
                        buffer,
                        status="STOPPED",
                        error_message="用户已停止生成",
                    )
                    done = self._message_event_data(
                        turn.assistant_id,
                        turn.user_id,
                    )
                    terminal = True
                    yield self._sse("done", done)
                    return
                cleaned, citations = self._validate_citations(
                    buffer,
                    turn.sources,
                )
                degraded = False
            if not cleaned.strip():
                raise RuntimeError("模型返回了空回答")
            for citation in self._citations_for_events(citations, turn.sources):
                if citation["source_index"] in emitted_citations:
                    continue
                citation.pop("source_index", None)
                yield self._sse("citation", citation)
            assistant = self._save_assistant(
                assistant,
                content=cleaned,
                status="COMPLETED",
                citations=citations,
                latency_ms=self._elapsed_ms(turn.started_at),
                error_message=None,
            )
            if assistant.status == "STOPPED":
                assistant = self._save_assistant(
                    assistant,
                    content=cleaned,
                    status="STOPPED",
                    citations=citations,
                    latency_ms=self._elapsed_ms(turn.started_at),
                    error_message="用户已停止生成",
                )
            final_status = assistant.status
            self._update_session_after_assistant(
                turn.session_id,
                assistant.content or cleaned,
            )
            self._mark_idempotency_terminal(turn, final_status)
            self._bump_cache_version(turn.user_id)
            terminal = True
            done = self._message_event_data(
                turn.assistant_id,
                turn.user_id,
            )
            done["degraded"] = degraded or final_status != "COMPLETED"
            done["citations"] = citations
            yield self._sse("done", done)
        except asyncio.CancelledError:
            self._mark_partial(
                turn,
                buffer,
                status="CANCELLED",
                error_message="客户端已断开连接",
            )
            raise
        except Exception as exc:
            safe_error = f"模型调用失败（{type(exc).__name__}）"
            if not terminal:
                self._mark_partial(
                    turn,
                    buffer,
                    status="FAILED",
                    error_message=safe_error or "AI 回答生成失败",
                )
            final_status = (
                self._message_event_data(
                    turn.assistant_id,
                    turn.user_id,
                ).get("status")
                or "FAILED"
            )
            logger.warning(
                "AI 招聘问答流式生成失败，会话：%s，异常类型：%s",
                turn.session_id,
                type(exc).__name__,
            )
            yield self._sse(
                "error",
                {
                    "code": 50200,
                    "message": "AI 回答生成失败，可稍后重试",
                    "status": final_status,
                },
            )
            done = self._message_event_data(
                turn.assistant_id,
                turn.user_id,
            )
            done["degraded"] = True
            yield self._sse("done", done)
        finally:
            if iterator is not None and hasattr(iterator, "close"):
                try:
                    iterator.close()
                except Exception:
                    logger.debug(
                        "关闭聊天文本流失败，会话：%s",
                        turn.session_id,
                        exc_info=True,
                    )
            if iterator is not None and hasattr(iterator, "aclose"):
                try:
                    await iterator.aclose()
                except Exception:
                    logger.debug(
                        "关闭异步聊天文本流失败，会话：%s",
                        turn.session_id,
                        exc_info=True,
                    )

    def stop_message(
        self,
        assistant_id: int,
        user_id: int,
    ) -> ChatMessageStopResponse:
        message = self.messages.get_owned(assistant_id, user_id)
        if not message or message.role != "ASSISTANT":
            raise NotFoundError("助手消息不存在")
        active = message.status in {"PENDING", "STREAMING"}
        if active:
            transitioned = self.messages.transition_assistant_status(
                assistant_id,
                {"PENDING", "STREAMING"},
                {
                    "status": "STOPPED",
                    "error_message": "用户已停止生成",
                    "latency_ms": self._elapsed_ms(message.created_at),
                },
            )
            if transitioned:
                message = transitioned
                ttl = max(
                    _STOP_FLAG_MIN_TTL_SECONDS,
                    settings.llm_timeout_seconds * 2,
                )
                redis_manager.set(
                    self._stop_key(assistant_id),
                    "1",
                    ttl,
                )
            else:
                message = (
                    self.messages.get_owned(assistant_id, user_id)
                    or message
                )
            self._bump_cache_version(user_id)
        return ChatMessageStopResponse(
            assistant_id=message.id,
            status=message.status,
            stopped=active or message.status == "STOPPED",
        )

    def retry_message(
        self,
        assistant_id: int,
        user_id: int,
        *,
        stream: bool,
    ) -> ChatTurn:
        del stream
        previous = self.messages.get_owned(assistant_id, user_id)
        if not previous or previous.role != "ASSISTANT":
            raise NotFoundError("助手消息不存在")
        if previous.status in {"PENDING", "STREAMING"}:
            raise ConflictError("该回答仍在生成中，不能重试")
        retry_key = f"retry:{previous.id}"
        existing_retry = self.messages.get_by_idempotency(
            previous.session_id,
            retry_key,
        )
        if existing_retry and existing_retry.role == "ASSISTANT":
            if existing_retry.status not in _TERMINAL_MESSAGE_STATUSES:
                raise self._idempotency_conflict()
            user_message = self.messages.get_owned(
                self._previous_user_id(previous),
                user_id,
            )
            if not user_message:
                raise NotFoundError("原用户消息不存在")
            return self._existing_turn(user_message, existing_retry)
        session = self._require_session(previous.session_id, user_id)
        recent = self.messages.recent_for_session(
            previous.session_id,
            max(previous.sequence_no, 13),
        )
        user_message = next(
            (
                item
                for item in reversed(recent)
                if item.role == "USER"
                and item.sequence_no < previous.sequence_no
            ),
            None,
        )
        if not user_message:
            raise NotFoundError("原用户消息不存在")
        context = self._context_from_snapshot(
            previous.context_snapshot,
            session,
        )
        retrieved = self._retrieve_context(
            context.job_id,
            context.candidate_id,
        )
        retrieved.snapshot["session_no"] = session.session_no
        prompt_safety = detect_prompt_injection(
            {
                "user_content": user_message.content,
                "business_data": retrieved.snapshot,
                "sources": retrieved.sources,
            }
        )
        now = datetime.now(timezone.utc)
        sequence_lock_token = self._acquire_sequence_lock(session.id)
        try:
            sequence_no = self.messages.next_sequence_no(session.id)
            assistant = self.messages.create(
                {
                    "message_no": self._new_no("MSG"),
                    "session_id": session.id,
                    "user_id": user_id,
                    "role": "ASSISTANT",
                    "status": "PENDING",
                    "sequence_no": sequence_no,
                    "content": "",
                    "citations": [],
                    "context_snapshot": retrieved.snapshot,
                    "provider": self.provider.provider_name,
                    "model_name": self.provider.model_name,
                    "idempotency_key": retry_key,
                    "retry_of_message_id": previous.id,
                }
            )
            self.sessions.update(
                session,
                {
                    "message_count": session.message_count + 1,
                    "last_message_preview": user_message.content[:500],
                    "last_message_at": now,
                },
            )
        finally:
            self._release_sequence_lock(session.id, sequence_lock_token)
        self._bump_cache_version(user_id)
        history = [
            {
                "role": (
                    "assistant" if item.role == "ASSISTANT" else "user"
                ),
                "content": item.content[:8000],
            }
            for item in self.messages.recent_for_session(session.id, 13)
            if item.id not in {user_message.id, assistant.id}
            and item.content.strip()
            and item.status in {"COMPLETED", "STOPPED", "CANCELLED"}
        ][-12:]
        return ChatTurn(
            session_id=session.id,
            session_no=session.session_no,
            user_id=user_id,
            user_message_id=user_message.id,
            assistant_id=assistant.id,
            content=user_message.content,
            history=history,
            context_snapshot=retrieved.snapshot,
            sources=retrieved.sources,
            prompt_safety=prompt_safety,
            provider=assistant.provider,
            model_name=assistant.model_name,
            idempotency_key=retry_key,
            started_at=now,
        )

    def _existing_turn_response(
        self,
        turn: ChatTurn,
    ) -> ChatMessageSendResponse:
        user = self.messages.get_owned(turn.user_message_id, turn.user_id)
        assistant = self.messages.get_owned(turn.assistant_id, turn.user_id)
        if not user or not assistant:
            raise NotFoundError("聊天消息不存在")
        return ChatMessageSendResponse(
            user_message=ChatMessageResponse.model_validate(user),
            assistant_message=ChatMessageResponse.model_validate(assistant),
            degraded=turn.existing_degraded,
        )

    async def _replay_events(self, turn: ChatTurn) -> AsyncIterator[str]:
        yield self._sse(
            "meta",
            {
                "session_id": turn.session_id,
                "session_no": turn.session_no,
                "user_message_id": turn.user_message_id,
                "assistant_id": turn.assistant_id,
                "provider": turn.provider,
                "model": turn.model_name,
                "replay": True,
            },
        )
        yield self._sse(
            "progress",
            {
                "stage": "replay",
                "message": "已返回幂等请求的原回答",
                "source_count": len(turn.sources),
            },
        )
        for citation in turn.existing_citations:
            yield self._sse("citation", self._public_citation(citation))
        for chunk in self._chunk_text(turn.existing_content):
            yield self._sse("delta", {"content": chunk})
        done = self._message_event_data(turn.assistant_id, turn.user_id)
        done["degraded"] = turn.existing_degraded
        done["citations"] = turn.existing_citations
        done["replay"] = True
        yield self._sse("done", done)

    def _get_idempotent_turn(
        self,
        session_id: int,
        user_id: int,
        key: str,
    ) -> ChatTurn | None:
        marker = redis_manager.get(self._idempotency_key(user_id, key))
        if marker:
            data = json.loads(marker)
            user_message_id = data.get("user_message_id")
            assistant_id = data.get("assistant_id")
            if not user_message_id or not assistant_id:
                raise self._idempotency_conflict()
            user = self.messages.get_owned(int(user_message_id), user_id)
            assistant = self.messages.get_owned(int(assistant_id), user_id)
            if not user or not assistant or user.session_id != session_id:
                raise self._idempotency_conflict()
            if assistant.status not in _TERMINAL_MESSAGE_STATUSES:
                raise self._idempotency_conflict()
            self._store_idempotency_terminal(
                user_id,
                key,
                user.id,
                assistant.id,
                assistant.status,
            )
            return self._existing_turn(user, assistant)
        user = self.messages.get_by_idempotency(session_id, key)
        if not user or user.role != "USER":
            return None
        assistant = next(
            (
                item
                for item in self.messages.recent_for_session(
                    session_id,
                    max(user.sequence_no + 1, 2),
                )
                if item.role == "ASSISTANT"
                and item.sequence_no == user.sequence_no + 1
            ),
            None,
        )
        if not assistant:
            return None
        if assistant.status not in _TERMINAL_MESSAGE_STATUSES:
            raise self._idempotency_conflict()
        self._store_idempotency_terminal(
            user_id,
            key,
            user.id,
            assistant.id,
            assistant.status,
        )
        return self._existing_turn(user, assistant)

    def _existing_turn(
        self,
        user: Any,
        assistant: Any,
    ) -> ChatTurn:
        return ChatTurn(
            session_id=assistant.session_id,
            session_no=assistant.context_snapshot.get("session_no", ""),
            user_id=user.user_id or assistant.user_id or 0,
            user_message_id=user.id,
            assistant_id=assistant.id,
            content=user.content,
            history=[],
            context_snapshot=assistant.context_snapshot or {},
            sources=[],
            prompt_safety={},
            provider=assistant.provider,
            model_name=assistant.model_name,
            idempotency_key=assistant.idempotency_key,
            replay=True,
            existing_status=assistant.status,
            existing_content=assistant.content,
            existing_citations=assistant.citations or [],
            existing_degraded=assistant.status == "FAILED"
            or assistant.provider == "local",
        )

    def _mark_idempotency_terminal(
        self,
        turn: ChatTurn,
        status: str,
    ) -> None:
        if not turn.idempotency_key:
            return
        self._store_idempotency_terminal(
            turn.user_id,
            turn.idempotency_key,
            turn.user_message_id,
            turn.assistant_id,
            status,
        )

    def _store_idempotency_terminal(
        self,
        user_id: int,
        key: str,
        user_message_id: int,
        assistant_id: int,
        status: str,
    ) -> None:
        redis_manager.set(
            self._idempotency_key(user_id, key),
            json.dumps(
                {
                    "state": "completed",
                    "status": status,
                    "user_message_id": user_message_id,
                    "assistant_id": assistant_id,
                },
                ensure_ascii=False,
            ),
            _IDEMPOTENCY_TTL_SECONDS,
        )

    def _previous_user_id(self, assistant: Any) -> int:
        recent = self.messages.recent_for_session(
            assistant.session_id,
            max(assistant.sequence_no, 2),
        )
        previous = next(
            (
                item
                for item in reversed(recent)
                if item.role == "USER"
                and item.sequence_no < assistant.sequence_no
            ),
            None,
        )
        return previous.id if previous else 0

    def _provider_payload(self, turn: ChatTurn) -> dict[str, Any]:
        return {
            "question": turn.content,
            "current_context": turn.context_snapshot,
            "source_catalog": [
                {
                    "index": item["index"],
                    "source_type": item["source_type"],
                    "source_id": item["source_id"],
                    "title": item["title"],
                    "excerpt": item["excerpt"],
                }
                for item in turn.sources
            ],
            "prompt_safety": turn.prompt_safety,
        }

    def _history_for_prompt(
        self,
        session_id: int,
        *,
        exclude_message_id: int,
    ) -> list[dict[str, str]]:
        messages = self.messages.recent_for_session(session_id, 13)
        history: list[dict[str, str]] = []
        for item in messages:
            if item.id == exclude_message_id:
                continue
            if item.status not in {"COMPLETED", "STOPPED", "CANCELLED"}:
                continue
            if not item.content.strip():
                continue
            history.append(
                {
                    "role": (
                        "assistant"
                        if item.role == "ASSISTANT"
                        else "user"
                    ),
                    "content": item.content[:8000],
                }
            )
        return history[-12:]

    def _retrieve_context(
        self,
        job_id: int | None,
        candidate_id: int | None,
    ) -> RetrievedContext:
        job, candidate, resume = self._validate_context(job_id, candidate_id)
        sources: list[dict[str, Any]] = []
        snapshot: dict[str, Any] = {
            "job_id": job.id if job else None,
            "candidate_id": candidate.id if candidate else None,
            "resume_id": resume.id if resume else None,
            "parse_record_id": None,
            "match_result_id": None,
            "question_ids": [],
            "source_indexes": [],
        }
        if job:
            sources.append(
                self._source(
                    len(sources) + 1,
                    "job",
                    job.id,
                    job.title,
                    self._excerpt(
                        f"{job.requirements}\n{job.description}".strip()
                        or job.title
                    ),
                    f"/jobs/{job.id}",
                )
            )
        if candidate:
            candidate_text = "；".join(
                part
                for part in (
                    candidate.summary or "",
                    f"技能：{', '.join(candidate.skills or [])}",
                    f"当前职位：{candidate.current_title or ''}",
                )
                if part.strip()
            )
            sources.append(
                self._source(
                    len(sources) + 1,
                    "candidate",
                    candidate.id,
                    candidate.name,
                    self._excerpt(candidate_text or candidate.name),
                    f"/candidates/{candidate.id}",
                )
            )
        if resume:
            parse_record = self.parse_records.latest_for_resume(resume.id)
            if parse_record:
                snapshot["parse_record_id"] = parse_record.id
                parsed_text = json.dumps(
                    parse_record.parsed_data,
                    ensure_ascii=False,
                    default=str,
                )
                sources.append(
                    self._source(
                        len(sources) + 1,
                        "resume_parse_record",
                        parse_record.id,
                        resume.filename,
                        self._excerpt(parsed_text),
                        f"/resumes/{resume.id}",
                    )
                )
                snapshot["resume_parse_record_id"] = parse_record.id
        if job and candidate:
            match = self.messages.latest_match(job.id, candidate.id)
            if match:
                snapshot["match_result_id"] = match.id
                match_text = (
                    f"匹配分：{match.score:g}，等级：{match.level}；"
                    f"原因：{'；'.join(match.reasons or [])}"
                )
                sources.append(
                    self._source(
                        len(sources) + 1,
                        "job_match_result",
                        match.id,
                        f"{job.title} - {candidate.name} 匹配结果",
                        self._excerpt(match_text),
                        f"/match-results/{match.id}",
                    )
                )
        if job:
            questions = self.messages.related_questions(
                job.id,
                candidate.id if candidate else None,
                6,
            )
            snapshot["question_ids"] = [item.id for item in questions]
            for question in questions:
                route = (
                    f"/interviews/{question.interview_id}/questions"
                    if question.interview_id
                    else "/interview-questions"
                )
                sources.append(
                    self._source(
                        len(sources) + 1,
                        "interview_question",
                        question.id,
                        question.category,
                        self._excerpt(question.question),
                        route,
                    )
                )
        snapshot["source_indexes"] = [item["index"] for item in sources]
        return RetrievedContext(
            snapshot=snapshot,
            sources=sources,
            has_business_data=bool(sources),
        )

    def _validate_context(
        self,
        job_id: int | None,
        candidate_id: int | None,
    ) -> tuple[Any | None, Any | None, Any | None]:
        job = self.jobs.get(job_id) if job_id else None
        if job_id and not job:
            raise NotFoundError("岗位不存在")
        candidate = self.candidates.get(candidate_id) if candidate_id else None
        if candidate_id and not candidate:
            raise NotFoundError("候选人不存在")
        resume = (
            self.messages.latest_resume(candidate.id)
            if candidate
            else None
        )
        return job, candidate, resume

    def _merge_context(
        self,
        session: Any,
        override: ChatContext | None,
    ) -> ChatContext:
        job_id = session.job_id
        candidate_id = session.candidate_id
        if override is not None:
            provided = override.model_fields_set
            if "job_id" in provided:
                job_id = override.job_id
            if "candidate_id" in provided:
                candidate_id = override.candidate_id
        return ChatContext(job_id=job_id, candidate_id=candidate_id)

    def _context_from_snapshot(
        self,
        snapshot: dict[str, Any],
        session: Any,
    ) -> ChatContext:
        return ChatContext(
            job_id=snapshot.get("job_id", session.job_id),
            candidate_id=snapshot.get(
                "candidate_id",
                session.candidate_id,
            ),
        )

    def _require_session(self, session_id: int, user_id: int) -> Any:
        session = self.sessions.get_owned(session_id, user_id)
        if not session:
            raise NotFoundError("会话不存在")
        return session

    def _save_assistant(
        self,
        assistant: Any,
        *,
        content: str,
        status: str,
        citations: list[dict[str, Any]],
        latency_ms: float,
        error_message: str | None,
    ) -> Any:
        allowed_statuses = {"PENDING", "STREAMING"}
        if status == "STOPPED":
            allowed_statuses.add("STOPPED")
        updated = self.messages.transition_assistant_status(
            assistant.id,
            allowed_statuses,
            {
                "content": content,
                "status": status,
                "citations": citations,
                "latency_ms": latency_ms,
                "error_message": error_message,
            },
        )
        return updated or self.messages.get(assistant.id)

    def _update_session_after_assistant(
        self,
        session_id: int,
        content: str,
    ) -> None:
        session = self.sessions.get(session_id)
        if not session:
            return
        self.sessions.update(
            session,
            {
                "last_message_preview": content[:500],
                "last_message_at": datetime.now(timezone.utc),
            },
        )

    def _mark_partial(
        self,
        turn: ChatTurn,
        content: str,
        *,
        status: str,
        error_message: str,
    ) -> None:
        assistant = self.messages.get_owned(
            turn.assistant_id,
            turn.user_id,
        )
        if not assistant:
            return
        final_status = (
            "STOPPED"
            if assistant.status == "STOPPED"
            else status
        )
        assistant = self._save_assistant(
            assistant,
            content=content or assistant.content,
            status=final_status,
            citations=assistant.citations or [],
            latency_ms=self._elapsed_ms(turn.started_at),
            error_message=error_message,
        )
        self._mark_idempotency_terminal(turn, assistant.status)
        self._update_session_after_assistant(
            turn.session_id,
            assistant.content,
        )
        self._bump_cache_version(turn.user_id)

    def _validate_citations(
        self,
        answer: str,
        sources: list[dict[str, Any]],
    ) -> tuple[str, list[dict[str, Any]]]:
        allowed = {
            int(item["index"]): self._public_citation(item)
            for item in sources
        }

        def replace_group(match: re.Match[str]) -> str:
            indexes = sorted(
                {
                    int(value)
                    for value in _CITATION_INDEX.findall(match.group(1))
                }
            )
            valid = [index for index in indexes if index in allowed]
            return " ".join(f"[S{index}]" for index in valid)

        cleaned = _CITATION_GROUP.sub(replace_group, answer).strip()
        used: list[dict[str, Any]] = []
        for match in _CITATION_INDEX.finditer(cleaned):
            index = int(match.group(1))
            if index in allowed and all(
                item["source_id"] != allowed[index]["source_id"]
                or item["source_type"] != allowed[index]["source_type"]
                for item in used
            ):
                used.append(allowed[index])
        return cleaned, used

    def _newly_cited_sources(
        self,
        buffer: str,
        sources: list[dict[str, Any]],
        emitted: set[int],
    ) -> list[tuple[int, dict[str, Any]]]:
        allowed = {
            int(item["index"]): item
            for item in sources
        }
        result: list[tuple[int, dict[str, Any]]] = []
        for match in _CITATION_INDEX.finditer(buffer):
            index = int(match.group(1))
            if index not in allowed or index in emitted:
                continue
            emitted.add(index)
            result.append(
                (index, self._public_citation(allowed[index]))
            )
        return result

    def _citations_for_events(
        self,
        citations: list[dict[str, Any]],
        sources: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        index_by_source = {
            (item["source_type"], item["source_id"]): int(item["index"])
            for item in sources
        }
        return [
            {
                **citation,
                "source_index": index_by_source.get(
                    (citation["source_type"], citation["source_id"]),
                    0,
                ),
            }
            for citation in citations
        ]

    @staticmethod
    def _public_citation(source: dict[str, Any]) -> dict[str, Any]:
        return {
            "source_type": source["source_type"],
            "source_id": source["source_id"],
            "title": source["title"],
            "excerpt": source["excerpt"],
            "route": source["route"],
        }

    @staticmethod
    def _source(
        index: int,
        source_type: str,
        source_id: int,
        title: str,
        excerpt: str,
        route: str,
    ) -> dict[str, Any]:
        return {
            "index": index,
            "source_type": source_type,
            "source_id": source_id,
            "title": title[:200],
            "excerpt": excerpt[:1000],
            "route": route[:500],
        }

    @staticmethod
    def _excerpt(value: str) -> str:
        text = re.sub(r"\s+", " ", str(value or "")).strip()
        return text[:1000] or "暂无可用摘要"

    def _message_event_data(
        self,
        assistant_id: int,
        user_id: int,
    ) -> dict[str, Any]:
        message = self.messages.get_owned(assistant_id, user_id)
        if not message:
            return {
                "assistant_id": assistant_id,
                "status": "FAILED",
                "content": "",
                "citations": [],
            }
        return {
            "assistant_id": message.id,
            "message_no": message.message_no,
            "status": message.status,
            "content": message.content,
            "citations": message.citations or [],
            "latency_ms": message.latency_ms,
            "error": message.error_message,
        }

    def _session_list_cache_key(
        self,
        user_id: int,
        page: int,
        page_size: int,
        keyword: str | None,
    ) -> str:
        keyword_digest = hashlib.sha256(
            (keyword or "").strip().encode("utf-8")
        ).hexdigest()[:16]
        return (
            "recruit:chat:sessions:"
            f"{user_id}:{self._cache_version(user_id)}:"
            f"{page}:{page_size}:{keyword_digest}"
        )

    def _session_detail_cache_key(
        self,
        session_id: int,
        user_id: int,
    ) -> str:
        return (
            f"recruit:chat:session:{user_id}:{session_id}:"
            f"{self._cache_version(user_id)}"
        )

    def _cache_version(self, user_id: int) -> int:
        key = f"recruit:chat:cache-version:{user_id}"
        current = redis_manager.get(key)
        if current is not None:
            return int(current)
        redis_manager.set(key, "1", _IDEMPOTENCY_TTL_SECONDS)
        return 1

    def _bump_cache_version(self, user_id: int) -> None:
        redis_manager.increment(
            f"recruit:chat:cache-version:{user_id}",
            _IDEMPOTENCY_TTL_SECONDS,
        )

    def _acquire_sequence_lock(self, session_id: int) -> str:
        key = f"recruit:chat:sequence-lock:{session_id}"
        token = uuid4().hex
        deadline = time.monotonic() + _SEQUENCE_LOCK_WAIT_SECONDS
        while True:
            if redis_manager.set_nx(
                key,
                token,
                _SEQUENCE_LOCK_TTL_SECONDS,
            ):
                return token
            if time.monotonic() >= deadline:
                raise AppError(
                    "会话正在处理其他消息，请稍后重试",
                    code=40910,
                    status_code=409,
                )
            time.sleep(0.05)

    def _release_sequence_lock(
        self,
        session_id: int,
        token: str,
    ) -> None:
        key = f"recruit:chat:sequence-lock:{session_id}"
        if redis_manager.get(key) == token:
            redis_manager.delete(key)

    @staticmethod
    def _idempotency_conflict() -> AppError:
        return AppError(
            "相同幂等键的请求正在处理中",
            code=40910,
            status_code=409,
        )

    @staticmethod
    def _normalize_idempotency_key(value: str | None) -> str | None:
        if not value:
            return None
        cleaned = value.strip()
        return cleaned[:128] if cleaned else None

    @staticmethod
    def _idempotency_key(user_id: int, value: str) -> str:
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
        return f"recruit:chat:idempotency:{user_id}:{digest}"

    @staticmethod
    def _stop_key(assistant_id: int) -> str:
        return f"recruit:chat:stop:{assistant_id}"

    def _stop_requested(self, assistant_id: int) -> bool:
        return redis_manager.exists(self._stop_key(assistant_id))

    @staticmethod
    def _new_no(prefix: str) -> str:
        return f"{prefix}-{uuid4().hex.upper()}"

    @staticmethod
    def _elapsed_ms(started_at: datetime) -> float:
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        return round(
            max(
                0.0,
                (datetime.now(timezone.utc) - started_at).total_seconds()
                * 1000,
            ),
            2,
        )

    @staticmethod
    def _chunk_text(text: str, size: int = 40) -> Iterator[str]:
        for index in range(0, len(text), size):
            yield text[index : index + size]

    @staticmethod
    def _sse(event: str, data: dict[str, Any]) -> str:
        payload = json.dumps(data, ensure_ascii=False, default=str)
        return f"event: {event}\ndata: {payload}\n\n"
