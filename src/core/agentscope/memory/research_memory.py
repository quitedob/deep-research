#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
研究记忆管理
基于AgentScope的记忆系统，专门用于深度研究场景
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from agentscope.memory import InMemoryMemory, LongTermMemoryBase
from agentscope.message import Msg

from src.dao.base import BaseDAO
from src.dao.research_dao import ResearchDAO


class ResearchSessionMemory:
    """
    研究会话记忆管理器
    管理单个研究会话的短期和长期记忆
    """

    def __init__(
        self,
        session_id: str,
        research_dao: ResearchDAO,
        max_short_term_size: int = 100
    ):
        """
        初始化研究会话记忆

        Args:
            session_id: 研究会话ID
            research_dao: 研究数据访问对象
            max_short_term_size: 短期记忆最大消息数量
        """
        self.session_id = session_id
        self.research_dao = research_dao
        self.max_short_term_size = max_short_term_size

        # 短期记忆 - 存储当前会话的对话和推理过程
        self.short_memory = InMemoryMemory()

        # 记忆状态
        self.is_active = True
        self.created_at = datetime.now()
        self.last_updated = datetime.now()

    async def add_message(self, message: Msg) -> None:
        """
        添加消息到短期记忆

        Args:
            message: 要添加的消息
        """
        await self.short_memory.add(message)
        self.last_updated = datetime.now()

        # 如果短期记忆过大，将旧消息转移到长期记忆
        if len(await self.short_memory.get_memory()) > self.max_short_term_size:
            await self._transfer_to_long_term_memory()

    async def get_memory(self, limit: Optional[int] = None) -> List[Msg]:
        """
        获取短期记忆

        Args:
            limit: 返回消息数量限制

        Returns:
            消息列表
        """
        # ✅ 修复：AgentScope 的 get_memory() 不接受参数
        memory = await self.short_memory.get_memory()
        if limit and len(memory) > limit:
            return memory[-limit:]
        return memory

    async def get_memory_context(self, window_size: int = 10) -> str:
        """
        获取记忆上下文字符串

        Args:
            window_size: 上下文窗口大小

        Returns:
            格式化的记忆上下文
        """
        recent_memory = await self.get_memory(window_size)
        context_parts = []

        for msg in recent_memory:
            if msg.role == "system":
                context_parts.append(f"系统: {msg.content}")
            elif msg.role == "user":
                context_parts.append(f"用户: {msg.content}")
            elif msg.role == "assistant":
                context_parts.append(f"助手: {msg.content}")

        return "\n".join(context_parts)

    async def add_research_finding(
        self,
        source_type: str,
        source_url: str,
        content: str,
        relevance_score: float = 0.8
    ) -> str:
        """
        添加研究发现到长期记忆

        Args:
            source_type: 来源类型 (web, wiki, arxiv, image等)
            source_url: 来源URL
            content: 研究内容
            relevance_score: 相关性评分

        Returns:
            查找ID
        """
        finding_id = await self.research_dao.add_research_finding(
            session_id=self.session_id,
            source_type=source_type,
            source_url=source_url,
            content=content,
            relevance_score=relevance_score,
            created_at=datetime.now()
        )

        # 添加到短期记忆作为助手消息
        await self.add_message(Msg(
            name="research_memory",
            role="assistant",
            content=f"[研究发现 - {source_type}] {content[:200]}...",
            timestamp=datetime.now().isoformat()
        ))

        return finding_id

    async def get_research_findings(
        self,
        source_type: Optional[str] = None,
        min_relevance: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        获取研究发现

        Args:
            source_type: 过滤来源类型
            min_relevance: 最低相关性评分

        Returns:
            研究发现列表
        """
        return await self.research_dao.get_research_findings(
            session_id=self.session_id,
            source_type=source_type,
            min_relevance=min_relevance
        )

    async def add_citation(
        self,
        title: str,
        authors: List[str],
        source_url: str,
        publication_year: Optional[int] = None,
        doi: Optional[str] = None
    ) -> str:
        """
        添加引用到研究记录

        Args:
            title: 文献标题
            authors: 作者列表
            source_url: 来源URL
            publication_year: 发表年份
            doi: DOI标识符

        Returns:
            引用ID
        """
        citation_id = await self.research_dao.add_citation(
            session_id=self.session_id,
            title=title,
            authors=authors,
            source_url=source_url,
            publication_year=publication_year,
            doi=doi,
            created_at=datetime.now()
        )

        return citation_id

    async def get_citations(self) -> List[Dict[str, Any]]:
        """
        获取研究引用列表

        Returns:
            引用列表
        """
        return await self.research_dao.get_session_citations(self.session_id)

    async def _transfer_to_long_term_memory(self) -> None:
        """
        将短期记忆中的旧消息转移到长期记忆
        """
        try:
            memory = await self.short_memory.get_memory()
            if len(memory) <= self.max_short_term_size:
                return

            # 保留最新的消息，将旧消息保存到数据库
            messages_to_transfer = memory[:-self.max_short_term_size]

            for msg in messages_to_transfer:
                await self.research_dao.save_message_to_long_term(
                    session_id=self.session_id,
                    role=msg.role,
                    name=msg.name,
                    content=msg.content,
                    timestamp=msg.timestamp if hasattr(msg, 'timestamp') else datetime.now().isoformat()
                )

            # 清空短期记忆并重新添加最新消息
            self.short_memory = InMemoryMemory()
            recent_messages = memory[-self.max_short_term_size:]

            for msg in recent_messages:
                await self.short_memory.add(msg)

        except Exception as e:
            print(f"转移长期记忆时出错: {str(e)}")

    async def export_session_data(self) -> Dict[str, Any]:
        """
        导出会话数据

        Returns:
            包含所有会话数据的字典
        """
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "short_memory": [
                {
                    "role": msg.role,
                    "name": msg.name,
                    "content": msg.content,
                    "timestamp": getattr(msg, 'timestamp', datetime.now().isoformat())
                }
                for msg in await self.get_memory()
            ],
            "research_findings": await self.get_research_findings(),
            "citations": await self.get_citations()
        }

    async def clear_memory(self) -> None:
        """
        清空会话记忆
        """
        self.short_memory = InMemoryMemory()
        # 不删除长期记忆，只清空短期记忆
        self.last_updated = datetime.now()


class ResearchMemoryManager:
    """
    研究记忆管理器
    管理多个研究会话的记忆
    """

    def __init__(self, research_dao: ResearchDAO):
        """
        初始化记忆管理器

        Args:
            research_dao: 研究数据访问对象
        """
        self.research_dao = research_dao
        self.active_sessions: Dict[str, ResearchSessionMemory] = {}

    async def create_session(self, session_id: str) -> ResearchSessionMemory:
        """
        创建新的研究会话记忆

        Args:
            session_id: 会话ID

        Returns:
            研究会话记忆对象
        """
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]

        session_memory = ResearchSessionMemory(
            session_id=session_id,
            research_dao=self.research_dao
        )

        self.active_sessions[session_id] = session_memory

        # 在数据库中创建会话记录
        await self.research_dao.create_research_session(session_id)

        return session_memory

    async def get_session(self, session_id: str) -> Optional[ResearchSessionMemory]:
        """
        获取研究会话记忆

        Args:
            session_id: 会话ID

        Returns:
            研究会话记忆对象，如果不存在返回None
        """
        # 先检查活跃会话
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]

        # 尝试从数据库加载会话
        session_data = await self.research_dao.get_research_session(session_id)
        if session_data:
            session_memory = ResearchSessionMemory(
                session_id=session_id,
                research_dao=self.research_dao
            )
            self.active_sessions[session_id] = session_memory
            return session_memory

        return None

    async def close_session(self, session_id: str) -> None:
        """
        关闭研究会话

        Args:
            session_id: 会话ID
        """
        if session_id in self.active_sessions:
            # 保存会话状态到数据库
            session_memory = self.active_sessions[session_id]
            session_memory.is_active = False

            # 将短期记忆转移到长期记忆
            await session_memory._transfer_to_long_term_memory()

            # 更新数据库中的会话状态
            await self.research_dao.update_session_status(
                session_id,
                status="completed",
                ended_at=datetime.now()
            )

            del self.active_sessions[session_id]

    async def get_all_sessions(self) -> List[str]:
        """
        获取所有会话ID

        Returns:
            会话ID列表
        """
        return list(self.active_sessions.keys())

    async def search_across_sessions(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        跨会话搜索研究内容

        Args:
            query: 搜索查询
            limit: 结果数量限制

        Returns:
            搜索结果列表
        """
        return await self.research_dao.search_research_content(query, limit)

    async def cleanup_inactive_sessions(self, inactive_hours: int = 24) -> None:
        """
        清理非活跃会话

        Args:
            inactive_hours: 非活跃时间阈值（小时）
        """
        cutoff_time = datetime.now() - timedelta(hours=inactive_hours)

        for session_id, session_memory in list(self.active_sessions.items()):
            if session_memory.last_updated < cutoff_time:
                await self.close_session(session_id)
                print(f"清理非活跃会话: {session_id}")

    async def get_memory_statistics(self) -> Dict[str, Any]:
        """
        获取记忆统计信息

        Returns:
            统计信息字典
        """
        total_findings = 0
        total_citations = 0
        active_sessions = len(self.active_sessions)

        for session_memory in self.active_sessions.values():
            findings = await session_memory.get_research_findings()
            citations = await session_memory.get_citations()
            total_findings += len(findings)
            total_citations += len(citations)

        return {
            "active_sessions": active_sessions,
            "total_findings": total_findings,
            "total_citations": total_citations,
            "timestamp": datetime.now().isoformat()
        }