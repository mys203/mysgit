# models/chat_ai.py —— AI 聊天消息表：存每一轮对话，供多轮上下文取用
from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ChatMessage(Base):
    """AI 对话消息表：一条记录 = 一轮对话里的一句话"""
    __tablename__ = "chat_message"

    __table_args__ = (
        Index("idx_chat_session", "session_id"),  # 按会话查历史，建索引
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="消息ID")
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="会话ID（标识一轮完整对话）")
    role: Mapped[str] = mapped_column(String(20), nullable=False, comment="角色：user / assistant")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息内容")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="发送时间")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, session_id={self.session_id}, role={self.role})>"
