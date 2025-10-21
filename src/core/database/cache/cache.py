# -*- coding: utf-8 -*-
"""
缓存管理模块
提供基于Redis的缓存功能
"""

from __future__ import annotations

import json
import pickle
from typing import Any, Optional

import redis.asyncio as redis
from redis.exceptions import ConnectionError

from src.config.loader.config_loader import get_settings


class Cache:
    """缓存管理器"""

    def __init__(self):
        """初始化缓存管理器"""
        self.settings = get_settings()
        self._redis_client: Optional[redis.Redis] = None

    def _get_client(self) -> redis.Redis:
        """获取Redis客户端"""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                self.settings.redis_url,
                decode_responses=True,
                max_connections=20,
            )
        return self._redis_client

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            client = self._get_client()
            value = await client.get(key)
            if value is None:
                return None

            # 尝试JSON反序列化
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # 如果不是JSON，尝试pickle反序列化
                return pickle.loads(value.encode('latin1'))
        except ConnectionError:
            # Redis连接失败时返回None
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            client = self._get_client()

            # 序列化值
            if isinstance(value, (dict, list, str, int, float, bool)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = pickle.dumps(value).decode('latin1')

            # 设置过期时间
            if ttl is None:
                ttl = self.settings.cache_ttl

            await client.setex(key, ttl, serialized_value)
            return True
        except ConnectionError:
            # Redis连接失败时静默返回False
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            client = self._get_client()
            await client.delete(key)
            return True
        except ConnectionError:
            return False

    async def exists(self, key: str) -> bool:
        """检查缓存键是否存在"""
        try:
            client = self._get_client()
            return await client.exists(key) > 0
        except ConnectionError:
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """设置缓存过期时间"""
        try:
            client = self._get_client()
            await client.expire(key, ttl)
            return True
        except ConnectionError:
            return False

    async def connect(self):
        """连接缓存（为了兼容性）"""
        try:
            # 尝试连接Redis
            client = self._get_client()
            await client.ping()
            print("Redis缓存连接成功")
        except Exception as e:
            print(f"Redis缓存连接失败，使用内存缓存: {e}")

    async def disconnect(self):
        """断开缓存连接"""
        try:
            if self._redis_client:
                await self._redis_client.close()
                print("缓存连接已断开")
        except Exception as e:
            print(f"断开缓存连接失败: {e}")


# 全局缓存实例
cache = Cache()
