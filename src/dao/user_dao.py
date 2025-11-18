#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户数据访问对象
处理用户相关的数据库操作
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from src.dao.base import BaseDAO

logger = logging.getLogger(__name__)


class UserDAO(BaseDAO):
    """用户数据访问对象"""

    async def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        full_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        创建新用户
        
        Args:
            username: 用户名
            email: 邮箱
            password_hash: 密码哈希
            full_name: 全名
            
        Returns:
            创建的用户信息
        """
        user_id = str(uuid.uuid4())
        query = """
            INSERT INTO users (id, username, email, password_hash, full_name, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, username, email, full_name, is_active, is_verified, created_at
        """
        now = datetime.utcnow()
        
        try:
            result = await self.fetch_one(
                query,
                (user_id, username, email, password_hash, full_name, now, now)
            )
            
            if result:
                # 创建默认用户偏好
                await self.create_user_preferences(user_id)
                
            return result
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            return None

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        query = """
            SELECT id, username, email, password_hash, full_name, avatar_url,
                   is_active, is_verified, created_at, updated_at, last_login_at
            FROM users
            WHERE username = $1
        """
        return await self.fetch_one(query, (username,))

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取用户"""
        query = """
            SELECT id, username, email, password_hash, full_name, avatar_url,
                   is_active, is_verified, created_at, updated_at, last_login_at
            FROM users
            WHERE email = $1
        """
        return await self.fetch_one(query, (email,))

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        query = """
            SELECT id, username, email, full_name, avatar_url,
                   is_active, is_verified, created_at, updated_at, last_login_at
            FROM users
            WHERE id = $1
        """
        return await self.fetch_one(query, (user_id,))

    async def update_last_login(self, user_id: str) -> bool:
        """更新最后登录时间"""
        query = """
            UPDATE users
            SET last_login_at = $1, updated_at = $1
            WHERE id = $2
        """
        try:
            await self.execute_query(query, (datetime.utcnow(), user_id))
            return True
        except Exception as e:
            logger.error(f"更新登录时间失败: {e}")
            return False

    async def update_user_profile(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> bool:
        """更新用户资料"""
        updates = []
        params = []
        param_count = 1
        
        if full_name is not None:
            updates.append(f"full_name = ${param_count}")
            params.append(full_name)
            param_count += 1
            
        if avatar_url is not None:
            updates.append(f"avatar_url = ${param_count}")
            params.append(avatar_url)
            param_count += 1
        
        if not updates:
            return True
        
        updates.append(f"updated_at = ${param_count}")
        params.append(datetime.utcnow())
        param_count += 1
        
        params.append(user_id)
        
        query = f"""
            UPDATE users
            SET {', '.join(updates)}
            WHERE id = ${param_count}
        """
        
        try:
            await self.execute_query(query, tuple(params))
            return True
        except Exception as e:
            logger.error(f"更新用户资料失败: {e}")
            return False

    async def create_user_preferences(
        self,
        user_id: str,
        default_llm_provider: str = "deepseek",
        default_model: Optional[str] = None
    ) -> bool:
        """创建用户偏好设置"""
        query = """
            INSERT INTO user_preferences (user_id, default_llm_provider, default_model, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (user_id) DO NOTHING
        """
        now = datetime.utcnow()
        
        try:
            await self.execute_query(
                query,
                (user_id, default_llm_provider, default_model, now, now)
            )
            return True
        except Exception as e:
            logger.error(f"创建用户偏好失败: {e}")
            return False

    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户偏好设置"""
        query = """
            SELECT user_id, default_llm_provider, default_model, theme, language, preferences
            FROM user_preferences
            WHERE user_id = $1
        """
        return await self.fetch_one(query, (user_id,))

    async def update_user_preferences(
        self,
        user_id: str,
        default_llm_provider: Optional[str] = None,
        default_model: Optional[str] = None,
        theme: Optional[str] = None,
        language: Optional[str] = None,
        preferences: Optional[Dict] = None
    ) -> bool:
        """更新用户偏好设置"""
        updates = []
        params = []
        param_count = 1
        
        if default_llm_provider is not None:
            updates.append(f"default_llm_provider = ${param_count}")
            params.append(default_llm_provider)
            param_count += 1
            
        if default_model is not None:
            updates.append(f"default_model = ${param_count}")
            params.append(default_model)
            param_count += 1
            
        if theme is not None:
            updates.append(f"theme = ${param_count}")
            params.append(theme)
            param_count += 1
            
        if language is not None:
            updates.append(f"language = ${param_count}")
            params.append(language)
            param_count += 1
            
        if preferences is not None:
            updates.append(f"preferences = ${param_count}")
            params.append(preferences)
            param_count += 1
        
        if not updates:
            return True
        
        updates.append(f"updated_at = ${param_count}")
        params.append(datetime.utcnow())
        param_count += 1
        
        params.append(user_id)
        
        query = f"""
            UPDATE user_preferences
            SET {', '.join(updates)}
            WHERE user_id = ${param_count}
        """
        
        try:
            await self.execute_query(query, tuple(params))
            return True
        except Exception as e:
            logger.error(f"更新用户偏好失败: {e}")
            return False
