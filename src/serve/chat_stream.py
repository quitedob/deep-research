from typing import AsyncIterator, Dict, Any, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.llms.router import ModelRouter, LLMMessage
from src.serve.session_store import store
from src.serve.sanitizer import sanitize_model_output


router = APIRouter()
_router: ModelRouter | None = None  # 将在首次请求时惰性加载 conf.yaml


async def _ensure_router() -> ModelRouter:
    global _router
    if isinstance(_router, ModelRouter):
        return _router
    from pathlib import Path
    _router = ModelRouter.from_conf(Path("conf.yaml"))
    return _router


async def _sse(messages: List[Dict[str, Any]], session_id: str | None) -> AsyncIterator[bytes]:
    try:
        router = await _ensure_router()
        yield b"data: {\"type\":\"start\"}\n\n"

        # 简单会话记忆：拼接历史
        sid = await store.ensure_session(session_id)
        history = await store.get_messages(sid)
        # 使用消息参数或 message 文本追加
        msgs = [LLMMessage(role=m["role"], content=m["content"]) for m in history]
        for m in messages:
            msgs.append(LLMMessage(role=m.get("role", "user"), content=m.get("content", "")))
        # 将新用户消息存储
        if messages:
            last_user = messages[-1]
            await store.append_message(sid, last_user.get("role", "user"), last_user.get("content", ""))

        # 简化：一次性结果
        result = await router.chat(task="general", size="medium", messages=msgs)
        final = sanitize_model_output(result["content"]) 
        await store.append_message(sid, "assistant", final)
        yield f"data: {{\"type\":\"content\",\"content\":{final!r}}}\n\n".encode("utf-8")
        yield b"data: {\"type\":\"done\"}\n\n"
    except Exception as e:
        yield f"data: {{\"type\":\"error\",\"error\":{str(e)!r}}}\n\n".encode("utf-8")


@router.post("/chat/stream")
async def chat_stream(payload: Dict[str, Any]):
    messages = payload.get("messages") or [{"role": "user", "content": payload.get("message", "")}]
    session_id = payload.get("session_id")
    if not messages:
        raise HTTPException(status_code=400, detail="messages is required")
    return StreamingResponse(_sse(messages, session_id), media_type="text/event-stream")


