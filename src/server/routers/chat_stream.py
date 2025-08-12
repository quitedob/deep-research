# -*- coding: utf-8 -*-
"""
聊天流式API路由（学习模式 SSE），基于 Kimi/Moonshot 流式输出  # 模块说明
"""
import asyncio  # 异步工具
import logging  # 日志
from typing import Optional, List, Dict  # 类型注解

from fastapi import APIRouter, HTTPException, Header  # FastAPI
from fastapi.responses import StreamingResponse  # 流式响应
from pydantic import BaseModel  # 请求模型

from src.config.settings import get_settings  # 配置
from src.config.prompts import load_prompt  # 提示词
from src.llms.kimi_provider import get_kimi_provider  # Kimi 客户端
from src.memory.conversation_buffer import get_conversation_buffer  # 对话缓冲
from src.server.routers.auth import verify_token  # Token 校验
from src.server.db import insert_chat_log, insert_usage_log, get_user_by_username  # DB
from src.server.utils.sanitizer import strip_reasoning, IncrementalReasoningFilter  # 输出清洗

logger = logging.getLogger(__name__)  # 日志器
router = APIRouter(prefix="/api", tags=["学习与研究模式（流式）"])  # 路由器

settings = get_settings()  # 读取配置
provider = get_kimi_provider()  # 提供商
async_client = provider.get_async_chat_model()  # 异步客户端


class ChatStreamRequest(BaseModel):  # 请求模型
    message: str  # 用户消息
    session_id: Optional[str] = None  # 会话ID


def _sse(data: Dict) -> str:
    """将字典编码为 SSE 行"""
    import json
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
async def chat_stream(request: ChatStreamRequest, authorization: str | None = Header(default=None)):
    """学习模式流式聊天（SSE）"""
    session_id = request.session_id or "chat-stream"
    buffer = get_conversation_buffer(session_id)
    buffer.add_user_message(request.message)

    # 可选用户ID
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        username = verify_token(authorization.split(" ", 1)[1])
        if username:
            user = get_user_by_username(username)
            user_id = user["id"] if user else None

    tutor_prompt = load_prompt("tutor")
    history: List[Dict[str, str]] = buffer.get_messages()
    messages = [{"role": "system", "content": tutor_prompt}] + history + [
        {"role": "user", "content": request.message}
    ]

    async def event_gen():
        final_text_parts: List[str] = []
        filt = IncrementalReasoningFilter()  # 分片级过滤器
        # 起始事件
        yield _sse({"type": "start"})
        try:
            stream = await async_client.chat.completions.create(
                model=settings.KIMI_MODEL_CHAT,
                messages=messages,
                stream=True,
            )
            async for chunk in stream:
                try:
                    choice = chunk.choices[0]
                    delta = getattr(choice, "delta", None)
                    content_piece = None
                    if delta and getattr(delta, "content", None):
                        content_piece = delta.content
                    else:
                        # 兼容部分SDK结构
                        message = getattr(choice, "message", None)
                        if message and getattr(message, "content", None):
                            content_piece = message.content
                    if content_piece:
                        # 分片级过滤，避免<think>内容外泄
                        safe_piece = filt.process(content_piece)
                        if safe_piece:
                            final_text_parts.append(safe_piece)
                            yield _sse({"type": "content", "content": safe_piece})
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"流式聊天失败: {e}", exc_info=True)
            yield _sse({"type": "error", "error": str(e)})
            return

        # 完成事件
        final_text = strip_reasoning("".join(final_text_parts))
        buffer.add_assistant_message(final_text)
        insert_chat_log(user_id, session_id, "user", request.message, settings.KIMI_MODEL_CHAT)
        insert_chat_log(user_id, session_id, "assistant", final_text, settings.KIMI_MODEL_CHAT)
        insert_usage_log(user_id, endpoint="/api/chat/stream", model=settings.KIMI_MODEL_CHAT, tokens_in=len(request.message), tokens_out=len(final_text))
        yield _sse({"type": "done"})
        await asyncio.sleep(0)  # 让出控制权

    return StreamingResponse(event_gen(), media_type="text/event-stream")


