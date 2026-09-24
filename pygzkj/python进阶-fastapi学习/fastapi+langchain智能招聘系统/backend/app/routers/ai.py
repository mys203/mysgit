from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    Query,
    Request,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.common.response import success
from app.config.database import get_db
from app.schemas.ai import InterviewQuestionGenerateRequest, MatchRequest
from app.schemas.ai_chat import (
    ChatContextUpdate,
    ChatMessageCreate,
    ChatMessageRetry,
    ChatSessionCreate,
    ChatSessionRename,
)
from app.schemas.interviews import InterviewQuestionUpdate, QuestionApproveRequest
from app.security.dependencies import require_permissions
from app.security.rate_limit import rate_limit
from app.services.ai_service import AIService, run_match_task, run_question_task
from app.services.chat_service import AIChatService
from app.services.interview_service import InterviewService
from app.services.operations_service import AITaskQueryService

router = APIRouter(tags=["AI"])
DbSession = Annotated[Session, Depends(get_db)]
AIReader = Annotated[object, Depends(require_permissions("ai:execute"))]
AIWriter = Annotated[object, Depends(require_permissions("ai:execute"))]
InterviewReader = Annotated[object, Depends(require_permissions("interviews:read"))]
InterviewWriter = Annotated[object, Depends(require_permissions("interviews:write"))]


def _chat_stream_response(service: AIChatService, turn, request: Request):
    return StreamingResponse(
        service.stream_events(turn, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/ai/chat/sessions",
    dependencies=[Depends(rate_limit("chat:sessions:list", 180))],
)
def list_chat_sessions(
    db: DbSession,
    user: AIReader,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None, max_length=200),
):
    return success(
        AIChatService(db).list_sessions(
            user.id,
            page,
            page_size,
            keyword,
        )
    )


@router.post(
    "/ai/chat/sessions",
    dependencies=[Depends(rate_limit("chat:sessions:create", 60))],
)
def create_chat_session(
    payload: ChatSessionCreate,
    db: DbSession,
    user: AIWriter,
):
    return success(
        AIChatService(db).create_session(payload, user.id),
        status_code=201,
    )


@router.get("/ai/chat/sessions/{session_id}")
def get_chat_session(
    session_id: int,
    db: DbSession,
    user: AIReader,
):
    return success(AIChatService(db).get_session(session_id, user.id))


@router.patch(
    "/ai/chat/sessions/{session_id}",
    dependencies=[Depends(rate_limit("chat:sessions:update", 120))],
)
def rename_chat_session(
    session_id: int,
    payload: ChatSessionRename,
    db: DbSession,
    user: AIWriter,
):
    return success(
        AIChatService(db).rename_session(
            session_id,
            payload,
            user.id,
        )
    )


@router.patch(
    "/ai/chat/sessions/{session_id}/context",
    dependencies=[Depends(rate_limit("chat:sessions:context", 120))],
)
def update_chat_context(
    session_id: int,
    payload: ChatContextUpdate,
    db: DbSession,
    user: AIWriter,
):
    return success(
        AIChatService(db).update_context(
            session_id,
            payload,
            user.id,
        )
    )


@router.delete(
    "/ai/chat/sessions/{session_id}",
    dependencies=[Depends(rate_limit("chat:sessions:delete", 60))],
)
def delete_chat_session(
    session_id: int,
    db: DbSession,
    user: AIWriter,
):
    return success(AIChatService(db).delete_session(session_id, user.id))


@router.get(
    "/ai/chat/sessions/{session_id}/messages",
    dependencies=[Depends(rate_limit("chat:messages:list", 240))],
)
def list_chat_messages(
    session_id: int,
    db: DbSession,
    user: AIReader,
    before_sequence: int | None = Query(None, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return success(
        AIChatService(db).list_messages(
            session_id,
            user.id,
            before_sequence=before_sequence,
            page_size=page_size,
        )
    )


@router.post(
    "/ai/chat/sessions/{session_id}/messages",
    dependencies=[Depends(rate_limit("chat:messages:create", 60))],
)
def create_chat_message(
    session_id: int,
    payload: ChatMessageCreate,
    request: Request,
    db: DbSession,
    user: AIWriter,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        max_length=128,
    ),
):
    service = AIChatService(db)
    turn = service.prepare_message(
        session_id,
        payload,
        user.id,
        idempotency_key=idempotency_key,
    )
    if payload.stream:
        return _chat_stream_response(service, turn, request)
    return success(service.complete_turn(turn))


@router.post(
    "/ai/chat/messages/{assistant_id}/stop",
    dependencies=[Depends(rate_limit("chat:messages:stop", 120))],
)
def stop_chat_message(
    assistant_id: int,
    db: DbSession,
    user: AIWriter,
):
    return success(
        AIChatService(db).stop_message(assistant_id, user.id)
    )


@router.post(
    "/ai/chat/messages/{assistant_id}/retry",
    dependencies=[Depends(rate_limit("chat:messages:retry", 60))],
)
def retry_chat_message(
    assistant_id: int,
    request: Request,
    db: DbSession,
    user: AIWriter,
    payload: ChatMessageRetry | None = None,
):
    retry_payload = payload or ChatMessageRetry()
    service = AIChatService(db)
    turn = service.retry_message(
        assistant_id,
        user.id,
        stream=retry_payload.stream,
    )
    if retry_payload.stream:
        return _chat_stream_response(service, turn, request)
    return success(service.complete_turn(turn))


@router.get("/ai/tasks/{task_no}")
def get_ai_task(task_no: str, db: DbSession, user: AIReader):
    return success(AITaskQueryService(db).get(task_no))


@router.post("/ai/matches", dependencies=[Depends(rate_limit("ai:match", 30))])
def match(
    payload: MatchRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
    user: AIWriter,
):
    task = AIService(db).prepare_match_task(payload, user.id)
    background_tasks.add_task(
        run_match_task, task.task_no, payload.model_dump(mode="json"), user.id
    )
    return success(task, status_code=202)


@router.get("/match-results/{result_id}")
def get_match_result(result_id: int, db: DbSession, user: AIReader):
    return success(AIService(db).get_match_result(result_id))


@router.post("/ai/interview-questions", dependencies=[Depends(rate_limit("ai:questions", 30))])
def generate_interview_questions(
    payload: InterviewQuestionGenerateRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
    user: AIWriter,
):
    task = InterviewService(db).prepare_generation(payload, user)
    background_tasks.add_task(
        run_question_task, task.task_no, payload.model_dump(mode="json"), user.id
    )
    return success(task, status_code=202)


@router.get("/interviews/{interview_id}/questions")
def list_questions(interview_id: int, db: DbSession, user: AIReader):
    return success({"items": InterviewService(db).list_questions(interview_id)})


@router.get("/interview-questions")
def list_global_questions(
    db: DbSession,
    user: InterviewReader,
    status: str | None = Query(None, max_length=30),
    category: str | None = Query(None, max_length=50),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = InterviewService(db).list_global_questions(
        page, page_size, status, category
    )
    return success(
        {"items": items, "total": total, "page": page, "page_size": page_size}
    )


@router.patch("/interview-questions/{question_id}")
def update_question(
    question_id: int,
    payload: InterviewQuestionUpdate,
    db: DbSession,
    user: InterviewWriter,
):
    return success(InterviewService(db).update_question(question_id, payload, user))


@router.post("/interview-questions/approve")
def approve_questions(payload: QuestionApproveRequest, db: DbSession, user: InterviewWriter):
    return success(InterviewService(db).approve(payload.question_ids, user))
