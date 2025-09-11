# -*- coding: utf-8 -*-
"""
UsersDAO：用户数据的增删改查。
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.sqlmodel.models import User


class UsersDAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, *, username: str, email: str, password_hash: str, role: str = "free") -> User:
        user = User(username=username, email=email, password_hash=password_hash, role=role)
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        res = await self.session.execute(select(User).where(User.id == user_id))
        return res.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        res = await self.session.execute(select(User).where(User.username == username))
        return res.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        res = await self.session.execute(select(User).where(User.email == email))
        return res.scalar_one_or_none()

    async def update_role(self, user_id: int, role: str) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False
        user.role = role
        await self.session.flush()
        return True


