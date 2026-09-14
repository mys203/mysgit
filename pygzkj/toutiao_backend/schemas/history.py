from pydantic import BaseModel, Field


class HistoryAddResponse(BaseModel):
    news_id: int = Field(...,alias="newsId")