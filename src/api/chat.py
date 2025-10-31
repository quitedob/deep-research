# -*- coding: utf-8 -*-
"""
聊天相关API端点
集成智能对话编排服务
"""

from typing import List, Optional, Literal
from pathlib import Path
import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.api.deps import require_quota, require_auth
from src.core.db import get_db_session
from src.sqlmodel.models import User
from src.core.llms.router.smart_router import ModelRouter, LLMMessage
from src.services.session_service import store
from src.services.smart_conversation_service import (
    get_smart_conversation_service,
    ConversationMode
)
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


# ==================== 智能对话编排API ====================

class SmartChatRequest(BaseModel):
    """智能聊天请求"""
    message: str
    session_id: str
    force_mode: Optional[str] = None  # "normal" 或 "rag_enhanced"


class SmartChatResponse(BaseModel):
    """智能聊天响应"""
    success: bool
    content: str
    mode: str
    message_count: int
    needs_network: bool
    rag_used: bool
    search_used: bool
    sources: List[dict] = []
    metadata: dict


@router.post("/smart-chat", response_model=SmartChatResponse)
async def smart_chat(
    request: SmartChatRequest,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """
    智能对话接口
    自动根据消息数量切换模式，支持RAG增强和联网搜索
    """
    try:
        # 获取智能对话服务
        smart_service = get_smart_conversation_service(db)

        # 解析强制模式
        force_mode = None
        if request.force_mode:
            try:
                force_mode = ConversationMode(request.force_mode)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的模式: {request.force_mode}，有效值: normal, rag_enhanced"
                )

        # 处理消息
        result = await smart_service.process_message(
            user_id=str(current_user.id),
            session_id=request.session_id,
            message=request.message,
            force_mode=force_mode
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "处理消息失败")
            )

        return SmartChatResponse(
            success=result["success"],
            content=result["content"],
            mode=result["mode"],
            message_count=result["message_count"],
            needs_network=result["needs_network"],
            rag_used=result["rag_used"],
            search_used=result["search_used"],
            sources=result.get("sources", []),
            metadata=result.get("metadata", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"智能聊天失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/session/{session_id}/status")
async def get_chat_session_status(
    session_id: str,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """获取会话状态"""
    try:
        smart_service = get_smart_conversation_service(db)
        status = await smart_service.get_session_status(
            user_id=str(current_user.id),
            session_id=session_id
        )
        return status
    except Exception as e:
        logger.error(f"获取会话状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SwitchModeRequest(BaseModel):
    """切换模式请求"""
    mode: str  # "normal" 或 "rag_enhanced"


@router.post("/chat/session/{session_id}/switch-mode")
async def switch_chat_mode(
    session_id: str,
    request: SwitchModeRequest,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """手动切换对话模式"""
    try:
        # 验证模式
        try:
            mode = ConversationMode(request.mode)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的模式: {request.mode}，有效值: normal, rag_enhanced"
            )

        smart_service = get_smart_conversation_service(db)
        result = await smart_service.switch_mode(
            user_id=str(current_user.id),
            session_id=session_id,
            mode=mode
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换模式失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# TODO: 流式聊天功能需要重新实现
# from src.services.chat_stream_service import router as stream_router
# router.include_router(stream_router)