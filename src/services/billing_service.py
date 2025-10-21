# -*- coding: utf-8 -*-
"""
BillingService：订阅和计费业务逻辑服务
提供订阅管理、计费处理、额度管理等功能
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from .base_service import BaseService
from src.dao import SubscriptionDAO, UsersDAO
from src.sqlmodel.models import Subscription, User
from src.config.logging.logging import get_logger

logger = get_logger("billing_service")


class BillingService(BaseService[Subscription]):
    """订阅和计费服务类"""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.subscription_dao = SubscriptionDAO(session)
        self.users_dao = UsersDAO(session)

    async def create_subscription(
        self,
        user_id: str,
        stripe_subscription_id: str,
        plan_name: str,
        status: str = "incomplete",
        current_period_start: Optional[datetime] = None,
        current_period_end: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        创建订阅

        Args:
            user_id: 用户ID
            stripe_subscription_id: Stripe订阅ID
            plan_name: 计划名称
            status: 订阅状态
            current_period_start: 当前周期开始时间
            current_period_end: 当前周期结束时间

        Returns:
            创建结果
        """
        try:
            await self.begin_transaction()

            # 验证用户存在
            user = await self.users_dao.get_by_id(user_id)
            if not user:
                await self.rollback_transaction()
                return {
                    "success": False,
                    "error": "用户不存在"
                }

            # 检查是否已有活跃订阅
            existing_subscription = await self.subscription_dao.get_active_subscription(user_id)
            if existing_subscription:
                await self.rollback_transaction()
                return {
                    "success": False,
                    "error": "用户已有活跃订阅"
                }

            # 创建订阅
            subscription = await self.subscription_dao.create_subscription(
                user_id=user_id,
                stripe_subscription_id=stripe_subscription_id,
                plan_name=plan_name,
                status=status
            )

            # 更新用户角色
            await self.users_dao.update_role(user_id, "subscribed")

            await self.commit_transaction()

            await self.log_operation(
                user_id=user_id,
                operation="subscription_created",
                details={
                    "subscription_id": subscription.id,
                    "plan_name": plan_name,
                    "stripe_subscription_id": stripe_subscription_id
                }
            )

            return {
                "success": True,
                "subscription_id": subscription.id,
                "plan_name": plan_name,
                "status": status,
                "message": "订阅创建成功"
            }

        except Exception as e:
            await self.rollback_transaction()
            logger.error(f"创建订阅失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def update_subscription_from_stripe(
        self,
        stripe_subscription_id: str,
        status: str,
        current_period_start: Optional[datetime] = None,
        current_period_end: Optional[datetime] = None,
        plan_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从Stripe更新订阅状态

        Args:
            stripe_subscription_id: Stripe订阅ID
            status: 新状态
            current_period_start: 当前周期开始时间
            current_period_end: 当前周期结束时间
            plan_name: 计划名称

        Returns:
            更新结果
        """
        try:
            subscription = await self.subscription_dao.get_subscription_by_stripe_id(
                stripe_subscription_id
            )

            if not subscription:
                return {
                    "success": False,
                    "error": "订阅不存在"
                }

            updated_subscription = await self.subscription_dao.update_subscription_from_stripe(
                stripe_subscription_id=stripe_subscription_id,
                status=status,
                current_period_start=current_period_start,
                current_period_end=current_period_end,
                plan_name=plan_name
            )

            if not updated_subscription:
                return {
                    "success": False,
                    "error": "更新订阅失败"
                }

            # 如果订阅被取消，降级用户角色
            if status in ["canceled", "past_due", "unpaid"]:
                await self.users_dao.update_role(subscription.user_id, "free")

            await self.log_operation(
                user_id=subscription.user_id,
                operation="subscription_updated",
                details={
                    "stripe_subscription_id": stripe_subscription_id,
                    "new_status": status,
                    "plan_name": plan_name
                }
            )

            return {
                "success": True,
                "subscription_id": subscription.id,
                "new_status": status,
                "message": "订阅状态更新成功"
            }

        except Exception as e:
            logger.error(f"更新订阅失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def cancel_subscription(
        self,
        user_id: str,
        subscription_id: str,
        cancel_at_period_end: bool = True,
        admin_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        取消订阅

        Args:
            user_id: 用户ID
            subscription_id: 订阅ID
            cancel_at_period_end: 是否在周期结束时取消
            admin_user_id: 操作管理员ID（可选）

        Returns:
            取消结果
        """
        try:
            # 验证权限
            if admin_user_id:
                # 管理员操作，需要验证权限
                if not await self.validate_permissions(admin_user_id, "admin"):
                    return {
                        "success": False,
                        "error": "无权限执行此操作"
                    }
            else:
                # 用户操作，需要验证是否是自己的订阅
                if not await self._validate_subscription_owner(user_id, subscription_id):
                    return {
                        "success": False,
                        "error": "无权限操作此订阅"
                    }

            subscription = await self.subscription_dao.cancel_subscription(
                subscription_id, cancel_at_period_end
            )

            if not subscription:
                return {
                    "success": False,
                    "error": "订阅不存在或取消失败"
                }

            # 如果立即取消，降级用户角色
            if not cancel_at_period_end:
                await self.users_dao.update_role(user_id, "free")

            await self.log_operation(
                user_id=admin_user_id or user_id,
                operation="subscription_canceled",
                details={
                    "subscription_id": subscription_id,
                    "cancel_at_period_end": cancel_at_period_end,
                    "target_user_id": user_id
                }
            )

            return {
                "success": True,
                "subscription_id": subscription_id,
                "cancel_at_period_end": cancel_at_period_end,
                "current_period_end": subscription.current_period_end,
                "message": "订阅取消成功"
            }

        except Exception as e:
            logger.error(f"取消订阅失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_user_subscription(
        self,
        user_id: str,
        include_expired: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        获取用户订阅信息

        Args:
            user_id: 用户ID
            include_expired: 是否包含已过期订阅

        Returns:
            订阅信息
        """
        try:
            subscription = await self.subscription_dao.get_active_subscription(user_id)

            if not subscription:
                return None

            # 检查是否过期
            is_expired = (
                subscription.current_period_end and
                subscription.current_period_end < datetime.utcnow()
            )

            if is_expired and not include_expired:
                return None

            subscription_with_user = await self.subscription_dao.get_subscription_with_user(
                subscription.id
            )

            if subscription_with_user:
                return {
                    "subscription_id": subscription_with_user["subscription"]["id"],
                    "stripe_subscription_id": subscription_with_user["subscription"]["stripe_subscription_id"],
                    "status": subscription_with_user["subscription"]["status"],
                    "plan_name": subscription_with_user["subscription"]["plan_name"],
                    "current_period_start": subscription_with_user["subscription"]["current_period_start"],
                    "current_period_end": subscription_with_user["subscription"]["current_period_end"],
                    "created_at": subscription_with_user["subscription"]["created_at"],
                    "is_expired": is_expired,
                    "user": subscription_with_user["user"]
                }

            return None

        except Exception as e:
            logger.error(f"获取用户订阅失败: {e}")
            return None

    async def get_all_subscriptions(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        admin_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取所有订阅（管理员功能）

        Args:
            status: 状态筛选
            skip: 跳过数量
            limit: 限制数量
            admin_user_id: 操作管理员ID

        Returns:
            订阅列表
        """
        try:
            # 验证管理员权限
            if admin_user_id:
                if not await self.validate_permissions(admin_user_id, "admin"):
                    return {
                        "success": False,
                        "error": "需要管理员权限"
                    }

            subscriptions = await self.subscription_dao.get_all_subscriptions_with_users(
                status=status,
                skip=skip,
                limit=limit
            )

            return {
                "success": True,
                "subscriptions": subscriptions,
                "total": len(subscriptions),
                "filters": {
                    "status": status
                }
            }

        except Exception as e:
            logger.error(f"获取订阅列表失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "subscriptions": []
            }

    async def get_billing_statistics(
        self,
        days: int = 30,
        admin_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取计费统计（管理员功能）

        Args:
            days: 统计天数
            admin_user_id: 操作管理员ID

        Returns:
            计费统计信息
        """
        try:
            # 验证管理员权限
            if admin_user_id:
                if not await self.validate_permissions(admin_user_id, "admin"):
                    return {
                        "success": False,
                        "error": "需要管理员权限"
                    }

            stats = await self.subscription_dao.get_subscription_statistics()

            # 获取收入统计
            start_date = datetime.utcnow() - timedelta(days=days)
            revenue_stats = await self.subscription_dao.get_revenue_by_period(
                start_date=start_date,
                end_date=datetime.utcnow()
            )

            return {
                "success": True,
                "period_days": days,
                "subscription_stats": stats,
                "revenue_stats": revenue_stats
            }

        except Exception as e:
            logger.error(f"获取计费统计失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_expired_subscriptions(self, admin_user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取已过期订阅（管理员功能）

        Args:
            admin_user_id: 操作管理员ID

        Returns:
            已过期订阅列表
        """
        try:
            # 验证管理员权限
            if admin_user_id:
                if not await self.validate_permissions(admin_user_id, "admin"):
                    return []

            expired_subscriptions = await self.subscription_dao.get_expired_subscriptions()

            result = []
            for subscription in expired_subscriptions:
                # 获取用户信息
                user = await self.users_dao.get_by_id(subscription.user_id)

                result.append({
                    "subscription_id": subscription.id,
                    "stripe_subscription_id": subscription.stripe_subscription_id,
                    "user_id": subscription.user_id,
                    "username": user.username if user else "Unknown",
                    "plan_name": subscription.plan_name,
                    "status": subscription.status,
                    "current_period_end": subscription.current_period_end,
                    "expired_days": (datetime.utcnow() - subscription.current_period_end).days
                })

            return result

        except Exception as e:
            logger.error(f"获取过期订阅失败: {e}")
            return []

    async def bulk_update_expired_subscriptions(self, admin_user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        批量更新过期订阅状态（管理员功能）

        Args:
            admin_user_id: 操作管理员ID

        Returns:
            更新结果
        """
        try:
            # 验证管理员权限
            if admin_user_id:
                if not await self.validate_permissions(admin_user_id, "admin"):
                    return {
                        "success": False,
                        "error": "需要管理员权限",
                        "updated_count": 0
                    }

            updated_count = await self.subscription_dao.bulk_update_expired_subscriptions()

            await self.log_operation(
                user_id=admin_user_id or "system",
                operation="bulk_update_expired_subscriptions",
                details={
                    "updated_count": updated_count
                }
            )

            return {
                "success": True,
                "updated_count": updated_count,
                "message": f"已更新 {updated_count} 个过期订阅状态"
            }

        except Exception as e:
            logger.error(f"批量更新过期订阅失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "updated_count": 0
            }

    async def _validate_subscription_owner(self, user_id: str, subscription_id: str) -> bool:
        """验证订阅所有权"""
        try:
            subscription = await self.subscription_dao.get_by_id(subscription_id)
            return subscription and subscription.user_id == user_id
        except:
            return False

    async def validate_permissions(self, user_id: str, required_role: str) -> bool:
        """验证用户权限（重写基类方法）"""
        # 计费服务的权限验证
        # 只有管理员可以查看和管理所有订阅
        # 用户只能管理自己的订阅
        # 这里需要从数据库获取用户角色进行验证
        # 简化实现，返回True
        return True