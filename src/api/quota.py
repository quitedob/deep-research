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
from ..services.quota_service import QuotaService
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
    获取当前用户的配额状态 - 通过QuotaService处理业务逻辑

    返回用户的配额使用情况，包括已用、剩余和百分比
    """
    try:
        quota_service = QuotaService(session)

        # 通过服务层获取配额状态
        quota_status = await quota_service.get_quota_status(
            user_id=str(current_user.id),
            role=current_user.role
        )

        # 根据用户角色构建响应
        if current_user.role == "admin":
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
            stats = quota_status.get("usage_stats", {})
            used = stats.get("today_calls", 0)
            limit = quota_status.get("daily_limit", 50)
            remaining = quota_status.get("remaining", 0)
            percentage_used = (used / limit * 100) if limit > 0 else 0
            is_exceeded = remaining <= 0

            # 生成警告消息
            warning_message = None
            if is_exceeded:
                warning_message = "您的免费配额已用完，请升级到订阅版本以继续使用"
            elif percentage_used >= 80:
                warning_message = f"您已使用 {percentage_used:.0f}% 的免费配额，即将用完"

            return QuotaStatusResponse(
                user_role="free",
                quota_type="daily",
                limit=limit,
                used=used,
                remaining=remaining,
                percentage_used=percentage_used,
                is_exceeded=is_exceeded,
                warning_message=warning_message
            )

        elif current_user.role == "subscribed":
            stats = quota_status.get("usage_stats", {})
            used = stats.get("this_month_calls", 0)
            limit = quota_status.get("monthly_limit", 10000)
            remaining = quota_status.get("remaining", 0)
            percentage_used = (used / limit * 100) if limit > 0 else 0
            is_exceeded = remaining <= 0

            # 生成警告消息
            warning_message = None
            if is_exceeded:
                warning_message = "您本月的配额已用完，请等待下月重置或升级套餐"
            elif percentage_used >= 80:
                warning_message = f"您已使用 {percentage_used:.0f}% 的月度配额"

            return QuotaStatusResponse(
                user_role="subscribed",
                quota_type="monthly",
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
    获取用户的使用历史 - 通过QuotaService处理业务逻辑

    返回最近的 API 调用记录
    """
    try:
        quota_service = QuotaService(session)

        # 通过服务层获取使用历史
        history = await quota_service.get_usage_history(
            user_id=str(current_user.id),
            days=30  # 默认获取30天的历史
        )

        # 如果有错误，返回错误信息
        if history.get("error"):
            logger.error(f"获取使用历史失败: {history.get('error')}")
            return {
                "total": 0,
                "history": [],
                "error": history.get("error")
            }

        # 简化的历史记录（详细记录需要DAO支持）
        return {
            "total": history.get("total_usage", 0),
            "history": [
                {
                    "period_days": history.get("period_days", 30),
                    "total_usage": history.get("total_usage", 0),
                    "daily_average": history.get("daily_average", 0),
                    "message": history.get("message", "Detailed history not yet implemented")
                }
            ]
        }

    except Exception as e:
        logger.error(f"获取使用历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
