# crud/chat_ai.py —— AI 对话的数据库操作：存消息、取历史
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.chat_ai import ChatMessage


async def add_message(
        db: AsyncSession,
        session_id: str,
        role: str,
        content: str,
):
    """存一条对话消息"""
    msg = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_all_messages(
        db: AsyncSession,
        session_id: str,
):
    """取某个会话的全部历史，按时间正序返回（id 自增，用它排序最稳）"""
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return rows
