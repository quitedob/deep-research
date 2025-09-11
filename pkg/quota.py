# -*- coding: utf-8 -*-
"""
配额算法封装：
- 订阅用户：滑动时间窗限流（Redis ZSET 实现；无 Redis 则内存近似）。
"""

from __future__ import annotations

import time
from typing import Optional

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class SlidingWindowLimiter:
    def __init__(self, client: Optional["redis.Redis"], namespace: str = "quota"):
        self.client = client
        self.ns = namespace
        self._mem: dict[str, list[float]] = {}

    def _key(self, user_id: int, window_tag: str) -> str:
        return f"{self.ns}:{window_tag}:{user_id}"

    async def allow(self, *, user_id: int, window_tag: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        if self.client is None:
            key = self._key(user_id, window_tag)
            buf = [t for t in self._mem.get(key, []) if t > now - window_seconds]
            if len(buf) >= limit:
                self._mem[key] = buf
                return False
            buf.append(now)
            self._mem[key] = buf
            return True

        # Redis ZSET：score=timestamp，成员使用唯一值
        key = self._key(user_id, window_tag)
        pipe = self.client.pipeline()
        cutoff = now - window_seconds
        pipe.zremrangebyscore(key, 0, cutoff)
        pipe.zcard(key)
        res = await pipe.execute()
        current = int(res[1] or 0)
        if current >= limit:
            return False
        member = f"{now:.6f}:{int(now*1e6)}"
        pipe = self.client.pipeline()
        pipe.zadd(key, {member: now})
        pipe.expire(key, window_seconds)
        await pipe.execute()
        return True


