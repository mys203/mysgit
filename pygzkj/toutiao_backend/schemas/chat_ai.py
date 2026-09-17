from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str                      # 用户这次问的问题
    session_id: Optional[str] = None   # 会话ID，不传就新建一个会话
