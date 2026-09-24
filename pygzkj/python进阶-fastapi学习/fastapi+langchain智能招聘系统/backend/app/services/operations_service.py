from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.common.exceptions import NotFoundError
from app.config.redis import redis_manager
from app.config.settings import settings
from app.dao.repositories import AITaskDAO, DashboardDAO, OperationLogDAO
from app.schemas.ai import AITaskResponse
from app.services.helpers import model_dict


class OperationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.logs = OperationLogDAO(db)

    def list_logs(
        self,
        page: int,
        page_size: int,
        user_id: int | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ):
        rows, total = self.logs.search(
            page,
            page_size,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            start_time=start_time,
            end_time=end_time,
        )
        return [model_dict(item) for item in rows], total

    def get_log(self, log_id: int) -> dict:
        item = self.logs.get(log_id)
        if not item:
            raise NotFoundError("操作日志不存在")
        return model_dict(item)


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def summary(self) -> dict[str, Any]:
        cache_key = "recruit:cache:dashboard:summary"
        cached = redis_manager.get(cache_key)
        if cached:
            import json

            return json.loads(cached)
        result = DashboardDAO(self.db).summary()
        result["generated_at"] = datetime.now(timezone.utc).isoformat()
        import json

        redis_manager.set(cache_key, json.dumps(result, ensure_ascii=False), settings.cache_ttl_seconds)
        return result


class AITaskQueryService:
    def __init__(self, db: Session) -> None:
        self.tasks = AITaskDAO(db)

    def get(self, task_no: str) -> AITaskResponse:
        task = self.tasks.get_by_task_no(task_no)
        if not task:
            raise NotFoundError("AI 任务不存在")
        return AITaskResponse.model_validate(task)

