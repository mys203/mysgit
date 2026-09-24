from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.common.request_context import get_request_id


def _serialize(data: Any) -> Any:
    if isinstance(data, BaseModel):
        return data.model_dump(mode="json")
    return jsonable_encoder(data)


def success(
    data: Any = None,
    message: str = "成功",
    code: int = 0,
    status_code: int = 200,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "data": _serialize(data),
            "request_id": get_request_id(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def error(
    message: str,
    code: int,
    status_code: int,
    data: Any = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "data": _serialize(data),
            "request_id": get_request_id(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def page_result(items: list[Any], total: int, page: int, page_size: int) -> dict[str, Any]:
    pages = (total + page_size - 1) // page_size if page_size else 0
    return {
        "items": _serialize(items),
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }

