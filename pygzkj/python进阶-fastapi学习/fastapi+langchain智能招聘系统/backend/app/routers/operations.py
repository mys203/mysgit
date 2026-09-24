from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import success
from app.config.database import get_db
from app.security.dependencies import require_permissions
from app.security.rate_limit import rate_limit
from app.services.operations_service import DashboardService, OperationService

router = APIRouter(tags=["运维与看板"])
DbSession = Annotated[Session, Depends(get_db)]
LogReader = Annotated[object, Depends(require_permissions("logs:read"))]
DashboardReader = Annotated[object, Depends(require_permissions("jobs:read"))]


@router.get("/operation-logs", dependencies=[Depends(rate_limit("logs:list", 120))])
def list_operation_logs(
    db: DbSession,
    user: LogReader,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int | None = None,
    action: str | None = Query(None, max_length=100),
    resource_type: str | None = Query(None, max_length=100),
    start_time: datetime | None = None,
    end_time: datetime | None = None,
):
    items, total = OperationService(db).list_logs(
        page, page_size, user_id, action, resource_type, start_time, end_time
    )
    return success({"items": items, "total": total, "page": page, "page_size": page_size})


@router.get("/operation-logs/{log_id}")
def get_operation_log(log_id: int, db: DbSession, user: LogReader):
    return success(OperationService(db).get_log(log_id))


@router.get("/dashboard/summary")
def dashboard_summary(db: DbSession, user: DashboardReader):
    return success(DashboardService(db).summary())
