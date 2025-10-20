# -*- coding: utf-8 -*-
"""
共享依赖：认证与配额。
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db_session
from src.services.auth import decode_token
from src.services.quota import QuotaService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def require_auth(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")


async def require_admin(claims: dict = Depends(require_auth)) -> dict:
    """管理员权限验证"""
    if claims.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin access required")
    return claims


def require_quota(endpoint_tag: str):
    async def _inner(claims: dict = Depends(require_auth), session: AsyncSession = Depends(get_db_session)):
        svc = QuotaService(session)
        ok = await svc.check_and_consume(user_id=int(claims.get("sub")), role=claims.get("role", "free"), endpoint=endpoint_tag)
        if not ok:
            raise HTTPException(status_code=429, detail="quota exceeded")
        return True

    return _inner


