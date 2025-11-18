#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话数据访问对象
处理对话会话和消息的数据库操作
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import json

from src.dao.base import BaseDAO

logger = logging.getLogger(__name__)


class ChatDAO(BaseDAO):
    """对话数据访问对象"""

    async def create_session(
        self,
        user_id: str,
        title: str,
        llm_provider: str,
        model_name: str,
        system_prompt: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        创建对话会话
        
        Args:
            user_id: 用户ID
            title: 会话标题
            llm_provider: LLM提供商
            model_name: 模型名称
            system_prompt: 系统提示词
            
        Returns:
            创建的会话信息
        """
        session_id = str(uuid.uuid4())
        query = """
            INSERT INTO chat_sessions (id, user_id, title, llm_provider, model_name, system_prompt, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, user_id, title, llm_provider, model_name, system_prompt, status, message_count, created_at, updated_at
        """
        now = datetime.utcnow()
        
        try:
            result = await self.fetch_one(
                query,
                (session_id, user_id, title, llm_provider, model_name, system_prompt, now, now)
            )
            return result
        except Exception as e:
            logger.error(f"创建对话会话失败: {e}")
            return None

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取对话会话"""
        query = """
            SELECT id, user_id, title, llm_provider, model_name, system_prompt, 
                   status, message_count, created_at, updated_at
            FROM chat_sessions
            WHERE id = $1
        """
        return await self.fetch_one(query, (session_id,))

    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取用户的对话会话列表"""
        query = """
            SELECT id, user_id, title, llm_provider, model_name, status, message_count, created_at, updated_at
            FROM chat_sessions
            WHERE user_id = $1
            ORDER BY updated_at DESC
            LIMIT $2 OFFSET $3
        """
        return await self.fetch_all(query, (user_id, limit, offset))

    async def update_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        llm_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        status: Optional[str] = None
    ) -> bool:
        """更新对话会话"""
        updates = []
        params = []
        param_count = 1
        
        if title is not None:
            updates.append(f"title = ${param_count}")
            params.append(title)
            param_count += 1
            
        if llm_provider is not None:
            updates.append(f"llm_provider = ${param_count}")
            params.append(llm_provider)
            param_count += 1
            
        if model_name is not None:
            updates.append(f"model_name = ${param_count}")
            params.append(model_name)
            param_count += 1
            
        if system_prompt is not None:
            updates.append(f"system_prompt = ${param_count}")
            params.append(system_prompt)
            param_count += 1
            
        if status is not None:
            updates.append(f"status = ${param_count}")
            params.append(status)
            param_count += 1
        
        if not updates:
            return True
        
        updates.append(f"updated_at = ${param_count}")
        params.append(datetime.utcnow())
        param_count += 1
        
        params.append(session_id)
        
        query = f"""
            UPDATE chat_sessions
            SET {', '.join(updates)}
            WHERE id = ${param_count}
        """
        
        try:
            await self.execute_query(query, tuple(params))
            return True
        except Exception as e:
            logger.error(f"更新对话会话失败: {e}")
            return False

    async def delete_session(self, session_id: str) -> bool:
        """删除对话会话"""
        query = "DELETE FROM chat_sessions WHERE id = $1"
        try:
            await self.execute_query(query, (session_id,))
            return True
        except Exception as e:
            logger.error(f"删除对话会话失败: {e}")
            return False

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        model_name: Optional[str] = None,
        tokens_used: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[int]:
        """
        添加对话消息
        
        Args:
            session_id: 会话ID
            role: 角色 (user/assistant/system)
            content: 消息内容
            model_name: 模型名称
            tokens_used: 使用的token数
            metadata: 元数据
            
        Returns:
            消息ID
        """
        query = """
            INSERT INTO chat_messages (session_id, role, content, model_name, tokens_used, metadata, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """
        
        try:
            result = await self.fetch_one(
                query,
                (session_id, role, content, model_name, tokens_used, 
                 json.dumps(metadata) if metadata else None, datetime.utcnow())
            )
            
            if result:
                # 更新会话的消息计数和更新时间
                await self.execute_query(
                    """
                    UPDATE chat_sessions 
                    SET message_count = message_count + 1, updated_at = $1
                    WHERE id = $2
                    """,
                    (datetime.utcnow(), session_id)
                )
                return result['id']
            return None
        except Exception as e:
            logger.error(f"添加对话消息失败: {e}")
            return None

    async def get_session_messages(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取会话的消息列表"""
        if limit:
            query = """
                SELECT id, session_id, role, content, model_name, tokens_used, metadata, created_at
                FROM chat_messages
                WHERE session_id = $1
                ORDER BY created_at ASC
                LIMIT $2
            """
            return await self.fetch_all(query, (session_id, limit))
        else:
            query = """
                SELECT id, session_id, role, content, model_name, tokens_used, metadata, created_at
                FROM chat_messages
                WHERE session_id = $1
                ORDER BY created_at ASC
            """
            return await self.fetch_all(query, (session_id,))

    async def get_recent_messages(
        self,
        session_id: str,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """获取最近的N条消息"""
        query = """
            SELECT id, session_id, role, content, model_name, tokens_used, metadata, created_at
            FROM (
                SELECT * FROM chat_messages
                WHERE session_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            ) AS recent
            ORDER BY created_at ASC
        """
        return await self.fetch_all(query, (session_id, count))

    async def clear_session_messages(self, session_id: str) -> bool:
        """清空会话的所有消息"""
        try:
            await self.execute_query(
                "DELETE FROM chat_messages WHERE session_id = $1",
                (session_id,)
            )
            await self.execute_query(
                "UPDATE chat_sessions SET message_count = 0, updated_at = $1 WHERE id = $2",
                (datetime.utcnow(), session_id)
            )
            return True
        except Exception as e:
            logger.error(f"清空会话消息失败: {e}")
            return False
