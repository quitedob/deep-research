# -*- coding: utf-8 -*-
"""
ApiUsageLogDAO：接口调用日志写入，用于配额与审计。
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.sqlmodel.models import ApiUsageLog


class ApiUsageLogDAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def write_log(self, *, user_id: Optional[int], endpoint: str, extra: Optional[str] = None) -> ApiUsageLog:
        log = ApiUsageLog(user_id=user_id, endpoint=endpoint, extra=extra)
        self.session.add(log)
        await self.session.flush()
        return log

    async def count_calls_in_window(self, *, user_id: int, endpoint: Optional[str], window_seconds: int) -> int:
        since = datetime.utcnow() - timedelta(seconds=window_seconds)
        stmt = select(func.count()).select_from(ApiUsageLog).where(ApiUsageLog.user_id == user_id, ApiUsageLog.timestamp >= since)
        if endpoint:
            stmt = stmt.where(ApiUsageLog.endpoint == endpoint)
        res = await self.session.execute(stmt)
        return int(res.scalar_one() or 0)


