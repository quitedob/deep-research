# -*- coding: utf-8 -*-
"""
会话管理服务
提供会话创建、管理、消息存储等功能
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional

from .base_service import BaseService
from ..core.security import sanitize_model_output

class SessionService(BaseService):
    """会话管理服务"""

    def __init__(self):
        super().__init__()
        self._lock = asyncio.Lock()
        self._chat_sessions: Dict[str, List[Dict[str, str]]] = {}
        self._research_reports: Dict[str, Dict[str, Any]] = {}

    async def ensure_session(self, session_id: Optional[str] = None) -> str:
        """
        确保会话存在，如果不存在则创建新会话

        Args:
            session_id: 可选的会话ID

        Returns:
            会话ID
        """
        sid = session_id or uuid.uuid4().hex
        async with self._lock:
            if sid not in self._chat_sessions:
                self._chat_sessions[sid] = []
                await self.log_operation("session_created", {"session_id": sid})
        return sid

    async def list_sessions(self) -> List[str]:
        """
        获取所有会话ID列表

        Returns:
            会话ID列表
        """
        async with self._lock:
            return list(self._chat_sessions.keys())

    async def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        """
        获取指定会话的消息历史

        Args:
            session_id: 会话ID

        Returns:
            消息列表
        """
        async with self._lock:
            messages = self._chat_sessions.get(session_id, [])
            await self.log_operation("messages_retrieved", {
                "session_id": session_id,
                "message_count": len(messages)
            })
            return list(messages)

    async def append_message(self, session_id: str, role: str, content: str) -> None:
        """
        向会话添加新消息

        Args:
            session_id: 会话ID
            role: 消息角色（user/assistant/system）
            content: 消息内容
        """
        # 清理输出内容
        if role == "assistant":
            content = sanitize_model_output(content)

        message = {"role": role, "content": content}

        async with self._lock:
            self._chat_sessions.setdefault(session_id, []).append(message)
            await self.log_operation("message_added", {
                "session_id": session_id,
                "role": role,
                "content_length": len(content)
            })

    async def clear_session(self, session_id: str) -> bool:
        """
        清空指定会话的消息

        Args:
            session_id: 会话ID

        Returns:
            是否成功清空
        """
        async with self._lock:
            if session_id in self._chat_sessions:
                self._chat_sessions[session_id] = []
                await self.log_operation("session_cleared", {"session_id": session_id})
                return True
            return False

    async def delete_session(self, session_id: str) -> bool:
        """
        删除指定会话

        Args:
            session_id: 会话ID

        Returns:
            是否成功删除
        """
        async with self._lock:
            deleted = False
            if session_id in self._chat_sessions:
                del self._chat_sessions[session_id]
                deleted = True

            if session_id in self._research_reports:
                del self._research_reports[session_id]
                deleted = True

            if deleted:
                await self.log_operation("session_deleted", {"session_id": session_id})

            return deleted

    async def clear_all_sessions(self) -> None:
        """清空所有会话"""
        async with self._lock:
            session_count = len(self._chat_sessions)
            self._chat_sessions.clear()
            self._research_reports.clear()
            await self.log_operation("all_sessions_cleared", {
                "cleared_sessions": session_count
            })

    # Research results management
    async def set_research_report(self, session_id: str, query: str, report: str) -> None:
        """
        保存研究报告到会话

        Args:
            session_id: 会话ID
            query: 研究查询
            report: 研究报告内容
        """
        # 清理报告内容
        report = sanitize_model_output(report)

        async with self._lock:
            self._research_reports[session_id] = {
                "session_id": session_id,
                "query": query,
                "report": report,
                "created_at": self.get_current_time()
            }
            await self.log_operation("research_report_saved", {
                "session_id": session_id,
                "query_length": len(query),
                "report_length": len(report)
            })

    async def get_research_report(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话的研究报告

        Args:
            session_id: 会话ID

        Returns:
            研究报告数据，如果不存在则返回None
        """
        async with self._lock:
            report = self._research_reports.get(session_id)
            if report:
                await self.log_operation("research_report_retrieved", {
                    "session_id": session_id
                })
            return report

    async def get_session_stats(self) -> Dict[str, Any]:
        """
        获取会话统计信息

        Returns:
            统计信息字典
        """
        async with self._lock:
            total_sessions = len(self._chat_sessions)
            total_messages = sum(len(messages) for messages in self._chat_sessions.values())
            total_reports = len(self._research_reports)

            return {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "total_research_reports": total_reports,
                "average_messages_per_session": total_messages / total_sessions if total_sessions > 0 else 0
            }

# 创建全局会话服务实例
session_service = SessionService()

# 为了向后兼容，保留原有的store实例
store = session_service

__all__ = [
    'SessionService',
    'session_service',
    'store'  # 向后兼容
]