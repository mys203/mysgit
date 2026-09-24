from contextvars import ContextVar

request_id_context: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    return request_id_context.get() or "unknown"


def set_request_id(request_id: str) -> None:
    request_id_context.set(request_id)

