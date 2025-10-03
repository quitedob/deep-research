# -*- coding: utf-8 -*-
"""
Quota API：GET /api/users/me/quota
最小可用：根据角色返回配额占位信息（后续联动 Redis/DB）。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import cache
from src.core.db import get_db_session
from src.service.auth import decode_token
from src.api.auth import oauth2_scheme
from src.service.quota import QuotaService


router = APIRouter(prefix="/users/me", tags=["quota"])


@router.get("/quota")
async def get_quota(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db_session)):
    claims = decode_token(token)
    role = claims.get("role", "free")
    svc = QuotaService(session)
    return await svc.remaining(user_id=int(claims.get("sub")), role=role, endpoint="chat")


