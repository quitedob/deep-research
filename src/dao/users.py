# -*- coding: utf-8 -*-
"""
UsersDAO：用户数据的增删改查。
Standardized to use the BaseRepository interface.
"""

from __future__ import annotations

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.sqlmodel.models import User
from .base import BaseRepository


class UsersDAO(BaseRepository[User]):
    """Data access object for user operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return await self.find_one({"username": username})

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return await self.find_one({"email": email})

    async def update_role(self, user_id: str, role: str) -> bool:
        """Update user role."""
        if role not in ["free", "subscribed", "admin"]:
            raise ValueError(f"Invalid role: {role}")

        updated_user = await self.update(user_id, {"role": role})
        return updated_user is not None

    async def update_active_status(self, user_id: str, is_active: bool) -> bool:
        """Update user active status."""
        updated_user = await self.update(user_id, {"is_active": is_active})
        return updated_user is not None

    async def get_users_by_role(self, role: str, skip: int = 0, limit: int = 100) -> list[User]:
        """Get users by role with pagination."""
        return await self.find_many(
            filters={"role": role},
            skip=skip,
            limit=limit,
            order_by="created_at"
        )

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get active users with pagination."""
        return await self.find_many(
            filters={"is_active": True},
            skip=skip,
            limit=limit,
            order_by="created_at"
        )

    async def search_users(self, search_term: str, skip: int = 0, limit: int = 100) -> list[User]:
        """Search users by username or email."""
        # This would need a more complex implementation with ILIKE
        # For now, we'll use the base find_many with basic filters
        from sqlalchemy import select, or_
        from sqlalchemy.ext.asyncio import AsyncSession

        search_pattern = f"%{search_term}%"
        query = select(User).where(
            or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern) if User.email.type else False
            )
        ).offset(skip).limit(limit).order_by(User.created_at.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_by_role(self, role: str) -> int:
        """Count users by role."""
        return await self.count({"role": role})

    async def count_active_users(self) -> int:
        """Count active users."""
        return await self.count({"is_active": True})


