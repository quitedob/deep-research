# -*- coding: utf-8 -*-
"""
Redis 缓存客户端最小封装：在无 Redis 时自动降级为内存字典（开发占位）。
提供 get/set/incr/ttl 基本接口，后续配额与队列将复用。
"""

from __future__ import annotations

import os
import time
from typing import Optional, Tuple


class _MemoryCache:
    def __init__(self):
        self._store: dict[str, Tuple[Optional[float], str]] = {}

    async def get(self, key: str) -> Optional[str]:
        item = self._store.get(key)
        if not item:
            return None
        expire_at, value = item
        if expire_at and expire_at < time.time():
            self._store.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        expire_at = (time.time() + ex) if ex else None
        self._store[key] = (expire_at, value)

    async def incr(self, key: str, ex: Optional[int] = None) -> int:
        current = int(await self.get(key) or 0) + 1
        await self.set(key, str(current), ex=ex)
        return current


try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class CacheClient:
    def __init__(self):
        self._client = None
        self._fallback = _MemoryCache()

    async def connect(self):
        if redis is None:
            return
        url = os.getenv("REDIS_URL") or "redis://localhost:6379/0"
        try:
            self._client = redis.from_url(url, encoding="utf-8", decode_responses=True)
            await self._client.ping()
        except Exception:
            self._client = None

    async def get(self, key: str) -> Optional[str]:
        if self._client is None:
            return await self._fallback.get(key)
        return await self._client.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        if self._client is None:
            await self._fallback.set(key, value, ex=ex)
            return
        await self._client.set(key, value, ex=ex)

    async def incr(self, key: str, ex: Optional[int] = None) -> int:
        if self._client is None:
            return await self._fallback.incr(key, ex=ex)
        val = await self._client.incr(key)
        if ex:
            await self._client.expire(key, ex)
        return val


# 单例
cache = CacheClient()


