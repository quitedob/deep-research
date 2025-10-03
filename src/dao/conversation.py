# -*- coding: utf-8 -*-
"""
对话数据访问对象（DAO）
负责对话会话和消息的数据库操作
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.sqlmodel.models import ConversationSession, ConversationMessage, User


class ConversationDAO:
    """对话会话数据访问对象"""

    def __init__(self, session: AsyncSession):
        """初始化DAO"""
        self.session = session

    async def create_session(
        self,
        *,
        user_id: str,
        title: str,
        initial_message: Optional[str] = None
    ) -> ConversationSession:
        """创建对话会话"""
        session_obj = ConversationSession(
            user_id=user_id,
            title=title
        )
        self.session.add(session_obj)
        await self.session.flush()  # 获取ID但不提交

        # 如果有初始消息，创建第一条消息
        if initial_message:
            message_obj = ConversationMessage(
                session_id=session_obj.id,
                role="user",
                content=initial_message,
                message_type="text"
            )
            self.session.add(message_obj)

        return session_obj

    async def get_session_by_id(self, *, session_id: str, user_id: str) -> Optional[ConversationSession]:
        """根据ID获取对话会话"""
        stmt = select(ConversationSession).where(
            ConversationSession.id == session_id,
            ConversationSession.user_id == user_id
        ).options(selectinload(ConversationSession.messages))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_sessions_by_user(
        self,
        *,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        include_messages: bool = False
    ) -> List[ConversationSession]:
        """获取用户的所有对话会话"""
        offset = (page - 1) * page_size

        # 构建查询语句
        stmt = select(ConversationSession).where(
            ConversationSession.user_id == user_id
        ).order_by(desc(ConversationSession.updated_at)).offset(offset).limit(page_size)

        # 如果需要包含消息
        if include_messages:
            stmt = stmt.options(selectinload(ConversationSession.messages))

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_session_count_by_user(self, *, user_id: str) -> int:
        """获取用户对话会话总数"""
        stmt = select(func.count()).select_from(ConversationSession).where(
            ConversationSession.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar()

    async def update_session_title(self, *, session_id: str, user_id: str, title: str) -> bool:
        """更新对话会话标题"""
        stmt = select(ConversationSession).where(
            ConversationSession.id == session_id,
            ConversationSession.user_id == user_id
        )
        result = await self.session.execute(stmt)
        session_obj = result.scalar_one_or_none()

        if session_obj:
            session_obj.title = title
            return True
        return False

    async def delete_session(self, *, session_id: str, user_id: str) -> bool:
        """删除对话会话"""
        stmt = select(ConversationSession).where(
            ConversationSession.id == session_id,
            ConversationSession.user_id == user_id
        )
        result = await self.session.execute(stmt)
        session_obj = result.scalar_one_or_none()

        if session_obj:
            await self.session.delete(session_obj)
            return True
        return False

    async def add_message(
        self,
        *,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[dict] = None
    ) -> Optional[ConversationMessage]:
        """添加消息到对话会话"""
        # 先验证会话存在且属于用户
        session_obj = await self.get_session_by_id(session_id=session_id, user_id=user_id)
        if not session_obj:
            return None

        # 创建消息
        message_obj = ConversationMessage(
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            metadata_=metadata
        )
        self.session.add(message_obj)

        # 更新会话的更新时间和最后消息
        session_obj.updated_at = datetime.utcnow()
        if role == "user":
            session_obj.last_message = content[:100]  # 取前100个字符作为摘要

        return message_obj

    async def get_messages_by_session(
        self,
        *,
        session_id: str,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[ConversationMessage]:
        """获取会话中的所有消息"""
        # 先验证会话存在且属于用户
        session_obj = await self.get_session_by_id(session_id=session_id, user_id=user_id)
        if not session_obj:
            return []

        stmt = select(ConversationMessage).where(
            ConversationMessage.session_id == session_id
        ).order_by(ConversationMessage.created_at)

        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_recent_sessions(
        self,
        *,
        user_id: str,
        limit: int = 10
    ) -> List[ConversationSession]:
        """获取用户最近的对话会话"""
        stmt = select(ConversationSession).where(
            ConversationSession.user_id == user_id
        ).order_by(desc(ConversationSession.updated_at)).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search_sessions(
        self,
        *,
        user_id: str,
        query: str,
        limit: int = 20
    ) -> List[ConversationSession]:
        """搜索用户的对话会话"""
        # 这里可以实现基于标题或消息内容的搜索
        # 暂时只搜索标题
        stmt = select(ConversationSession).where(
            ConversationSession.user_id == user_id,
            ConversationSession.title.ilike(f"%{query}%")
        ).order_by(desc(ConversationSession.updated_at)).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()
