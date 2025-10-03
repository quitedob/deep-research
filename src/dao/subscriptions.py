# -*- coding: utf-8 -*-
"""
SubscriptionsDAO：用户订阅的查询与写入（Stripe 状态同步）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.sqlmodel.models import Subscription


class SubscriptionsDAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_by_user(self, user_id: int) -> Optional[Subscription]:
        res = await self.session.execute(
            select(Subscription).where(Subscription.user_id == user_id, Subscription.status == "active")
        )
        return res.scalar_one_or_none()

    async def upsert_by_stripe(self,
                               *,
                               user_id: int,
                               stripe_customer_id: Optional[str],
                               stripe_subscription_id: Optional[str],
                               status: str,
                               current_period_end: Optional[datetime],
                               plan_name: Optional[str]) -> Subscription:
        res = await self.session.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
        )
        sub = res.scalar_one_or_none()
        if sub is None:
            sub = Subscription(
                user_id=user_id,
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id,
                status=status,
                current_period_end=current_period_end,
                plan_name=plan_name,
            )
            self.session.add(sub)
        else:
            sub.user_id = user_id
            sub.stripe_customer_id = stripe_customer_id
            sub.status = status
            sub.current_period_end = current_period_end
            sub.plan_name = plan_name
        await self.session.flush()
        return sub


