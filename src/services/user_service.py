#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户服务
处理用户注册、登录、认证等业务逻辑
"""

import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import hashlib

from src.dao.user_dao import UserDAO
from src.schemas.user import UserRegister, UserLogin, UserResponse, UserUpdate, UserPreferences
from src.core.security.jwt_manager import jwt_manager

logger = logging.getLogger(__name__)


class UserService:
    """用户服务"""
    
    def __init__(self):
        self.user_dao = UserDAO()
        self.jwt_manager = jwt_manager
    
    @staticmethod
    def hash_password(password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """验证密码"""
        return UserService.hash_password(password) == password_hash
    
    async def register(self, user_data: UserRegister) -> Optional[Dict[str, Any]]:
        """
        用户注册
        
        Args:
            user_data: 用户注册数据
            
        Returns:
            用户信息和访问令牌
        """
        # 检查用户名是否已存在
        existing_user = await self.user_dao.get_user_by_username(user_data.username)
        if existing_user:
            raise ValueError("用户名已存在")
        
        # 检查邮箱是否已存在
        existing_email = await self.user_dao.get_user_by_email(user_data.email)
        if existing_email:
            raise ValueError("邮箱已被注册")
        
        # 创建用户
        password_hash = self.hash_password(user_data.password)
        user = await self.user_dao.create_user(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash,
            full_name=user_data.full_name
        )
        
        if not user:
            raise Exception("用户创建失败")
        
        # 生成Token对
        access_token, refresh_token = self.jwt_manager.create_token_pair(
            user['id'], 
            user['username']
        )
        
        # 存储刷新令牌到Redis
        await self.jwt_manager.store_refresh_token(user['id'], refresh_token)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }
    
    async def login(self, login_data: UserLogin) -> Optional[Dict[str, Any]]:
        """
        用户登录
        
        Args:
            login_data: 登录数据
            
        Returns:
            用户信息和访问令牌
        """
        # 尝试通过用户名或邮箱查找用户
        user = await self.user_dao.get_user_by_username(login_data.username)
        if not user:
            user = await self.user_dao.get_user_by_email(login_data.username)
        
        if not user:
            raise ValueError("用户名或密码错误")
        
        # 验证密码
        if not self.verify_password(login_data.password, user['password_hash']):
            raise ValueError("用户名或密码错误")
        
        # 检查用户是否激活
        if not user.get('is_active', True):
            raise ValueError("账户已被禁用")
        
        # 更新最后登录时间
        await self.user_dao.update_last_login(user['id'])
        
        # 生成Token对
        access_token, refresh_token = self.jwt_manager.create_token_pair(
            user['id'], 
            user['username']
        )
        
        # 存储刷新令牌到Redis
        await self.jwt_manager.store_refresh_token(user['id'], refresh_token)
        
        # 移除密码哈希
        user.pop('password_hash', None)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }
    
    async def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        获取当前用户
        
        Args:
            token: 访问令牌
            
        Returns:
            用户信息
        """
        # 验证Token并检查黑名单
        is_valid, payload = await self.jwt_manager.verify_and_check_blacklist(token)
        if not is_valid or not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = await self.user_dao.get_user_by_id(user_id)
        return user
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            新的Token对
        """
        result = await self.jwt_manager.refresh_access_token(refresh_token)
        if not result:
            return None
        
        new_access_token, new_refresh_token = result
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    
    async def logout(self, access_token: str, user_id: str) -> bool:
        """
        用户登出
        
        Args:
            access_token: 访问令牌
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        return await self.jwt_manager.logout(access_token, user_id)
    
    async def update_profile(
        self,
        user_id: str,
        update_data: UserUpdate
    ) -> bool:
        """更新用户资料"""
        return await self.user_dao.update_user_profile(
            user_id=user_id,
            full_name=update_data.full_name,
            avatar_url=update_data.avatar_url
        )
    
    async def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户偏好设置"""
        return await self.user_dao.get_user_preferences(user_id)
    
    async def update_preferences(
        self,
        user_id: str,
        preferences: UserPreferences
    ) -> bool:
        """更新用户偏好设置"""
        return await self.user_dao.update_user_preferences(
            user_id=user_id,
            default_llm_provider=preferences.default_llm_provider,
            default_model=preferences.default_model,
            theme=preferences.theme,
            language=preferences.language,
            preferences=preferences.preferences
        )
