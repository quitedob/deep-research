# -*- coding: utf-8 -*-
"""
ConversationService：对话管理业务逻辑服务
提供对话会话管理、消息处理、历史记录等功能
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from .base_service import BaseService
from src.dao import ConversationDAO
from src.sqlmodel.models import ConversationSession, ConversationMessage, User
from src.config.logging import get_logger

logger = get_logger("conversation_service")


class ConversationService(BaseService[ConversationSession]):
    """对话管理服务类"""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.conversation_dao = ConversationDAO(session)

    async def create_conversation(
        self,
        user_id: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建新的对话会话

        Args:
            user_id: 用户ID
            title: 对话标题（可选）

        Returns:
            创建的对话会话信息
        """
        try:
            await self.begin_transaction()

            # 生成会话ID
            session_id = str(uuid.uuid4())

            # 生成默认标题
            if not title:
                title = f"对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            # 创建对话会话
            session = ConversationSession(
                id=session_id,
                user_id=user_id,
                title=title,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.session.add(session)
            await self.session.commit()
            await self.session.refresh(session)

            await self.commit_transaction()

            await self.log_operation(
                user_id=user_id,
                operation="conversation_created",
                details={
                    "session_id": session_id,
                    "title": title
                }
            )

            return {
                "success": True,
                "session_id": session_id,
                "title": session.title,
                "created_at": session.created_at,
                "message": "对话会话创建成功"
            }

        except Exception as e:
            await self.rollback_transaction()
            logger.error(f"创建对话会话失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "创建对话会话失败"
            }

    async def get_conversation(
        self,
        user_id: str,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取对话会话信息

        Args:
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            对话会话信息
        """
        try:
            session = await self.conversation_dao.get_by_id(session_id)

            if not session or session.user_id != user_id:
                return None

            return {
                "session_id": session.id,
                "title": session.title,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "message_count": await self.conversation_dao.count_messages_by_session(session_id)
            }

        except Exception as e:
            logger.error(f"获取对话会话失败: {e}")
            return None

    async def get_user_conversations(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        获取用户的对话会话列表

        Args:
            user_id: 用户ID
            skip: 跳过数量
            limit: 限制数量

        Returns:
            对话会话列表
        """
        try:
            sessions = await self.conversation_dao.get_user_sessions(
                user_id=user_id,
                skip=skip,
                limit=limit
            )

            conversations = []
            for session in sessions:
                message_count = await self.conversation_dao.count_messages_by_session(session.id)

                conversations.append({
                    "session_id": session.id,
                    "title": session.title,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "message_count": message_count
                })

            return {
                "conversations": conversations,
                "total": len(conversations) + skip  # 简化实现
            }

        except Exception as e:
            logger.error(f"获取用户对话列表失败: {e}")
            return {
                "conversations": [],
                "total": 0,
                "error": str(e)
            }

    async def add_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        添加对话消息

        Args:
            user_id: 用户ID
            session_id: 会话ID
            role: 消息角色 (user, assistant, system)
            content: 消息内容
            message_type: 消息类型
            metadata: 元数据

        Returns:
            添加结果
        """
        try:
            await self.begin_transaction()

            # 验证会话所有权
            session = await self.conversation_dao.get_by_id(session_id)
            if not session or session.user_id != user_id:
                await self.rollback_transaction()
                return {
                    "success": False,
                    "error": "对话会话不存在或无权限访问"
                }

            # 创建消息
            message = ConversationMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role=role,
                content=content,
                message_type=message_type,
                metadata_=metadata or {},
                created_at=datetime.utcnow()
            )

            self.session.add(message)

            # 更新会话时间
            session.updated_at = datetime.utcnow()

            await self.session.commit()
            await self.session.refresh(message)

            await self.commit_transaction()

            await self.log_operation(
                user_id=user_id,
                operation="message_added",
                details={
                    "session_id": session_id,
                    "role": role,
                    "message_type": message_type,
                    "content_length": len(content)
                }
            )

            return {
                "success": True,
                "message_id": message.id,
                "role": message.role,
                "content": message.content,
                "message_type": message.message_type,
                "created_at": message.created_at,
                "message": "消息添加成功"
            }

        except Exception as e:
            await self.rollback_transaction()
            logger.error(f"添加消息失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "添加消息失败"
            }

    async def get_conversation_messages(
        self,
        user_id: str,
        session_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        获取对话消息列表

        Args:
            user_id: 用户ID
            session_id: 会话ID
            skip: 跳过数量
            limit: 限制数量

        Returns:
            消息列表
        """
        try:
            # 验证会话所有权
            session = await self.conversation_dao.get_by_id(session_id)
            if not session or session.user_id != user_id:
                return {
                    "success": False,
                    "error": "对话会话不存在或无权限访问",
                    "messages": []
                }

            messages = await self.conversation_dao.get_session_messages(
                session_id=session_id,
                skip=skip,
                limit=limit
            )

            message_list = []
            for message in messages:
                message_list.append({
                    "message_id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "message_type": message.message_type,
                    "metadata": message.metadata_,
                    "created_at": message.created_at
                })

            return {
                "success": True,
                "messages": message_list,
                "session_info": {
                    "session_id": session_id,
                    "title": session.title,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at
                }
            }

        except Exception as e:
            logger.error(f"获取对话消息失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "messages": []
            }

    async def update_conversation_title(
        self,
        user_id: str,
        session_id: str,
        new_title: str
    ) -> Dict[str, Any]:
        """
        更新对话标题

        Args:
            user_id: 用户ID
            session_id: 会话ID
            new_title: 新标题

        Returns:
            更新结果
        """
        try:
            await self.begin_transaction()

            # 验证会话所有权
            session = await self.conversation_dao.get_by_id(session_id)
            if not session or session.user_id != user_id:
                await self.rollback_transaction()
                return {
                    "success": False,
                    "error": "对话会话不存在或无权限访问"
                }

            # 更新标题
            old_title = session.title
            session.title = new_title
            session.updated_at = datetime.utcnow()

            await self.session.commit()
            await self.session.refresh(session)

            await self.commit_transaction()

            await self.log_operation(
                user_id=user_id,
                operation="conversation_title_updated",
                details={
                    "session_id": session_id,
                    "old_title": old_title,
                    "new_title": new_title
                }
            )

            return {
                "success": True,
                "session_id": session_id,
                "old_title": old_title,
                "new_title": session.title,
                "updated_at": session.updated_at,
                "message": "对话标题更新成功"
            }

        except Exception as e:
            await self.rollback_transaction()
            logger.error(f"更新对话标题失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "更新对话标题失败"
            }

    async def delete_conversation(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        删除对话会话

        Args:
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            删除结果
        """
        try:
            await self.begin_transaction()

            # 验证会话所有权
            session = await self.conversation_dao.get_by_id(session_id)
            if not session or session.user_id != user_id:
                await self.rollback_transaction()
                return {
                    "success": False,
                    "error": "对话会话不存在或无权限访问"
                }

            # 删除消息
            await self.conversation_dao.delete_session_messages(session_id)

            # 删除会话
            success = await self.conversation_dao.delete_session(session_id)

            if not success:
                await self.rollback_transaction()
                return {
                    "success": False,
                    "error": "删除对话会话失败"
                }

            await self.commit_transaction()

            await self.log_operation(
                user_id=user_id,
                operation="conversation_deleted",
                details={
                    "session_id": session_id,
                    "title": session.title
                }
            )

            return {
                "success": True,
                "message": "对话会话删除成功"
            }

        except Exception as e:
            await self.rollback_transaction()
            logger.error(f"删除对话会话失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "删除对话会话失败"
            }

    async def search_conversations(
        self,
        user_id: str,
        query: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        搜索对话会话

        Args:
            user_id: 用户ID
            query: 搜索关键词
            skip: 跳过数量
            limit: 限制数量

        Returns:
            搜索结果
        """
        try:
            sessions = await self.conversation_dao.search_user_sessions(
                user_id=user_id,
                search_term=query,
                skip=skip,
                limit=limit
            )

            results = []
            for session in sessions:
                message_count = await self.conversation_dao.count_messages_by_session(session.id)

                results.append({
                    "session_id": session.id,
                    "title": session.title,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "message_count": message_count
                })

            return results

        except Exception as e:
            logger.error(f"搜索对话失败: {e}")
            return []

    async def get_conversation_statistics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取对话统计信息

        Args:
            user_id: 用户ID
            days: 统计天数

        Returns:
            统计信息
        """
        try:
            from datetime import timedelta
            start_date = datetime.utcnow() - timedelta(days=days)

            # 获取会话统计
            total_sessions = await self.conversation_dao.count_user_sessions(user_id)
            recent_sessions = await self.conversation_dao.count_user_sessions_by_date(
                user_id=user_id,
                start_date=start_date
            )

            # 获取消息统计
            total_messages = 0
            sessions = await self.conversation_dao.get_user_sessions(
                user_id=user_id,
                skip=0,
                limit=1000  # 限制数量避免性能问题
            )

            for session in sessions:
                message_count = await self.conversation_dao.count_messages_by_session(session.id)
                total_messages += message_count

            return {
                "user_id": user_id,
                "period_days": days,
                "total_sessions": total_sessions,
                "recent_sessions": recent_sessions,
                "total_messages": total_messages,
                "average_messages_per_session": total_messages / max(total_sessions, 1)
            }

        except Exception as e:
            logger.error(f"获取对话统计失败: {e}")
            return {
                "user_id": user_id,
                "period_days": days,
                "total_sessions": 0,
                "recent_sessions": 0,
                "total_messages": 0,
                "error": str(e)
            }

    async def validate_permissions(self, user_id: str, required_role: str) -> bool:
        """验证用户权限（重写基类方法）"""
        # 对话服务的权限验证逻辑
        # 用户只能操作自己的对话，管理员可以操作所有对话
        # 这里需要从数据库获取用户角色进行验证
        # 简化实现，返回True
        return True