#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆数据访问对象
处理用户事实和记忆的数据库操作
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from src.dao.base import BaseDAO

logger = logging.getLogger(__name__)


class MemoryDAO(BaseDAO):
    """记忆数据访问对象"""

    async def create_user_fact(
        self,
        user_id: str,
        fact_content: str,
        fact_type: str = "general",
        source_session_id: Optional[str] = None,
        source_message_id: Optional[int] = None,
        validity_score: float = 1.0,
        embedding_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        创建用户事实
        
        Args:
            user_id: 用户ID
            fact_content: 事实内容
            fact_type: 事实类型 (general, preference, skill, background等)
            source_session_id: 来源会话ID
            source_message_id: 来源消息ID
            validity_score: 有效性分数
            embedding_id: 向量ID
            
        Returns:
            创建的事实信息
        """
        fact_id = str(uuid.uuid4())
        query = """
            INSERT INTO user_facts 
            (id, user_id, fact_content, fact_type, source_session_id, source_message_id, 
             validity_score, embedding_id, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id, user_id, fact_content, fact_type, source_session_id, 
                      validity_score, embedding_id, created_at, updated_at
        """
        now = datetime.utcnow()
        
        try:
            result = await self.fetch_one(
                query,
                (fact_id, user_id, fact_content, fact_type, source_session_id,
                 source_message_id, validity_score, embedding_id, now, now)
            )
            return result
        except Exception as e:
            logger.error(f"创建用户事实失败: {e}")
            return None

    async def get_user_facts(
        self,
        user_id: str,
        fact_type: Optional[str] = None,
        min_validity_score: float = 0.5,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取用户事实列表
        
        Args:
            user_id: 用户ID
            fact_type: 事实类型过滤
            min_validity_score: 最小有效性分数
            limit: 返回数量限制
            
        Returns:
            事实列表
        """
        if fact_type:
            query = """
                SELECT id, user_id, fact_content, fact_type, source_session_id,
                       validity_score, embedding_id, created_at, updated_at
                FROM user_facts
                WHERE user_id = $1 AND fact_type = $2 AND validity_score >= $3
                ORDER BY created_at DESC
                LIMIT $4
            """
            return await self.fetch_all(query, (user_id, fact_type, min_validity_score, limit))
        else:
            query = """
                SELECT id, user_id, fact_content, fact_type, source_session_id,
                       validity_score, embedding_id, created_at, updated_at
                FROM user_facts
                WHERE user_id = $1 AND validity_score >= $2
                ORDER BY created_at DESC
                LIMIT $3
            """
            return await self.fetch_all(query, (user_id, min_validity_score, limit))

    async def get_fact_by_id(self, fact_id: str) -> Optional[Dict[str, Any]]:
        """获取单个事实"""
        query = """
            SELECT id, user_id, fact_content, fact_type, source_session_id,
                   validity_score, embedding_id, created_at, updated_at
            FROM user_facts
            WHERE id = $1
        """
        return await self.fetch_one(query, (fact_id,))

    async def update_fact_validity(
        self,
        fact_id: str,
        validity_score: float
    ) -> bool:
        """
        更新事实的有效性分数
        
        Args:
            fact_id: 事实ID
            validity_score: 新的有效性分数
            
        Returns:
            是否成功
        """
        query = """
            UPDATE user_facts
            SET validity_score = $1, updated_at = $2
            WHERE id = $3
        """
        try:
            await self.execute_query(query, (validity_score, datetime.utcnow(), fact_id))
            return True
        except Exception as e:
            logger.error(f"更新事实有效性失败: {e}")
            return False

    async def delete_fact(self, fact_id: str) -> bool:
        """删除事实"""
        query = "DELETE FROM user_facts WHERE id = $1"
        try:
            await self.execute_query(query, (fact_id,))
            return True
        except Exception as e:
            logger.error(f"删除事实失败: {e}")
            return False

    async def delete_user_facts(self, user_id: str) -> bool:
        """删除用户的所有事实"""
        query = "DELETE FROM user_facts WHERE user_id = $1"
        try:
            await self.execute_query(query, (user_id,))
            return True
        except Exception as e:
            logger.error(f"删除用户事实失败: {e}")
            return False

    async def mark_message_processed(self, message_id: int) -> bool:
        """
        标记消息已处理
        
        Args:
            message_id: 消息ID
            
        Returns:
            是否成功
        """
        query = """
            UPDATE chat_messages
            SET is_processed = TRUE
            WHERE id = $1
        """
        try:
            await self.execute_query(query, (message_id,))
            return True
        except Exception as e:
            logger.error(f"标记消息已处理失败: {e}")
            return False

    async def get_unprocessed_messages(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取未处理的消息
        
        Args:
            session_id: 会话ID
            limit: 返回数量限制
            
        Returns:
            未处理的消息列表
        """
        query = """
            SELECT id, session_id, role, content, model_name, created_at
            FROM chat_messages
            WHERE session_id = $1 AND is_processed = FALSE
            ORDER BY created_at ASC
            LIMIT $2
        """
        return await self.fetch_all(query, (session_id, limit))

    async def get_session_user_id(self, session_id: str) -> Optional[str]:
        """
        获取会话对应的用户ID
        
        Args:
            session_id: 会话ID
            
        Returns:
            用户ID
        """
        query = "SELECT user_id FROM chat_sessions WHERE id = $1"
        result = await self.fetch_one(query, (session_id,))
        return result['user_id'] if result else None
