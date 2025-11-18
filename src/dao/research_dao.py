#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
研究数据访问对象
处理研究会话、发现和引用的数据库操作
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from src.dao.base import BaseDAO


class ResearchDAO(BaseDAO):
    """
    研究数据访问对象
    管理研究会话、发现、引用等数据的持久化
    """

    async def create_research_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> str:
        """
        创建新的研究会话

        Args:
            session_id: 会话ID
            user_id: 用户ID
            title: 会话标题

        Returns:
            会话ID
        """
        query = """
        INSERT INTO research_sessions (
            id, user_id, title, status, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (id) DO UPDATE SET
            updated_at = EXCLUDED.updated_at
        """

        await self.execute_query(
            query,
            (
                session_id,
                user_id,
                title or f"研究会话_{session_id[:8]}",
                "active",
                datetime.now(),
                datetime.now()
            )
        )

        return session_id

    async def get_research_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取研究会话信息

        Args:
            session_id: 会话ID

        Returns:
            会话信息字典，如果不存在返回None
        """
        query = """
        SELECT * FROM research_sessions
        WHERE id = $1
        """

        result = await self.fetch_one(query, (session_id,))
        return result

    async def update_session_status(
        self,
        session_id: str,
        status: str,
        ended_at: Optional[datetime] = None
    ) -> None:
        """
        更新会话状态

        Args:
            session_id: 会话ID
            status: 新状态
            ended_at: 结束时间
        """
        query = """
        UPDATE research_sessions
        SET status = $2,
            ended_at = COALESCE($3, ended_at),
            updated_at = $4
        WHERE id = $1
        """

        await self.execute_query(
            query,
            (session_id, status, ended_at, datetime.now())
        )

    async def add_research_finding(
        self,
        session_id: str,
        source_type: str,
        source_url: str,
        content: str,
        relevance_score: float = 0.8,
        created_at: Optional[datetime] = None
    ) -> str:
        """
        添加研究发现

        Args:
            session_id: 会话ID
            source_type: 来源类型
            source_url: 来源URL
            content: 研究内容
            relevance_score: 相关性评分
            created_at: 创建时间

        Returns:
            发现ID
        """
        query = """
        INSERT INTO research_findings (
            session_id, source_type, source_url, content,
            relevance_score, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
        """

        result = await self.fetch_one(
            query,
            (
                session_id,
                source_type,
                source_url,
                content,
                relevance_score,
                created_at or datetime.now()
            )
        )

        return result["id"] if result else None

    async def get_research_findings(
        self,
        session_id: str,
        source_type: Optional[str] = None,
        min_relevance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        获取研究发现

        Args:
            session_id: 会话ID
            source_type: 过滤来源类型
            min_relevance: 最低相关性评分

        Returns:
            研究发现列表
        """
        query = """
        SELECT * FROM research_findings
        WHERE session_id = $1
        AND relevance_score >= $2
        """
        params = [session_id, min_relevance]

        if source_type:
            query += " AND source_type = $3"
            params.append(source_type)

        query += " ORDER BY relevance_score DESC, created_at DESC"

        return await self.fetch_all(query, tuple(params))

    async def add_citation(
        self,
        session_id: str,
        title: str,
        authors: List[str],
        source_url: str,
        publication_year: Optional[int] = None,
        doi: Optional[str] = None,
        citation_type: str = "article",
        created_at: Optional[datetime] = None
    ) -> str:
        """
        添加引用

        Args:
            session_id: 会话ID
            title: 文献标题
            authors: 作者列表
            source_url: 来源URL
            publication_year: 发表年份
            doi: DOI标识符
            citation_type: 引用类型
            created_at: 创建时间

        Returns:
            引用ID
        """
        query = """
        INSERT INTO research_citations (
            session_id, title, authors, source_url,
            publication_year, doi, citation_type, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id
        """

        result = await self.fetch_one(
            query,
            (
                session_id,
                title,
                json.dumps(authors),
                source_url,
                publication_year,
                doi,
                citation_type,
                created_at or datetime.now()
            )
        )

        return result["id"] if result else None

    async def get_session_citations(self, session_id: str) -> List[Dict[str, Any]]:
        """
        获取会话的引用列表

        Args:
            session_id: 会话ID

        Returns:
            引用列表
        """
        query = """
        SELECT * FROM research_citations
        WHERE session_id = $1
        ORDER BY publication_year DESC NULLS LAST, created_at DESC
        """

        results = await self.fetch_all(query, (session_id,))

        # 解析作者JSON
        for result in results:
            if result.get("authors"):
                try:
                    result["authors"] = json.loads(result["authors"])
                except json.JSONDecodeError:
                    result["authors"] = []

        return results

    async def save_message_to_long_term(
        self,
        session_id: str,
        role: str,
        name: str,
        content: str,
        timestamp: str
    ) -> str:
        """
        保存消息到长期记忆

        Args:
            session_id: 会话ID
            role: 消息角色
            name: 消息名称
            content: 消息内容
            timestamp: 时间戳

        Returns:
            消息ID
        """
        query = """
        INSERT INTO research_memory (
            session_id, message_role, message_name,
            message_content, timestamp, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
        """

        result = await self.fetch_one(
            query,
            (
                session_id,
                role,
                name,
                content,
                timestamp,
                datetime.now()
            )
        )

        return result["id"] if result else None

    async def get_long_term_memory(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取长期记忆消息

        Args:
            session_id: 会话ID
            limit: 消息数量限制

        Returns:
            消息列表
        """
        query = """
        SELECT * FROM research_memory
        WHERE session_id = $1
        ORDER BY created_at DESC
        LIMIT $2
        """

        return await self.fetch_all(query, (session_id, limit))

    async def search_research_content(
        self,
        query: str,
        limit: int = 10,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索研究内容

        Args:
            query: 搜索查询
            limit: 结果数量限制
            session_id: 限制会话ID

        Returns:
            搜索结果列表
        """
        base_query = """
        SELECT 'finding' as content_type, id, session_id, source_type,
               content as text, relevance_score, created_at
        FROM research_findings
        WHERE to_tsvector('english', content) @@ to_tsquery('english', $1)

        UNION ALL

        SELECT 'citation' as content_type, id, session_id, title as source_type,
               title || ' ' || COALESCE(string_agg(author, ' '), '') as text,
               1.0 as relevance_score, created_at
        FROM research_citations, json_array_elements_text(cast(authors as json)) as author
        WHERE to_tsvector('english', title || ' ' || author) @@ to_tsquery('english', $1)
        GROUP BY id, session_id, title, created_at

        UNION ALL

        SELECT 'memory' as content_type, id, session_id, message_role as source_type,
               message_content as text, 0.5 as relevance_score, created_at
        FROM research_memory
        WHERE to_tsvector('english', message_content) @@ to_tsquery('english', $1)
        """

        if session_id:
            base_query += " AND session_id = $2"
            base_query += f" ORDER BY relevance_score DESC LIMIT $3"
            return await self.fetch_all(base_query, (query, session_id, limit))
        else:
            base_query += f" ORDER BY relevance_score DESC LIMIT $2"
            return await self.fetch_all(base_query, (query, limit))

    async def get_user_research_sessions(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取用户的研究会话列表

        Args:
            user_id: 用户ID
            status: 过滤状态
            limit: 结果数量限制

        Returns:
            会话列表
        """
        query = """
        SELECT rs.*,
               COUNT(DISTINCT rf.id) as findings_count,
               COUNT(DISTINCT rc.id) as citations_count
        FROM research_sessions rs
        LEFT JOIN research_findings rf ON rs.id = rf.session_id
        LEFT JOIN research_citations rc ON rs.id = rc.session_id
        WHERE rs.user_id = $1
        """

        params = [user_id]

        if status:
            query += " AND rs.status = $2"
            params.append(status)

        query += """
        GROUP BY rs.id
        ORDER BY rs.updated_at DESC
        LIMIT $""" + str(len(params) + 1)

        params.append(limit)

        return await self.fetch_all(query, tuple(params))

    async def get_research_statistics(
        self,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取研究统计信息

        Args:
            user_id: 用户ID，如果为None则获取全局统计

        Returns:
            统计信息字典
        """
        # 会话统计
        session_query = """
        SELECT
            COUNT(*) as total_sessions,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active_sessions,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_sessions
        FROM research_sessions
        """
        params = []

        if user_id:
            session_query += " WHERE user_id = $1"
            params.append(user_id)

        session_stats = await self.fetch_one(session_query, tuple(params) if params else ())

        # 发现和引用统计
        stats_query = """
        SELECT
            COUNT(DISTINCT rf.id) as total_findings,
            COUNT(DISTINCT rc.id) as total_citations,
            AVG(rf.relevance_score) as avg_relevance_score
        FROM research_sessions rs
        LEFT JOIN research_findings rf ON rs.id = rf.session_id
        LEFT JOIN research_citations rc ON rs.id = rc.session_id
        """
        params = []

        if user_id:
            stats_query += " WHERE rs.user_id = $1"
            params.append(user_id)

        content_stats = await self.fetch_one(stats_query, tuple(params) if params else ())

        # 来源类型统计
        source_query = """
        SELECT source_type, COUNT(*) as count
        FROM research_findings rf
        JOIN research_sessions rs ON rf.session_id = rs.id
        """
        params = []

        if user_id:
            source_query += " WHERE rs.user_id = $1"
            params.append(user_id)

        source_query += " GROUP BY source_type ORDER BY count DESC"
        source_stats = await self.fetch_all(source_query, tuple(params) if params else ())

        return {
            "sessions": session_stats or {},
            "content": content_stats or {},
            "sources": source_stats or [],
            "timestamp": datetime.now().isoformat()
        }

    async def delete_research_session(self, session_id: str) -> None:
        """
        删除研究会话及相关数据

        Args:
            session_id: 会话ID
        """
        # 注意：参数必须作为元组传递
        await self.execute_query("DELETE FROM research_memory WHERE session_id = $1", (session_id,))
        await self.execute_query("DELETE FROM research_citations WHERE session_id = $1", (session_id,))
        await self.execute_query("DELETE FROM research_findings WHERE session_id = $1", (session_id,))
        await self.execute_query("DELETE FROM research_sessions WHERE id = $1", (session_id,))

    async def export_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        导出会话的所有数据

        Args:
            session_id: 会话ID

        Returns:
            会话数据字典
        """
        # 获取会话信息
        session_info = await self.get_research_session(session_id)
        if not session_info:
            return None

        # 转换 datetime 对象为字符串
        if session_info.get('created_at') and isinstance(session_info['created_at'], datetime):
            session_info['created_at'] = session_info['created_at'].isoformat()
        if session_info.get('updated_at') and isinstance(session_info['updated_at'], datetime):
            session_info['updated_at'] = session_info['updated_at'].isoformat()
        if session_info.get('ended_at') and isinstance(session_info['ended_at'], datetime):
            session_info['ended_at'] = session_info['ended_at'].isoformat()
        
        # 确保必需字段存在
        if 'findings_count' not in session_info:
            session_info['findings_count'] = 0
        if 'citations_count' not in session_info:
            session_info['citations_count'] = 0

        # 获取研究发现
        findings = await self.get_research_findings(session_id)

        # 获取引用
        citations = await self.get_session_citations(session_id)

        # 获取长期记忆
        memory = await self.get_long_term_memory(session_id, 1000)
        
        # 转换记忆中的 datetime
        for msg in memory:
            if msg.get('timestamp') and isinstance(msg['timestamp'], datetime):
                msg['timestamp'] = msg['timestamp'].isoformat()

        return {
            "session_info": session_info,
            "findings": findings,
            "citations": citations,
            "memory": memory,
            "exported_at": datetime.now().isoformat()
        }