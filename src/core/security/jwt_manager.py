#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JWT Token管理器
支持Redis存储、Token刷新、黑名单等功能
"""

import jwt
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import os

from src.core.security.redis_client import redis_client

logger = logging.getLogger(__name__)

# JWT配置
SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '60'))  # 1小时
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7'))  # 7天


class JWTManager:
    """JWT Token管理器"""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        self.refresh_token_expire = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    def create_access_token(
        self, 
        user_id: str, 
        username: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建访问令牌
        
        Args:
            user_id: 用户ID
            username: 用户名
            additional_claims: 额外的声明
            
        Returns:
            JWT Token
        """
        expire = datetime.utcnow() + self.access_token_expire
        
        to_encode = {
            "sub": user_id,
            "username": username,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        if additional_claims:
            to_encode.update(additional_claims)
        
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        logger.debug(f"创建访问令牌: user_id={user_id}, expire={expire}")
        return token
    
    def create_refresh_token(
        self, 
        user_id: str, 
        username: str
    ) -> str:
        """
        创建刷新令牌
        
        Args:
            user_id: 用户ID
            username: 用户名
            
        Returns:
            JWT Token
        """
        expire = datetime.utcnow() + self.refresh_token_expire
        
        to_encode = {
            "sub": user_id,
            "username": username,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16)  # JWT ID，用于撤销
        }
        
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        logger.debug(f"创建刷新令牌: user_id={user_id}, expire={expire}")
        return token
    
    def create_token_pair(
        self, 
        user_id: str, 
        username: str
    ) -> Tuple[str, str]:
        """
        创建访问令牌和刷新令牌对
        
        Args:
            user_id: 用户ID
            username: 用户名
            
        Returns:
            (access_token, refresh_token)
        """
        access_token = self.create_access_token(user_id, username)
        refresh_token = self.create_refresh_token(user_id, username)
        
        return access_token, refresh_token
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        解码Token
        
        Args:
            token: JWT Token
            
        Returns:
            Token载荷或None
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token已过期")
            return None
        except jwt.JWTError as e:
            logger.error(f"Token解码失败: {e}")
            return None
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        验证Token
        
        Args:
            token: JWT Token
            
        Returns:
            (是否有效, Token载荷)
        """
        payload = self.decode_token(token)
        if not payload:
            return False, None
        
        # 检查Token类型
        token_type = payload.get("type")
        if token_type not in ["access", "refresh"]:
            logger.warning(f"无效的Token类型: {token_type}")
            return False, None
        
        return True, payload
    
    async def store_refresh_token(
        self, 
        user_id: str, 
        refresh_token: str,
        expire_seconds: Optional[int] = None
    ) -> bool:
        """
        存储刷新令牌到Redis
        
        Args:
            user_id: 用户ID
            refresh_token: 刷新令牌
            expire_seconds: 过期时间（秒）
            
        Returns:
            是否成功
        """
        if not redis_client.is_available():
            logger.debug("Redis不可用，跳过存储刷新令牌")
            return False
        
        key = f"refresh_token:{user_id}"
        expire = expire_seconds or int(self.refresh_token_expire.total_seconds())
        
        return await redis_client.set(key, refresh_token, expire)
    
    async def get_refresh_token(self, user_id: str) -> Optional[str]:
        """
        从Redis获取刷新令牌
        
        Args:
            user_id: 用户ID
            
        Returns:
            刷新令牌或None
        """
        if not redis_client.is_available():
            return None
        
        key = f"refresh_token:{user_id}"
        return await redis_client.get(key)
    
    async def revoke_refresh_token(self, user_id: str) -> bool:
        """
        撤销刷新令牌
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        if not redis_client.is_available():
            return False
        
        key = f"refresh_token:{user_id}"
        return await redis_client.delete(key)
    
    async def add_to_blacklist(
        self, 
        token: str, 
        expire_seconds: Optional[int] = None
    ) -> bool:
        """
        将Token加入黑名单
        
        Args:
            token: JWT Token
            expire_seconds: 过期时间（秒）
            
        Returns:
            是否成功
        """
        if not redis_client.is_available():
            logger.debug("Redis不可用，无法使用黑名单功能")
            return False
        
        # 解码Token获取过期时间
        payload = self.decode_token(token)
        if not payload:
            return False
        
        # 计算剩余有效时间
        exp = payload.get("exp")
        if exp:
            now = datetime.utcnow().timestamp()
            remaining = int(exp - now)
            if remaining <= 0:
                return True  # Token已过期，无需加入黑名单
            expire_seconds = remaining
        
        key = f"blacklist:{token}"
        return await redis_client.set(key, "1", expire_seconds)
    
    async def is_blacklisted(self, token: str) -> bool:
        """
        检查Token是否在黑名单中
        
        Args:
            token: JWT Token
            
        Returns:
            是否在黑名单中
        """
        if not redis_client.is_available():
            return False
        
        key = f"blacklist:{token}"
        return await redis_client.exists(key)
    
    async def refresh_access_token(
        self, 
        refresh_token: str
    ) -> Optional[Tuple[str, str]]:
        """
        使用刷新令牌获取新的访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            (新访问令牌, 新刷新令牌) 或 None
        """
        # 验证刷新令牌
        is_valid, payload = self.verify_token(refresh_token)
        if not is_valid or not payload:
            logger.warning("刷新令牌无效")
            return None
        
        # 检查Token类型
        if payload.get("type") != "refresh":
            logger.warning("Token类型不是refresh")
            return None
        
        user_id = payload.get("sub")
        username = payload.get("username")
        
        if not user_id or not username:
            logger.warning("刷新令牌缺少必要信息")
            return None
        
        # 如果使用Redis，验证刷新令牌是否匹配
        if redis_client.is_available():
            stored_token = await self.get_refresh_token(user_id)
            if stored_token != refresh_token:
                logger.warning("刷新令牌不匹配")
                return None
        
        # 创建新的Token对
        new_access_token, new_refresh_token = self.create_token_pair(
            user_id, 
            username
        )
        
        # 存储新的刷新令牌
        await self.store_refresh_token(user_id, new_refresh_token)
        
        # 将旧的刷新令牌加入黑名单
        await self.add_to_blacklist(refresh_token)
        
        logger.info(f"Token刷新成功: user_id={user_id}")
        return new_access_token, new_refresh_token
    
    async def logout(self, access_token: str, user_id: str) -> bool:
        """
        登出（撤销Token）
        
        Args:
            access_token: 访问令牌
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        # 将访问令牌加入黑名单
        await self.add_to_blacklist(access_token)
        
        # 撤销刷新令牌
        await self.revoke_refresh_token(user_id)
        
        logger.info(f"用户登出: user_id={user_id}")
        return True
    
    async def verify_and_check_blacklist(
        self, 
        token: str
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        验证Token并检查黑名单
        
        Args:
            token: JWT Token
            
        Returns:
            (是否有效, Token载荷)
        """
        # 先验证Token
        is_valid, payload = self.verify_token(token)
        if not is_valid:
            return False, None
        
        # 检查黑名单
        if await self.is_blacklisted(token):
            logger.warning("Token在黑名单中")
            return False, None
        
        return True, payload


# 全局JWT管理器实例
jwt_manager = JWTManager()
