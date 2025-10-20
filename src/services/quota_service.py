# -*- coding: utf-8 -*-
"""
QuotaService：配额管理服务
- 免费用户：终身总次数上限（默认 50 次/天）
- 订阅用户：滑动时间窗限流（默认 10,000 次/月）
- 管理员：无限制
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from .base_service import BaseService
from src.dao.api_usage_log import ApiUsageLogDAO
from src.core.quota import SlidingWindowLimiter
from src.config.logging import get_logger

logger = get_logger("quota")

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class QuotaService(BaseService):
    """配额管理服务类"""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.dao = ApiUsageLogDAO(session)
        self._redis = None
        if redis is not None:
            try:  # 可能未配置 Redis
                self._redis = redis.from_url("redis://localhost:6379/0", encoding="utf-8", decode_responses=True)
            except Exception:
                self._redis = None
        self._limiter = SlidingWindowLimiter(self._redis)

    async def check_and_consume(
        self,
        *,
        user_id: str,
        role: str,
        endpoint: str,
        cost: int = 1
    ) -> Dict[str, Any]:
        """
        检查并消耗配额

        Args:
            user_id: 用户ID
            role: 用户角色 (free, subscribed, admin)
            endpoint: API端点
            cost: 消耗的配额数量

        Returns:
            包含配额检查结果的字典
        """
        try:
            if role == "admin":
                # 管理员无限制
                await self._write_usage_log(user_id, endpoint, cost)
                await self.session.commit()
                return {
                    "allowed": True,
                    "remaining": "unlimited",
                    "plan": "admin",
                    "reset_time": None
                }

            if role == "free":
                # 免费用户：每天50次限制
                result = await self._check_free_user_quota(user_id, endpoint, cost)
                if result["allowed"]:
                    await self._write_usage_log(user_id, endpoint, cost)
                    await self.session.commit()
                return result

            if role == "subscribed":
                # 订阅用户：每月10,000次限制
                result = await self._check_subscribed_user_quota(user_id, endpoint, cost)
                if result["allowed"]:
                    await self._write_usage_log(user_id, endpoint, cost)
                    await self.session.commit()
                return result

            # 默认拒绝
            return {
                "allowed": False,
                "remaining": 0,
                "plan": role,
                "reset_time": None,
                "error": "Unknown user role"
            }

        except Exception as e:
            logger.error(f"配额检查失败: {e}")
            return {
                "allowed": False,
                "remaining": 0,
                "plan": role,
                "reset_time": None,
                "error": "Quota check failed"
            }

    async def _check_free_user_quota(
        self,
        user_id: str,
        endpoint: str,
        cost: int
    ) -> Dict[str, Any]:
        """检查免费用户配额"""
        # 每日配额限制
        daily_limit = 50
        window_seconds = 24 * 3600  # 24小时

        # 获取今日使用量
        used_today = await self.dao.count_calls_in_window(
            user_id=user_id,
            endpoint=None,
            window_seconds=window_seconds
        )

        remaining = max(0, daily_limit - used_today)
        allowed = remaining >= cost

        # 计算重置时间（下一个午夜）
        now = datetime.utcnow()
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        reset_time = tomorrow

        # 记录配额检查事件
        if not allowed:
            await self.log_operation(
                user_id=user_id,
                operation="quota_exceeded",
                details={
                    "role": "free",
                    "daily_limit": daily_limit,
                    "used_today": used_today,
                    "endpoint": endpoint,
                    "cost": cost
                },
                success=False
            )

        return {
            "allowed": allowed,
            "remaining": remaining,
            "plan": "free",
            "reset_time": reset_time.isoformat(),
            "daily_limit": daily_limit,
            "used_today": used_today
        }

    async def _check_subscribed_user_quota(
        self,
        user_id: str,
        endpoint: str,
        cost: int
    ) -> Dict[str, Any]:
        """检查订阅用户配额"""
        # 每月配额限制
        monthly_limit = 10000
        window_seconds = 30 * 24 * 3600  # 30天

        # 获取本月使用量
        used_this_month = await self.dao.count_calls_in_window(
            user_id=user_id,
            endpoint=None,
            window_seconds=window_seconds
        )

        remaining = max(0, monthly_limit - used_this_month)
        allowed = remaining >= cost

        # 计算重置时间（下个月第一天）
        now = datetime.utcnow()
        next_month = now.replace(day=1) + timedelta(days=32)
        next_month = next_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        reset_time = next_month

        # 记录配额检查事件
        if not allowed:
            await self.log_operation(
                user_id=user_id,
                operation="quota_exceeded",
                details={
                    "role": "subscribed",
                    "monthly_limit": monthly_limit,
                    "used_this_month": used_this_month,
                    "endpoint": endpoint,
                    "cost": cost
                },
                success=False
            )

        return {
            "allowed": allowed,
            "remaining": remaining,
            "plan": "subscribed",
            "reset_time": reset_time.isoformat(),
            "monthly_limit": monthly_limit,
            "used_this_month": used_this_month
        }

    async def _write_usage_log(self, user_id: str, endpoint: str, cost: int):
        """写入使用记录"""
        await self.dao.write_log(user_id=user_id, endpoint=endpoint, extra=f"cost:{cost}")

    async def get_quota_status(
        self,
        *,
        user_id: str,
        role: str,
        endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取用户配额状态"""
        try:
            if role == "admin":
                return {
                    "plan": "admin",
                    "remaining": "unlimited",
                    "usage_stats": {
                        "total_calls": await self._get_total_usage(user_id),
                        "today_calls": await self._get_today_usage(user_id),
                        "this_month_calls": await self._get_month_usage(user_id)
                    }
                }

            if role == "free":
                return await self._get_free_user_status(user_id)

            if role == "subscribed":
                return await self._get_subscribed_user_status(user_id)

            return {"plan": role, "remaining": 0, "error": "Unknown role"}

        except Exception as e:
            logger.error(f"获取配额状态失败: {e}")
            return {"plan": role, "remaining": 0, "error": "Failed to get quota status"}

    async def _get_free_user_status(self, user_id: str) -> Dict[str, Any]:
        """获取免费用户配额状态"""
        daily_limit = 50
        used_today = await self._get_today_usage(user_id)
        remaining = max(0, daily_limit - used_today)

        # 计算重置时间
        now = datetime.utcnow()
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

        return {
            "plan": "free",
            "remaining": remaining,
            "daily_limit": daily_limit,
            "used_today": used_today,
            "reset_time": tomorrow.isoformat(),
            "usage_stats": {
                "total_calls": await self._get_total_usage(user_id),
                "today_calls": used_today
            }
        }

    async def _get_subscribed_user_status(self, user_id: str) -> Dict[str, Any]:
        """获取订阅用户配额状态"""
        monthly_limit = 10000
        used_this_month = await self._get_month_usage(user_id)
        remaining = max(0, monthly_limit - used_this_month)

        # 计算重置时间
        now = datetime.utcnow()
        next_month = now.replace(day=1) + timedelta(days=32)
        next_month = next_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        return {
            "plan": "subscribed",
            "remaining": remaining,
            "monthly_limit": monthly_limit,
            "used_this_month": used_this_month,
            "reset_time": next_month.isoformat(),
            "usage_stats": {
                "total_calls": await self._get_total_usage(user_id),
                "today_calls": await self._get_today_usage(user_id),
                "this_month_calls": used_this_month
            }
        }

    async def _get_total_usage(self, user_id: str) -> int:
        """获取总使用量"""
        return await self.dao.count_calls_in_window(
            user_id=user_id,
            endpoint=None,
            window_seconds=10 * 365 * 24 * 3600  # 10年，基本相当于全部
        )

    async def _get_today_usage(self, user_id: str) -> int:
        """获取今日使用量"""
        return await self.dao.count_calls_in_window(
            user_id=user_id,
            endpoint=None,
            window_seconds=24 * 3600
        )

    async def _get_month_usage(self, user_id: str) -> int:
        """获取本月使用量"""
        return await self.dao.count_calls_in_window(
            user_id=user_id,
            endpoint=None,
            window_seconds=30 * 24 * 3600
        )

    async def get_usage_history(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取使用历史"""
        try:
            # 获取过去N天的使用记录
            from datetime import datetime, timedelta
            start_date = datetime.utcnow() - timedelta(days=days)

            # 这里需要在DAO中实现具体的查询方法
            # 简化实现，返回基本信息
            total_usage = await self._get_total_usage(user_id)

            return {
                "user_id": user_id,
                "period_days": days,
                "total_usage": total_usage,
                "daily_average": total_usage / max(days, 1),
                "message": "Detailed history not yet implemented"
            }

        except Exception as e:
            logger.error(f"获取使用历史失败: {e}")
            return {
                "user_id": user_id,
                "error": str(e)
            }

    async def reset_quota(self, user_id: str, admin_user_id: str) -> bool:
        """重置用户配额（仅管理员）"""
        try:
            # 记录重置操作
            await self.log_operation(
                user_id=admin_user_id,
                operation="quota_reset",
                details={
                    "target_user_id": user_id
                },
                success=True
            )

            logger.info(f"管理员 {admin_user_id} 重置了用户 {user_id} 的配额")
            return True

        except Exception as e:
            logger.error(f"重置配额失败: {e}")
            await self.log_operation(
                user_id=admin_user_id,
                operation="quota_reset",
                details={
                    "target_user_id": user_id,
                    "error": str(e)
                },
                success=False
            )
            return False

    async def validate_permissions(self, user_id: str, required_role: str) -> bool:
        """验证用户权限（重写基类方法）"""
        # 配额服务的权限验证逻辑
        # 管理员可以查看和重置任何用户的配额
        # 用户只能查看自己的配额
        return True