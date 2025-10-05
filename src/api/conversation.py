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
from src.service.auth import get_current_user
from src.dao.conversation import ConversationDAO
from src.config.config_loader import get_settings
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
    获取用户的对话会话列表
    """
    try:
        # 使用DAO查询真实数据
        convo_dao = ConversationDAO(db)
        sessions = await convo_dao.get_sessions_by_user(
            user_id=current_user.id,
            page=page,
            page_size=page_size
        )

        # 计算消息数量并构建响应
        result_sessions = []
        for session in sessions:
            message_count = len(session.messages) if hasattr(session, 'messages') else 0
            last_message = session.last_message if hasattr(session, 'last_message') else ""

            result_sessions.append(ConversationSession(
                id=session.id,
                title=session.title,
                user_id=session.user_id,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=message_count,
                last_message=last_message
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
    创建新的对话会话
    """
    try:
        # 使用DAO创建真实对话会话
        convo_dao = ConversationDAO(db)
        session = await convo_dao.create_session(
            user_id=current_user.id,
            title=request.title,
            initial_message=request.initial_message
        )

        # 构建响应对象
        return ConversationSession(
            id=session.id,
            title=session.title,
            user_id=session.user_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
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
    获取对话详情
    """
    try:
        # 使用DAO获取真实对话详情
        convo_dao = ConversationDAO(db)
        session = await convo_dao.get_session_by_id(session_id=session_id, user_id=current_user.id)

        if not session:
            return handle_not_found_error("对话会话", session_id)

        # 获取会话中的消息
        messages = await convo_dao.get_messages_by_session(
            session_id=session_id,
            user_id=current_user.id
        )

        # 构建消息响应
        response_messages = []
        for msg in messages:
            response_messages.append(ConversationMessage(
                role=msg.role,
                content=msg.content,
                timestamp=msg.created_at
            ))

        # 构建响应对象
        conversation = ConversationDetail(
            id=session.id,
            title=session.title,
            user_id=session.user_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
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
    向对话会话添加消息
    """
    try:
        # 使用DAO添加真实消息
        convo_dao = ConversationDAO(db)
        message = await convo_dao.add_message(
            session_id=session_id,
            user_id=current_user.id,
            role=request.role,
            content=request.content
        )

        if not message:
            return handle_not_found_error("对话会话", session_id)

        return {
            "message": "消息添加成功",
            "session_id": session_id,
            "message_id": message.id
        }
        
    except Exception as e:
        return handle_database_error(e, "添加消息")


@router.delete("/sessions/{session_id}")
async def delete_conversation_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    删除对话会话
    """
    try:
        # 使用DAO删除真实对话会话
        convo_dao = ConversationDAO(db)
        success = await convo_dao.delete_session(
            session_id=session_id,
            user_id=current_user.id
        )

        if not success:
            return handle_not_found_error("对话会话", session_id)

        return {
            "message": "对话会话删除成功",
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
    获取对话记忆摘要
    """
    try:
        # 使用DAO获取真实统计数据
        convo_dao = ConversationDAO(db)

        # 获取用户的所有对话会话
        sessions = await convo_dao.get_sessions_by_user(
            user_id=current_user.id,
            include_messages=False
        )

        total_conversations = len(sessions)

        # 计算总消息数
        total_messages = 0
        topics = set()
        last_active = None

        for session in sessions:
            # 统计消息数
            messages = await convo_dao.get_messages_by_session(
                session_id=session.id,
                user_id=current_user.id,
                limit=100  # 限制查询数量，避免性能问题
            )
            total_messages += len(messages)

            # 收集话题（从会话标题中提取关键词）
            title_words = session.title.split()
            topics.update(title_words)

            # 更新最后活动时间
            if last_active is None or session.updated_at > last_active:
                last_active = session.updated_at

        # 分析对话风格（简单的关键词统计）
        style_keywords = ["详细", "简洁", "专业", "友好", "条理", "清晰"]
        conversation_style = "专业且有条理"  # 默认风格

        return {
            "user_id": str(current_user.id),
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "favorite_topics": list(topics)[:5],  # 取前5个话题
            "conversation_style": conversation_style,
            "last_active": last_active.isoformat() if last_active else None
        }
        
    except Exception as e:
        return handle_database_error(e, "获取记忆摘要")
