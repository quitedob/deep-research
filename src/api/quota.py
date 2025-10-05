# -*- coding: utf-8 -*-
"""
配额管理 API
提供配额查询和管理功能
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .deps import require_auth
from ..sqlmodel.models import User, ApiUsageLog
from ..core.db import get_async_session
from ..config.config_loader import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/quota", tags=["quota"])


# ==================== 响应模型 ====================

class QuotaStatusResponse(BaseModel):
    """配额状态响应"""
    user_role: str
    quota_type: str
    limit: int
    used: int
    remaining: int
    percentage_used: float
    is_exceeded: bool
    warning_message: str = None


# ==================== API 端点 ====================

@router.get("/status", response_model=QuotaStatusResponse)
async def get_quota_status(
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取当前用户的配额状态
    
    返回用户的配额使用情况，包括已用、剩余和百分比
    """
    try:
        if current_user.role == "admin":
            # 管理员无限制
            return QuotaStatusResponse(
                user_role="admin",
                quota_type="unlimited",
                limit=999999,
                used=0,
                remaining=999999,
                percentage_used=0.0,
                is_exceeded=False
            )
        
        elif current_user.role == "free":
            # 免费用户：终身次数限制
            result = await session.execute(
                select(func.count(ApiUsageLog.id))
                .where(ApiUsageLog.user_id == current_user.id)
            )
            used = result.scalar_one() or 0
            limit = settings.free_tier_lifetime_limit
            remaining = max(0, limit - used)
            percentage_used = (used / limit * 100) if limit > 0 else 0
            is_exceeded = used >= limit
            
            # 生成警告消息
            warning_message = None
            if is_exceeded:
                warning_message = "您的免费配额已用完，请升级到订阅版本以继续使用"
            elif percentage_used >= 80:
                warning_message = f"您已使用 {percentage_used:.0f}% 的免费配额，即将用完"
            
            return QuotaStatusResponse(
                user_role="free",
                quota_type="lifetime",
                limit=limit,
                used=used,
                remaining=remaining,
                percentage_used=percentage_used,
                is_exceeded=is_exceeded,
                warning_message=warning_message
            )
        
        elif current_user.role == "subscribed":
            # 订阅用户：每小时次数限制
            # 注意：这里简化处理，实际应该查询最近一小时的使用量
            from datetime import datetime, timedelta
            
            one_hour_ago = datetime.now() - timedelta(hours=1)
            result = await session.execute(
                select(func.count(ApiUsageLog.id))
                .where(ApiUsageLog.user_id == current_user.id)
                .where(ApiUsageLog.timestamp >= one_hour_ago)
            )
            used = result.scalar_one() or 0
            limit = settings.subscribed_tier_hourly_limit
            remaining = max(0, limit - used)
            percentage_used = (used / limit * 100) if limit > 0 else 0
            is_exceeded = used >= limit
            
            # 生成警告消息
            warning_message = None
            if is_exceeded:
                warning_message = "您本小时的配额已用完，请稍后再试"
            elif percentage_used >= 80:
                warning_message = f"您已使用 {percentage_used:.0f}% 的小时配额"
            
            return QuotaStatusResponse(
                user_role="subscribed",
                quota_type="hourly",
                limit=limit,
                used=used,
                remaining=remaining,
                percentage_used=percentage_used,
                is_exceeded=is_exceeded,
                warning_message=warning_message
            )
        
        else:
            raise HTTPException(status_code=400, detail="无效的用户角色")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配额状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_usage_history(
    limit: int = 50,
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取用户的使用历史
    
    返回最近的 API 调用记录
    """
    try:
        result = await session.execute(
            select(ApiUsageLog)
            .where(ApiUsageLog.user_id == current_user.id)
            .order_by(ApiUsageLog.timestamp.desc())
            .limit(limit)
        )
        logs = result.scalars().all()
        
        return {
            "total": len(logs),
            "history": [
                {
                    "endpoint": log.endpoint_called,
                    "timestamp": log.timestamp.isoformat(),
                    "extra": log.extra
                }
                for log in logs
            ]
        }
    
    except Exception as e:
        logger.error(f"获取使用历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
