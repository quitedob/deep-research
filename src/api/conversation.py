# -*- coding: utf-8 -*-
"""
对话记忆管理API：支持用户对话历史记录和记忆功能。
"""

from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.core.db import get_db_session
from src.sqlmodel.models import User
from src.services.auth_service import get_current_user
from src.services.conversation_service import ConversationService
from src.config.loader.config_loader import get_settings
from src.api.errors import create_error_response, ErrorCodes, handle_database_error, handle_not_found_error

router = APIRouter(prefix="/conversation", tags=["conversation"])

settings = get_settings()


class ConversationMessage(BaseModel):
    """对话消息模型"""
    role: str  # "user" 或 "assistant"
    content: str
    timestamp: datetime


class ConversationSession(BaseModel):
    """对话会话模型"""
    id: str
    title: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message: Optional[str] = None


class ConversationDetail(BaseModel):
    """对话详情模型"""
    id: str
    title: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    messages: List[ConversationMessage]


class CreateConversationRequest(BaseModel):
    """创建对话请求"""
    title: str
    initial_message: str


class AddMessageRequest(BaseModel):
    """添加消息请求"""
    role: str
    content: str


@router.get("/sessions", response_model=List[ConversationSession])
async def list_conversation_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    page: int = 1,
    page_size: int = 20
):
    """
    获取用户的对话会话列表 - 通过ConversationService处理业务逻辑
    """
    try:
        conversation_service = ConversationService(db)

        # 计算偏移量
        skip = (page - 1) * page_size

        # 通过服务层获取对话会话
        result = await conversation_service.get_user_conversations(
            user_id=str(current_user.id),
            skip=skip,
            limit=page_size
        )

        # 构建响应数据
        result_sessions = []
        for conv in result.get("conversations", []):
            result_sessions.append(ConversationSession(
                id=conv["session_id"],
                title=conv["title"],
                user_id=str(current_user.id),
                created_at=conv["created_at"],
                updated_at=conv["updated_at"],
                message_count=conv.get("message_count", 0),
                last_message=""  # 可以在服务层扩展获取最后消息
            ))

        return result_sessions

    except Exception as e:
        return handle_database_error(e, "获取对话会话列表")


@router.post("/sessions", response_model=ConversationSession)
async def create_conversation_session(
    request: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    创建新的对话会话 - 通过ConversationService处理业务逻辑
    """
    try:
        conversation_service = ConversationService(db)

        # 通过服务层创建对话会话
        result = await conversation_service.create_conversation(
            user_id=str(current_user.id),
            title=request.title
        )

        if not result.get("success"):
            return handle_database_error(
                Exception(result.get("error", "创建对话会话失败")),
                "创建对话会话"
            )

        # 如果有初始消息，添加到会话中
        if request.initial_message:
            await conversation_service.add_message(
                user_id=str(current_user.id),
                session_id=result["session_id"],
                role="user",
                content=request.initial_message
            )

        # 构建响应对象
        return ConversationSession(
            id=result["session_id"],
            title=result["title"],
            user_id=str(current_user.id),
            created_at=result["created_at"],
            updated_at=result["created_at"],  # 刚创建时updated_at等于created_at
            message_count=1 if request.initial_message else 0,
            last_message=request.initial_message or ""
        )

    except Exception as e:
        return handle_database_error(e, "创建对话会话")


@router.get("/sessions/{session_id}", response_model=ConversationDetail)
async def get_conversation_detail(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取对话详情 - 通过ConversationService处理业务逻辑
    """
    try:
        conversation_service = ConversationService(db)

        # 通过服务层获取对话详情
        session_info = await conversation_service.get_conversation(
            user_id=str(current_user.id),
            session_id=session_id
        )

        if not session_info:
            return handle_not_found_error("对话会话", session_id)

        # 获取对话消息
        messages_result = await conversation_service.get_conversation_messages(
            user_id=str(current_user.id),
            session_id=session_id
        )

        # 构建消息响应
        response_messages = []
        for msg in messages_result.get("messages", []):
            response_messages.append(ConversationMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["created_at"]
            ))

        # 构建响应对象
        conversation = ConversationDetail(
            id=session_id,
            title=session_info["title"],
            user_id=str(current_user.id),
            created_at=session_info["created_at"],
            updated_at=session_info["updated_at"],
            messages=response_messages
        )

        return conversation

    except Exception as e:
        return handle_database_error(e, "获取对话详情")


@router.post("/sessions/{session_id}/messages")
async def add_message_to_conversation(
    session_id: str,
    request: AddMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    向对话会话添加消息 - 通过ConversationService处理业务逻辑
    """
    try:
        conversation_service = ConversationService(db)

        # 验证消息角色
        valid_roles = ["user", "assistant", "system"]
        if request.role not in valid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"无效的消息角色。有效选项: {', '.join(valid_roles)}"
            )

        # 通过服务层添加消息
        result = await conversation_service.add_message(
            user_id=str(current_user.id),
            session_id=session_id,
            role=request.role,
            content=request.content
        )

        if not result.get("success"):
            error_msg = result.get("error", "添加消息失败")
            if "不存在或无权限访问" in error_msg:
                return handle_not_found_error("对话会话", session_id)
            else:
                return handle_database_error(
                    Exception(error_msg),
                    "添加消息"
                )

        return {
            "message": result.get("message", "消息添加成功"),
            "session_id": session_id,
            "message_id": result.get("message_id")
        }

    except HTTPException:
        raise
    except Exception as e:
        return handle_database_error(e, "添加消息")


@router.delete("/sessions/{session_id}")
async def delete_conversation_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    删除对话会话 - 通过ConversationService处理业务逻辑
    """
    try:
        conversation_service = ConversationService(db)

        # 通过服务层删除对话会话
        result = await conversation_service.delete_conversation(
            user_id=str(current_user.id),
            session_id=session_id
        )

        if not result.get("success"):
            error_msg = result.get("error", "删除对话会话失败")
            if "不存在或无权限访问" in error_msg:
                return handle_not_found_error("对话会话", session_id)
            else:
                return handle_database_error(
                    Exception(error_msg),
                    "删除对话会话"
                )

        return {
            "message": result.get("message", "对话会话删除成功"),
            "session_id": session_id
        }

    except Exception as e:
        return handle_database_error(e, "删除对话会话")


@router.get("/memory/summary")
async def get_conversation_memory_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取对话记忆摘要 - 通过ConversationService处理业务逻辑
    """
    try:
        conversation_service = ConversationService(db)

        # 通过服务层获取对话统计信息
        stats = await conversation_service.get_conversation_statistics(
            user_id=str(current_user.id),
            days=30  # 默认统计30天
        )

        # 分析对话风格（简单的关键词统计）
        style_keywords = ["详细", "简洁", "专业", "友好", "条理", "清晰"]
        conversation_style = "专业且有条理"  # 默认风格

        # 获取最近活动时间（简化实现）
        last_active = None
        user_conversations = await conversation_service.get_user_conversations(
            user_id=str(current_user.id),
            skip=0,
            limit=1
        )

        if user_conversations.get("conversations"):
            last_active = user_conversations["conversations"][0]["updated_at"]

        return {
            "user_id": str(current_user.id),
            "total_conversations": stats.get("total_sessions", 0),
            "total_messages": stats.get("total_messages", 0),
            "favorite_topics": [],  # 可以在服务层扩展分析话题
            "conversation_style": conversation_style,
            "last_active": last_active.isoformat() if last_active else None
        }

    except Exception as e:
        return handle_database_error(e, "获取记忆摘要")
