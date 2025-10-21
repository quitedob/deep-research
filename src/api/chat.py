# -*- coding: utf-8 -*-
"""
聊天相关API端点
"""

from typing import List, Optional, Literal
from pathlib import Path
import logging

from fastapi import APIRouter, HTTPException, Depends
from src.api.deps import require_quota
from src.sqlmodel.models import User
from src.core.llms.router.smart_router import ModelRouter, LLMMessage
from src.services.session_service import store
from src.core.security import sanitize_model_output
from src.schemas.chat import ChatItem, ChatReq, ChatResp

logger = logging.getLogger(__name__)

router = APIRouter()

# 初始化模型路由器
_model_router = ModelRouter.from_conf(Path("conf.yaml"))

@router.post("/llm/chat", response_model=ChatResp, dependencies=[Depends(require_quota("chat"))])
async def llm_chat(req: ChatReq):
    """LLM聊天端点"""
    try:
        msgs = [LLMMessage(role=m.role, content=m.content) for m in req.messages]
        result = await _model_router.chat(
            task=req.task,
            size=req.size,
            messages=msgs,
            temperature=req.temperature,
            max_tokens=req.max_tokens
        )
        return ChatResp(model=result["model"], content=sanitize_model_output(result["content"]))
    except Exception as e:
        logger.error(f"LLM聊天失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=ChatResp)
async def simple_chat(payload: dict):
    """兼容前端简单聊天接口：接受 {message, session_id} 并调用统一聊天，带会话记忆。"""
    message = payload.get("message", "")
    session_id = payload.get("session_id")
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    try:
        session_id = await store.ensure_session(session_id)
        history = await store.get_messages(session_id)
        await store.append_message(session_id, "user", message)

        # 将历史拼接发送（简单策略：直接传历史）
        msgs = [LLMMessage(role=m["role"], content=m["content"]) for m in history]
        msgs.append(LLMMessage(role="user", content=message))

        result = await _model_router.chat(task="general", size="medium", messages=msgs, temperature=0.7)
        final = sanitize_model_output(result["content"])
        await store.append_message(session_id, "assistant", final)
        return ChatResp(model=result["model"], content=final)
    except Exception as e:
        logger.error(f"简单聊天失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# TODO: 流式聊天功能需要重新实现
# from src.services.chat_stream_service import router as stream_router
# router.include_router(stream_router)