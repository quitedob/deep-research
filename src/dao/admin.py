# -*- coding: utf-8 -*-
"""
AdminDAO: Administrative data access operations.
Provides high-level methods for user management, statistics, and audit operations.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.sqlmodel.models import User, AdminAuditLog, Subscription, ConversationSession, ConversationMessage, ApiUsageLog
from src.sqlmodel.rag_models import DocumentProcessingJob, Chunk as DocumentChunk
from .base import BaseRepository, FilterBuilder


class AdminDAO(BaseRepository[User]):
    """Data access object for administrative operations on users and related data."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    # ==================== User Management ====================

    async def get_users_with_filters(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[User]:
        """Get users with advanced filtering options."""
        query = select(User)

        # Build filter conditions
        conditions = []
        if role:
            conditions.append(User.role == role)
        if is_active is not None:
            conditions.append(User.is_active == is_active)
        if search:
            # Search in username and email
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term) if User.email.type else False
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Add pagination and ordering
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_user_statistics(self) -> Dict[str, int]:
        """Get comprehensive user statistics."""
        stats = {}

        # Total users
        total_result = await self.session.execute(select(func.count(User.id)))
        stats["total_users"] = total_result.scalar()

        # Active users
        active_result = await self.session.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        stats["active_users"] = active_result.scalar()

        # Users by role
        for role in ["admin", "subscribed", "free"]:
            role_result = await self.session.execute(
                select(func.count(User.id)).where(User.role == role)
            )
            stats[f"{role}_users"] = role_result.scalar()

        return stats

    async def toggle_user_status(self, user_id: str) -> Optional[User]:
        """Toggle a user's active status."""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        user.is_active = not user.is_active
        await self.session.flush()
        return user

    async def update_user_role(self, user_id: str, new_role: str) -> Optional[User]:
        """Update a user's role."""
        if new_role not in ["free", "subscribed", "admin"]:
            raise ValueError(f"Invalid role: {new_role}")

        return await self.update(user_id, {"role": new_role})

    # ==================== Subscription Management ====================

    async def get_all_subscriptions(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
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
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "plan_name": subscription.plan_name,
                "created_at": subscription.created_at
            })

        return subscriptions

    async def update_subscription_status(self, subscription_id: str, new_status: str) -> Optional[Subscription]:
        """Update subscription status."""
        valid_statuses = ["active", "canceled", "past_due", "unpaid", "incomplete"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")

        subscription_query = select(Subscription).where(Subscription.id == subscription_id)
        result = await self.session.execute(subscription_query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            return None

        subscription.status = new_status
        await self.session.flush()
        return subscription

    # ==================== Conversation Management ====================

    async def get_user_conversations(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's conversation sessions with message counts."""
        # Verify user exists
        user = await self.get_by_id(user_id)
        if not user:
            return []

        # Get conversation sessions
        query = select(ConversationSession).where(
            ConversationSession.user_id == user_id
        ).order_by(ConversationSession.updated_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        sessions = result.scalars().all()

        # Get message counts for each session
        sessions_with_count = []
        for session in sessions:
            count_query = select(func.count(ConversationMessage.id)).where(
                ConversationMessage.session_id == session.id
            )
            count_result = await self.session.execute(count_query)
            message_count = count_result.scalar()

            sessions_with_count.append({
                "id": str(session.id),
                "user_id": str(session.user_id),
                "title": session.title,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "message_count": message_count
            })

        return sessions_with_count

    # ==================== Document Management ====================

    async def get_user_documents(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's document processing jobs."""
        # Verify user exists
        user = await self.get_by_id(user_id)
        if not user:
            return []

        query = select(DocumentProcessingJob).where(
            DocumentProcessingJob.user_id == user_id
        ).order_by(DocumentProcessingJob.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        jobs = result.scalars().all()

        return [
            {
                "id": str(job.id),
                "filename": job.filename,
                "status": job.status,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "error_message": job.error_message
            }
            for job in jobs
        ]

    # ==================== API Usage Management ====================

    async def get_user_api_usage(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ApiUsageLog]:
        """Get user's API usage logs."""
        # Verify user exists
        user = await self.get_by_id(user_id)
        if not user:
            return []

        query = select(ApiUsageLog).where(
            ApiUsageLog.user_id == user_id
        ).order_by(ApiUsageLog.timestamp.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    # ==================== Research Reports Management ====================

    async def get_all_research_reports(
        self,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all research reports (document chunks)."""
        query = select(DocumentChunk).order_by(
            DocumentChunk.created_at.desc()
        ).offset(skip).limit(limit)

        result = await self.session.execute(query)
        chunks = result.scalars().all()

        # Group by document_id
        documents = {}
        for chunk in chunks:
            doc_id = chunk.document_id
            if doc_id not in documents:
                documents[doc_id] = {
                    "document_id": doc_id,
                    "chunks": [],
                    "total_chunks": 0,
                    "created_at": chunk.created_at
                }

            documents[doc_id]["chunks"].append({
                "id": str(chunk.id),
                "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                "chunk_index": chunk.chunk_index
            })
            documents[doc_id]["total_chunks"] += 1

        return list(documents.values())

    async def get_research_report_detail(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed research report by document ID."""
        query = select(DocumentChunk).where(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index)

        result = await self.session.execute(query)
        chunks = result.scalars().all()

        if not chunks:
            return None

        # Merge all chunk contents
        full_content = "\n\n".join([chunk.content for chunk in chunks])

        return {
            "document_id": document_id,
            "total_chunks": len(chunks),
            "content": full_content,
            "chunks": [
                {
                    "id": str(chunk.id),
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "metadata": chunk.metadata
                }
                for chunk in chunks
            ],
            "created_at": chunks[0].created_at if chunks else None
        }

    # ==================== Audit Log Management ====================

    async def get_audit_logs_with_filters(
        self,
        admin_user_id: Optional[str] = None,
        action: Optional[str] = None,
        target_user_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[AdminAuditLog], int]:
        """Get audit logs with comprehensive filtering."""
        # Build count query for total
        count_query = select(func.count(AdminAuditLog.id))
        filters = []

        if admin_user_id:
            filters.append(AdminAuditLog.admin_user_id == admin_user_id)
        if action:
            filters.append(AdminAuditLog.action == action)
        if target_user_id:
            filters.append(AdminAuditLog.target_user_id == target_user_id)
        if status:
            filters.append(AdminAuditLog.status == status)
        if start_date:
            filters.append(AdminAuditLog.timestamp >= start_date)
        if end_date:
            filters.append(AdminAuditLog.timestamp <= end_date)

        if filters:
            count_query = count_query.where(and_(*filters))

        total_result = await self.session.execute(count_query)
        total = total_result.scalar()

        # Build main query
        query = select(AdminAuditLog)
        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(AdminAuditLog.timestamp.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        logs = result.scalars().all()

        return logs, total

    async def get_audit_log_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get audit log statistical summary."""
        from datetime import timedelta

        start_date = datetime.utcnow() - timedelta(days=days)

        # Total operations
        total_ops_result = await self.session.execute(
            select(func.count(AdminAuditLog.id))
            .where(AdminAuditLog.timestamp >= start_date)
        )
        total_operations = total_ops_result.scalar()

        # Action breakdown
        action_stats_result = await self.session.execute(
            select(
                AdminAuditLog.action,
                func.count(AdminAuditLog.id).label('count')
            )
            .where(AdminAuditLog.timestamp >= start_date)
            .group_by(AdminAuditLog.action)
            .order_by(func.count(AdminAuditLog.id).desc())
        )
        action_stats = action_stats_result.fetchall()

        # Status breakdown
        status_stats_result = await self.session.execute(
            select(
                AdminAuditLog.status,
                func.count(AdminAuditLog.id).label('count')
            )
            .where(AdminAuditLog.timestamp >= start_date)
            .group_by(AdminAuditLog.status)
        )
        status_stats = status_stats_result.fetchall()

        # Active admins
        active_admins_result = await self.session.execute(
            select(func.count(func.distinct(AdminAuditLog.admin_user_id)))
            .where(AdminAuditLog.timestamp >= start_date)
        )
        active_admins = active_admins_result.scalar()

        # Daily operations (last 7 days)
        daily_start = datetime.utcnow() - timedelta(days=7)
        daily_ops_result = await self.session.execute(
            select(
                func.date(AdminAuditLog.timestamp).label('date'),
                func.count(AdminAuditLog.id).label('count')
            )
            .where(AdminAuditLog.timestamp >= daily_start)
            .group_by(func.date(AdminAuditLog.timestamp))
            .order_by(func.date(AdminAuditLog.timestamp))
        )
        daily_ops = daily_ops_result.fetchall()

        return {
            "summary": {
                "total_operations": total_operations,
                "active_admins": active_admins,
                "period_days": days
            },
            "action_breakdown": [
                {"action": row.action, "count": row.count}
                for row in action_stats
            ],
            "status_breakdown": [
                {"status": row.status, "count": row.count}
                for row in status_stats
            ],
            "daily_operations": [
                {"date": str(row.date), "count": row.count}
                for row in daily_ops
            ]
        }