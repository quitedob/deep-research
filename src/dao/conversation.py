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

from src.sqlmodel.models import (
    ConversationSession,
    ConversationMessage,
    User,
    MemorySummary,
    MemoryKeypoint,
    MemoryIndex,
    ConversationSnapshot,
    ModeSwitchHistory,
    PerformanceMetric,
    AgentScopeSession
)


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

    # === AgentScope 增强功能 ===

    async def update_session_enhanced_fields(
        self,
        *,
        session_id: str,
        user_id: str,
        message_count: Optional[int] = None,
        conversation_mode: Optional[str] = None,
        rag_status: Optional[str] = None,
        enable_clarification: Optional[bool] = None,
        clarification_rounds: Optional[int] = None,
        max_clarification_rounds: Optional[int] = None,
        enable_long_term_memory: Optional[bool] = None,
        memory_summary: Optional[str] = None,
        total_tokens: Optional[int] = None,
        total_cost: Optional[float] = None,
        average_response_time: Optional[float] = None,
        metadata_: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新会话的增强字段"""
        stmt = select(ConversationSession).where(
            ConversationSession.id == session_id,
            ConversationSession.user_id == user_id
        )
        result = await self.session.execute(stmt)
        session_obj = result.scalar_one_or_none()

        if not session_obj:
            return False

        # 更新字段
        if message_count is not None:
            session_obj.message_count = message_count
        if conversation_mode is not None:
            session_obj.conversation_mode = conversation_mode
        if rag_status is not None:
            session_obj.rag_status = rag_status
        if enable_clarification is not None:
            session_obj.enable_clarification = enable_clarification
        if clarification_rounds is not None:
            session_obj.clarification_rounds = clarification_rounds
        if max_clarification_rounds is not None:
            session_obj.max_clarification_rounds = max_clarification_rounds
        if enable_long_term_memory is not None:
            session_obj.enable_long_term_memory = enable_long_term_memory
        if memory_summary is not None:
            session_obj.memory_summary = memory_summary
        if total_tokens is not None:
            session_obj.total_tokens = total_tokens
        if total_cost is not None:
            session_obj.total_cost = total_cost
        if average_response_time is not None:
            session_obj.average_response_time = average_response_time
        if metadata_ is not None:
            session_obj.metadata_ = metadata_

        return True

    async def add_message_enhanced(
        self,
        *,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        message_type: str = "text",
        token_count: Optional[int] = None,
        cost: Optional[float] = None,
        response_time: Optional[float] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None,
        is_clarification_question: bool = False,
        clarification_round: Optional[int] = None,
        reasoning_steps: Optional[List[Dict[str, Any]]] = None,
        confidence_score: Optional[float] = None,
        memory_importance: Optional[float] = None,
        memory_tags: Optional[List[str]] = None,
        metadata_: Optional[Dict[str, Any]] = None
    ) -> Optional[ConversationMessage]:
        """添加增强的消息到对话会话"""
        # 先验证会话存在且属于用户
        session_obj = await self.get_session_by_id(session_id=session_id, user_id=user_id)
        if not session_obj:
            return None

        # 创建增强的消息
        message_obj = ConversationMessage(
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            token_count=token_count,
            cost=cost,
            response_time=response_time,
            tool_calls=tool_calls,
            tool_results=tool_results,
            is_clarification_question=is_clarification_question,
            clarification_round=clarification_round,
            reasoning_steps=reasoning_steps,
            confidence_score=confidence_score,
            memory_importance=memory_importance,
            memory_tags=memory_tags,
            metadata_=metadata_
        )
        self.session.add(message_obj)

        # 更新会话统计信息
        session_obj.message_count += 1
        session_obj.updated_at = datetime.utcnow()

        # 更新最后消息
        if role == "user":
            session_obj.last_message = content[:100]

        # 更新性能指标
        if token_count is not None:
            session_obj.total_tokens += token_count
        if cost is not None:
            session_obj.total_cost += cost
        if response_time is not None:
            # 计算新的平均响应时间
            current_count = session_obj.message_count
            current_avg = session_obj.average_response_time
            session_obj.average_response_time = (current_avg * (current_count - 1) + response_time) / current_count

        return message_obj

    async def get_sessions_by_mode(
        self,
        *,
        user_id: str,
        conversation_mode: str,
        limit: int = 20
    ) -> List[ConversationSession]:
        """根据对话模式获取会话"""
        stmt = select(ConversationSession).where(
            ConversationSession.user_id == user_id,
            ConversationSession.conversation_mode == conversation_mode
        ).order_by(desc(ConversationSession.updated_at)).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_sessions_with_rag_enabled(
        self,
        *,
        user_id: str,
        limit: int = 20
    ) -> List[ConversationSession]:
        """获取启用RAG的会话"""
        stmt = select(ConversationSession).where(
            ConversationSession.user_id == user_id,
            ConversationSession.rag_status.in_(["enabled", "active"])
        ).order_by(desc(ConversationSession.updated_at)).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    # === 长期记忆相关方法 ===

    async def create_memory_summary(
        self,
        *,
        session_id: str,
        user_id: str,
        summary_text: str,
        key_points: Optional[List[str]] = None,
        time_range_start: Optional[datetime] = None,
        time_range_end: Optional[datetime] = None
    ) -> MemorySummary:
        """创建记忆摘要"""
        summary_obj = MemorySummary(
            session_id=session_id,
            user_id=user_id,
            summary_text=summary_text,
            key_points=key_points,
            time_range_start=time_range_start,
            time_range_end=time_range_end
        )
        self.session.add(summary_obj)
        await self.session.flush()
        return summary_obj

    async def get_memory_summaries_by_user(
        self,
        *,
        user_id: str,
        limit: int = 10
    ) -> List[MemorySummary]:
        """获取用户的记忆摘要"""
        stmt = select(MemorySummary).where(
            MemorySummary.user_id == user_id
        ).order_by(desc(MemorySummary.created_at)).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add_memory_keypoint(
        self,
        *,
        session_id: str,
        user_id: str,
        keypoint_text: str,
        importance_score: float = 0.5,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> MemoryKeypoint:
        """添加记忆关键点"""
        keypoint_obj = MemoryKeypoint(
            session_id=session_id,
            user_id=user_id,
            keypoint_text=keypoint_text,
            importance_score=importance_score,
            category=category,
            tags=tags
        )
        self.session.add(keypoint_obj)
        await self.session.flush()
        return keypoint_obj

    async def get_memory_keypoints(
        self,
        *,
        user_id: str,
        category: Optional[str] = None,
        min_importance: float = 0.0,
        limit: int = 20
    ) -> List[MemoryKeypoint]:
        """获取记忆关键点"""
        stmt = select(MemoryKeypoint).where(
            MemoryKeypoint.user_id == user_id,
            MemoryKeypoint.importance_score >= min_importance
        )

        if category:
            stmt = stmt.where(MemoryKeypoint.category == category)

        stmt = stmt.order_by(desc(MemoryKeypoint.importance_score)).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    # === 监控数据相关方法 ===

    async def create_conversation_snapshot(
        self,
        *,
        session_id: str,
        user_id: str,
        snapshot_type: str,
        state_data: Dict[str, Any],
        performance_metrics: Optional[Dict[str, Any]] = None
    ) -> ConversationSnapshot:
        """创建对话快照"""
        snapshot_obj = ConversationSnapshot(
            session_id=session_id,
            user_id=user_id,
            snapshot_type=snapshot_type,
            state_data=state_data,
            performance_metrics=performance_metrics
        )
        self.session.add(snapshot_obj)
        await self.session.flush()
        return snapshot_obj

    async def record_mode_switch(
        self,
        *,
        session_id: str,
        user_id: str,
        from_mode: str,
        to_mode: str,
        trigger_reason: Optional[str] = None,
        context_info: Optional[Dict[str, Any]] = None
    ) -> ModeSwitchHistory:
        """记录模式切换"""
        switch_obj = ModeSwitchHistory(
            session_id=session_id,
            user_id=user_id,
            from_mode=from_mode,
            to_mode=to_mode,
            trigger_reason=trigger_reason,
            context_info=context_info
        )
        self.session.add(switch_obj)
        await self.session.flush()
        return switch_obj

    async def record_performance_metric(
        self,
        *,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metric_type: str,
        metric_value: float,
        metric_unit: str,
        context_info: Optional[Dict[str, Any]] = None
    ) -> PerformanceMetric:
        """记录性能指标"""
        metric_obj = PerformanceMetric(
            session_id=session_id,
            user_id=user_id,
            metric_type=metric_type,
            metric_value=metric_value,
            metric_unit=metric_unit,
            context_info=context_info
        )
        self.session.add(metric_obj)
        await self.session.flush()
        return metric_obj

    # === AgentScope 会话管理 ===

    async def create_agentscope_session(
        self,
        *,
        session_id: str,
        user_id: str,
        agent_type: str,
        session_data: Dict[str, Any]
    ) -> AgentScopeSession:
        """创建 AgentScope 会话"""
        session_obj = AgentScopeSession(
            session_id=session_id,
            user_id=user_id,
            agent_type=agent_type,
            session_data=session_data,
            is_active=True
        )
        self.session.add(session_obj)
        await self.session.flush()
        return session_obj

    async def get_agentscope_session(
        self,
        *,
        session_id: str,
        user_id: str
    ) -> Optional[AgentScopeSession]:
        """获取 AgentScope 会话"""
        stmt = select(AgentScopeSession).where(
            AgentScopeSession.session_id == session_id,
            AgentScopeSession.user_id == user_id,
            AgentScopeSession.is_active == True
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_agentscope_session_data(
        self,
        *,
        session_id: str,
        user_id: str,
        session_data: Dict[str, Any]
    ) -> bool:
        """更新 AgentScope 会话数据"""
        stmt = select(AgentScopeSession).where(
            AgentScopeSession.session_id == session_id,
            AgentScopeSession.user_id == user_id,
            AgentScopeSession.is_active == True
        )
        result = await self.session.execute(stmt)
        session_obj = result.scalar_one_or_none()

        if session_obj:
            session_obj.session_data = session_data
            return True
        return False

    async def deactivate_agentscope_session(
        self,
        *,
        session_id: str,
        user_id: str
    ) -> bool:
        """停用 AgentScope 会话"""
        stmt = select(AgentScopeSession).where(
            AgentScopeSession.session_id == session_id,
            AgentScopeSession.user_id == user_id
        )
        result = await self.session.execute(stmt)
        session_obj = result.scalar_one_or_none()

        if session_obj:
            session_obj.is_active = False
            return True
        return False
