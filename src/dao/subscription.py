# -*- coding: utf-8 -*-
"""
SubscriptionDAO: Subscription and billing data access operations.
Provides high-level methods for subscription management, billing operations, and user plan management.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.sqlmodel.models import Subscription, User
from .base import BaseRepository, FilterBuilder


class SubscriptionDAO(BaseRepository[Subscription]):
    """Data access object for subscription and billing operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Subscription)

    async def create_subscription(
        self,
        user_id: str,
        stripe_subscription_id: str,
        plan_name: str,
        status: str = "incomplete"
    ) -> Subscription:
        """Create a new subscription."""
        subscription = Subscription(
            user_id=user_id,
            stripe_subscription_id=stripe_subscription_id,
            plan_name=plan_name,
            status=status
        )
        self.session.add(subscription)
        await self.session.flush()
        return subscription

    async def get_subscription_by_stripe_id(self, stripe_subscription_id: str) -> Optional[Subscription]:
        """Get subscription by Stripe subscription ID."""
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_subscription_id
            )
        )
        return result.scalar_one_or_none()

    async def get_active_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get the active subscription for a user."""
        result = await self.session.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.status == "active"
                )
            ).order_by(Subscription.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def get_user_subscriptions(
        self,
        user_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
    ) -> List[Subscription]:
        """Get all subscriptions for a user with optional status filter."""
        query = select(Subscription).where(Subscription.user_id == user_id)

        if status:
            query = query.where(Subscription.status == status)

        query = query.order_by(Subscription.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_subscription_status(
        self,
        subscription_id: str,
        new_status: str,
        period_end: Optional[datetime] = None
    ) -> Optional[Subscription]:
        """Update subscription status and optionally period end."""
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            return None

        valid_statuses = ["active", "canceled", "past_due", "unpaid", "incomplete", "incomplete_expired"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")

        subscription.status = new_status

        if period_end:
            subscription.current_period_end = period_end

        await self.session.flush()
        return subscription

    async def update_subscription_from_stripe(
        self,
        stripe_subscription_id: str,
        status: str,
        current_period_start: Optional[datetime] = None,
        current_period_end: Optional[datetime] = None,
        plan_name: Optional[str] = None
    ) -> Optional[Subscription]:
        """Update subscription from Stripe webhook data."""
        subscription = await self.get_subscription_by_stripe_id(stripe_subscription_id)
        if not subscription:
            return None

        subscription.status = status

        if current_period_start:
            subscription.current_period_start = current_period_start

        if current_period_end:
            subscription.current_period_end = current_period_end

        if plan_name:
            subscription.plan_name = plan_name

        await self.session.flush()
        return subscription

    async def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> Optional[Subscription]:
        """Cancel a subscription."""
        subscription = await self.get_by_id(subscription_id)
        if not subscription:
            return None

        subscription.status = "canceled"

        # If not canceling at period end, set end date to now
        if not at_period_end:
            subscription.current_period_end = datetime.utcnow()

        await self.session.flush()
        return subscription

    async def get_expiring_subscriptions(self, days: int = 7) -> List[Subscription]:
        """Get subscriptions that will expire in the next N days."""
        future_date = datetime.utcnow() + timedelta(days=days)

        query = select(Subscription).where(
            and_(
                Subscription.status == "active",
                Subscription.current_period_end <= future_date,
                Subscription.current_period_end > datetime.utcnow()
            )
        ).order_by(Subscription.current_period_end.asc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_expired_subscriptions(self) -> List[Subscription]:
        """Get subscriptions that have expired but are still marked as active."""
        query = select(Subscription).where(
            and_(
                Subscription.status == "active",
                Subscription.current_period_end < datetime.utcnow()
            )
        ).order_by(Subscription.current_period_end.asc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_subscription_statistics(self) -> Dict[str, Any]:
        """Get comprehensive subscription statistics."""
        stats = {}

        # Total subscriptions
        total_result = await self.session.execute(
            select(func.count(Subscription.id))
        )
        stats["total_subscriptions"] = total_result.scalar()

        # Active subscriptions
        active_result = await self.session.execute(
            select(func.count(Subscription.id)).where(Subscription.status == "active")
        )
        stats["active_subscriptions"] = active_result.scalar()

        # Subscriptions by status
        status_query = select(
            Subscription.status,
            func.count(Subscription.id).label('count')
        ).group_by(Subscription.status)

        status_result = await self.session.execute(status_query)
        status_stats = status_result.fetchall()

        stats["by_status"] = {
            row.status: row.count for row in status_stats
        }

        # Subscriptions by plan
        plan_query = select(
            Subscription.plan_name,
            func.count(Subscription.id).label('count')
        ).where(
            Subscription.status == "active"
        ).group_by(Subscription.plan_name)

        plan_result = await self.session.execute(plan_query)
        plan_stats = plan_result.fetchall()

        stats["by_plan"] = {
            row.plan_name: row.count for row in plan_stats
        }

        # Monthly recurring revenue (MRR) - simplified calculation
        # This would need actual pricing logic based on plan names
        from sqlalchemy import case
        mrr_query = select(
            func.sum(
                case(
                    (Subscription.plan_name.ilike('%basic%'), 9.99),
                    (Subscription.plan_name.ilike('%pro%'), 29.99),
                    (Subscription.plan_name.ilike('%enterprise%'), 99.99),
                    else_=0.0
                )
            )
        ).where(Subscription.status == "active")

        mrr_result = await self.session.execute(mrr_query)
        stats["estimated_mrr"] = float(mrr_result.scalar() or 0.0)

        # New subscriptions this month
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_result = await self.session.execute(
            select(func.count(Subscription.id))
            .where(Subscription.created_at >= current_month_start)
        )
        stats["new_this_month"] = new_result.scalar()

        # Churned subscriptions this month (canceled or expired)
        churn_result = await self.session.execute(
            select(func.count(Subscription.id))
            .where(
                and_(
                    Subscription.status.in_(["canceled", "past_due"]),
                    Subscription.updated_at >= current_month_start
                )
            )
        )
        stats["churned_this_month"] = churn_result.scalar()

        return stats

    async def get_subscription_with_user(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription details with user information."""
        query = select(Subscription, User).join(
            User, Subscription.user_id == User.id
        ).where(Subscription.id == subscription_id)

        result = await self.session.execute(query)
        row = result.first()

        if not row:
            return None

        subscription, user = row

        return {
            "subscription": {
                "id": str(subscription.id),
                "stripe_subscription_id": subscription.stripe_subscription_id,
                "status": subscription.status,
                "plan_name": subscription.plan_name,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "created_at": subscription.created_at
            },
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }

    async def get_all_subscriptions_with_users(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all subscriptions with user information."""
        query = select(Subscription, User).join(
            User, Subscription.user_id == User.id
        )

        if status:
            query = query.where(Subscription.status == status)

        query = query.order_by(Subscription.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        rows = result.fetchall()

        subscriptions = []
        for subscription, user in rows:
            subscriptions.append({
                "id": str(subscription.id),
                "user_id": str(subscription.user_id),
                "username": user.username if user else "Unknown",
                "email": user.email if user else None,
                "stripe_subscription_id": subscription.stripe_subscription_id,
                "status": subscription.status,
                "plan_name": subscription.plan_name,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "created_at": subscription.created_at,
                "updated_at": subscription.updated_at
            })

        return subscriptions

    async def bulk_update_expired_subscriptions(self) -> int:
        """Update all expired active subscriptions to 'past_due' status."""
        query = select(Subscription.id).where(
            and_(
                Subscription.status == "active",
                Subscription.current_period_end < datetime.utcnow()
            )
        )

        result = await self.session.execute(query)
        subscription_ids = [row[0] for row in result.fetchall()]

        if not subscription_ids:
            return 0

        # Update the subscriptions
        from sqlalchemy import update
        update_stmt = update(Subscription).where(
            Subscription.id.in_(subscription_ids)
        ).values(status="past_due")

        await self.session.execute(update_stmt)
        await self.session.flush()

        return len(subscription_ids)

    async def get_revenue_by_period(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get revenue statistics for a specific period."""
        # This is a simplified version - real implementation would need
        # actual payment/transaction data from Stripe

        query = select(
            func.count(Subscription.id).label('new_subscriptions'),
            func.sum(
                case(
                    (Subscription.plan_name.ilike('%basic%'), 9.99),
                    (Subscription.plan_name.ilike('%pro%'), 29.99),
                    (Subscription.plan_name.ilike('%enterprise%'), 99.99),
                    else_=0.0
                )
            ).label('estimated_revenue')
        ).where(
            and_(
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date
            )
        )

        result = await self.session.execute(query)
        row = result.first()

        return {
            "period_start": start_date,
            "period_end": end_date,
            "new_subscriptions": row.new_subscriptions or 0,
            "estimated_revenue": float(row.estimated_revenue or 0.0)
        }