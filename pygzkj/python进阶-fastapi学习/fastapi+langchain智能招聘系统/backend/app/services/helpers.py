from __future__ import annotations

from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.common.request_context import get_request_id
from app.dao.repositories import OperationLogDAO
from app.security.dependencies import UserPrincipal


def model_dict(instance: Any, exclude: set[str] | None = None) -> dict[str, Any]:
    excluded = exclude or set()
    return {
        column.name: getattr(instance, column.name)
        for column in instance.__table__.columns
        if column.name not in excluded
    }


def record_operation(
    db: Session,
    user: UserPrincipal | None,
    *,
    method: str,
    path: str,
    action: str,
    resource_type: str | None = None,
    resource_id: int | str | None = None,
    status_code: int = 200,
    detail: dict[str, Any] | None = None,
    request: Request | None = None,
) -> None:
    OperationLogDAO(db).create(
        {
            "user_id": user.id if user else None,
            "username": user.username if user else None,
            "method": method,
            "path": path,
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id is not None else None,
            "status_code": status_code,
            "ip": request.client.host if request and request.client else None,
            "user_agent": request.headers.get("user-agent") if request else None,
            "request_id": get_request_id(),
            "detail": detail or {},
        }
    )

