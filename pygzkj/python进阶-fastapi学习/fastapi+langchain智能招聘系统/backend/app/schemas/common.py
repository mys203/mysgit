from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ORMSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginationQuery(StrictSchema):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class IdsRequest(StrictSchema):
    ids: list[int] = Field(min_length=1, max_length=200)


class MessageData(BaseModel):
    message: str
    detail: dict[str, Any] | None = None

