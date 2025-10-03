# -*- coding: utf-8 -*-
"""
QuotaService：
- 免费用户：终身总次数上限（默认 5 次），以 DB 日志为准。
- 订阅用户：滑动时间窗限流（默认 1 小时 5 次），以 Redis 优先，回退内存。
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.dao.api_usage_log import ApiUsageLogDAO
from src.core.quota import SlidingWindowLimiter

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class QuotaService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.dao = ApiUsageLogDAO(session)
        self._redis = None
        if redis is not None:
            try:  # 可能未配置 Redis
                self._redis = redis.from_url("redis://localhost:6379/0", encoding="utf-8", decode_responses=True)
            except Exception:
                self._redis = None
        self._limiter = SlidingWindowLimiter(self._redis)

    async def check_and_consume(self, *, user_id: int, role: str, endpoint: str) -> bool:
        if role == "free":
            total = await self.dao.count_calls_in_window(user_id=user_id, endpoint=None, window_seconds=10 * 365 * 24 * 3600)
            if total >= 5:
                return False
            await self.dao.write_log(user_id=user_id, endpoint=endpoint)
            await self.session.commit()
            return True

        # 订阅或更高：每小时 5 次
        allowed = await self._limiter.allow(user_id=user_id, window_tag=endpoint or "global", limit=5, window_seconds=3600)
        if not allowed:
            return False
        await self.dao.write_log(user_id=user_id, endpoint=endpoint)
        await self.session.commit()
        return True

    async def remaining(self, *, user_id: int, role: str, endpoint: Optional[str] = None):
        if role == "free":
            total = await self.dao.count_calls_in_window(user_id=user_id, endpoint=None, window_seconds=10 * 365 * 24 * 3600)
            return {"plan": "free", "remaining_total": max(0, 5 - total)}
        # 订阅：根据最近 1 小时 DB 统计估算
        used = await self.dao.count_calls_in_window(user_id=user_id, endpoint=endpoint, window_seconds=3600)
        return {"plan": role, "remaining_per_hour": max(0, 5 - used)}


