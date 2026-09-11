"""Authentication dependencies for required and optional bearer credentials."""

import logging
from typing import Any, Dict, Optional

from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)


def bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(401, "未提供认证信息", headers={"WWW-Authenticate": "Bearer"})
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(401, "认证格式错误", headers={"WWW-Authenticate": "Bearer"})
    return parts[1]


async def get_current_user(
    authorization: Optional[str] = Header(None, description="JWT Token")
) -> Dict[str, Any]:
    token = bearer_token(authorization)
    from backend.services.user_service import UserService
    try:
        user = await UserService().get_current_user(token)
    except Exception as exc:
        logger.error("Authentication storage failed", exc_info=True)
        raise HTTPException(503, "认证服务暂时不可用") from exc
    if not user:
        raise HTTPException(401, "认证失败", headers={"WWW-Authenticate": "Bearer"})
    return {
        "user_id": user["id"],
        "username": user.get("username", ""),
        "email": user.get("email", ""),
        "is_admin": user.get("role") == "admin",
        "is_anonymous": False,
    }


async def get_optional_user(
    authorization: Optional[str] = Header(None, description="JWT Token（可选）")
) -> Optional[Dict[str, Any]]:
    if authorization is None:
        return None
    # Credentials that are present but invalid must never bypass ownership checks.
    return await get_current_user(authorization)
