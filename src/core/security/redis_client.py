#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis客户端
用于Token管理、会话管理和缓存
"""

import redis.asyncio as redis
import logging
import os
from typing import Optional
import json

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis客户端单例"""
    
    _instance: Optional['RedisClient'] = None
    _redis: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self):
        """连接到Redis"""
        if self._redis is not None:
            return
        
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', '6379'))
            redis_password = os.getenv('REDIS_PASSWORD', '')
            redis_db = int(os.getenv('REDIS_DB', '0'))
            
            self._redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password if redis_password else None,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # 测试连接
            await self._redis.ping()
            logger.info(f"✓ Redis连接成功: {redis_host}:{redis_port}")
            
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}")
            logger.info("将使用内存模式（Token不会在服务器重启后保持）")
            self._redis = None
    
    async def close(self):
        """关闭Redis连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Redis连接已关闭")
    
    def is_available(self) -> bool:
        """检查Redis是否可用"""
        return self._redis is not None
    
    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """
        设置键值
        
        Args:
            key: 键
            value: 值
            expire: 过期时间（秒）
            
        Returns:
            是否成功
        """
        if not self.is_available():
            return False
        
        try:
            if expire:
                await self._redis.setex(key, expire, value)
            else:
                await self._redis.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET失败: {e}")
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """
        获取值
        
        Args:
            key: 键
            
        Returns:
            值或None
        """
        if not self.is_available():
            return None
        
        try:
            return await self._redis.get(key)
        except Exception as e:
            logger.error(f"Redis GET失败: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """
        删除键
        
        Args:
            key: 键
            
        Returns:
            是否成功
        """
        if not self.is_available():
            return False
        
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE失败: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 键
            
        Returns:
            是否存在
        """
        if not self.is_available():
            return False
        
        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS失败: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        设置过期时间
        
        Args:
            key: 键
            seconds: 秒数
            
        Returns:
            是否成功
        """
        if not self.is_available():
            return False
        
        try:
            await self._redis.expire(key, seconds)
            return True
        except Exception as e:
            logger.error(f"Redis EXPIRE失败: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """
        获取剩余过期时间
        
        Args:
            key: 键
            
        Returns:
            剩余秒数，-1表示永不过期，-2表示不存在
        """
        if not self.is_available():
            return -2
        
        try:
            return await self._redis.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL失败: {e}")
            return -2
    
    async def set_json(self, key: str, value: dict, expire: Optional[int] = None) -> bool:
        """
        设置JSON值
        
        Args:
            key: 键
            value: 字典值
            expire: 过期时间（秒）
            
        Returns:
            是否成功
        """
        try:
            json_str = json.dumps(value)
            return await self.set(key, json_str, expire)
        except Exception as e:
            logger.error(f"Redis SET_JSON失败: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[dict]:
        """
        获取JSON值
        
        Args:
            key: 键
            
        Returns:
            字典或None
        """
        try:
            json_str = await self.get(key)
            if json_str:
                return json.loads(json_str)
            return None
        except Exception as e:
            logger.error(f"Redis GET_JSON失败: {e}")
            return None
    
    async def incr(self, key: str) -> Optional[int]:
        """
        递增计数器
        
        Args:
            key: 键
            
        Returns:
            新值或None
        """
        if not self.is_available():
            return None
        
        try:
            return await self._redis.incr(key)
        except Exception as e:
            logger.error(f"Redis INCR失败: {e}")
            return None
    
    async def decr(self, key: str) -> Optional[int]:
        """
        递减计数器
        
        Args:
            key: 键
            
        Returns:
            新值或None
        """
        if not self.is_available():
            return None
        
        try:
            return await self._redis.decr(key)
        except Exception as e:
            logger.error(f"Redis DECR失败: {e}")
            return None


# 全局Redis客户端实例
redis_client = RedisClient()
