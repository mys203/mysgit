from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.common.response import page_result, success


def serialize_model(instance: Any, schema: type[BaseModel]) -> dict:
    return schema.model_validate(instance).model_dump(mode="json")


def paginated(items: list[Any], total: int, page: int, page_size: int):
    serialized = [
        item.model_dump(mode="json") if isinstance(item, BaseModel) else item
        for item in items
    ]
    return success(page_result(serialized, total, page, page_size))

