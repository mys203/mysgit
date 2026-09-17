import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.ai_conf import client, MODEL_NAME, SYSTEM_PROMPT, MAX_HISTORY_ROUNDS, TEMPERATURE
from config.db_config import get_db
from crud import chat_ai
from schemas.chat_ai import ChatRequest

router = APIRouter(prefix="/api/ai", tags=["ai"])


async def _summarize(messages: list) -> str:
    """把超出窗口的旧对话压缩成一段摘要，省 token 又不丢关键信息"""
    resp = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "请把下面这段对话压缩成100字以内的摘要，保留关键信息。"},
            *messages,
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content


@router.post("/chat")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    # 没有 session_id 就新建一个，返回给前端存起来，下次继续用
    session_id = req.session_id or uuid.uuid4().hex

    # 从库里取全部历史，转成模型要的格式
    history_rows = await chat_ai.get_all_messages(db, session_id)
    history = [{"role": m.role, "content": m.content} for m in history_rows]

    # 截断窗口：历史超过 MAX_HISTORY_ROUNDS 轮，把最早的多余部分压成摘要
    summary = ""
    if len(history) > MAX_HISTORY_ROUNDS * 2:
        overflow = history[: len(history) - MAX_HISTORY_ROUNDS * 2]
        summary = await _summarize(overflow)
        history = history[-MAX_HISTORY_ROUNDS * 2:]

    # 组装消息：system + 摘要 + 最近历史 + 当前问题
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if summary:
        messages.append({"role": "system", "content": f"之前对话的摘要：{summary}"})
    messages.extend(history)
    messages.append({"role": "user", "content": req.question})

    try:
        resp = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=TEMPERATURE,
        )
        answer = resp.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调用AI失败: {e}")

    # 把这一轮的 user 问题和 assistant 回答都存进库，供下一轮取用
    await chat_ai.add_message(db, session_id, "user", req.question)
    await chat_ai.add_message(db, session_id, "assistant", answer)

    return {
        "code": 200,
        "msg": "success",
        "data": {"session_id": session_id, "answer": answer},
    }


@router.get("/history")
async def history(session_id: str, db: AsyncSession = Depends(get_db)):
    """按会话ID拉取历史对话，前端切回聊天页时用它恢复内容"""
    rows = await chat_ai.get_all_messages(db, session_id)
    messages = [{"role": m.role, "content": m.content} for m in rows]
    return {
        "code": 200,
        "msg": "success",
        "data": {"messages": messages},
    }
