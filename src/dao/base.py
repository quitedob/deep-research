# -*- coding: utf-8 -*-
"""
Base Repository Interface
Defines the standard interface that all DAOs should follow for consistent data access patterns.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

# Generic type for model classes
ModelType = TypeVar("ModelType")

class BaseRepository(ABC, Generic[ModelType]):
    """
    Base repository interface that defines standard CRUD operations.
    All concrete repositories should inherit from this base class.
    """

    def __init__(self, session: AsyncSession, model_class: type[ModelType]):
        self.session = session
        self.model_class = model_class

    async def create(self, **kwargs) -> ModelType:
        """Create a new record with the given attributes."""
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_by_id(self, id: str) -> Optional[ModelType]:
        """Get a record by its primary key."""
        result = await self.session.execute(
            select(self.model_class).where(self.model_class.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """Get all records with pagination."""
        query = select(self.model_class)

        if order_by:
            # Handle basic order_by clauses
            if hasattr(self.model_class, order_by):
                query = query.order_by(getattr(self.model_class, order_by))

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters."""
        query = select(func.count(self.model_class.id))

        if filters:
            conditions = []
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    conditions.append(getattr(self.model_class, key) == value)

            if conditions:
                query = query.where(and_(*conditions))

        result = await self.session.execute(query)
        return result.scalar()

    async def update(
        self,
        id: str,
        update_data: Dict[str, Any]
    ) -> Optional[ModelType]:
        """Update a record by ID."""
        instance = await self.get_by_id(id)
        if not instance:
            return None

        for key, value in update_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.session.flush()
        return instance

    async def delete(self, id: str) -> bool:
        """Delete a record by ID."""
        instance = await self.get_by_id(id)
        if not instance:
            return False

        await self.session.delete(instance)
        await self.session.flush()
        return True

    async def exists(self, filters: Dict[str, Any]) -> bool:
        """Check if a record exists matching the given filters."""
        conditions = []
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                conditions.append(getattr(self.model_class, key) == value)

        if not conditions:
            return False

        query = select(func.count(self.model_class.id)).where(and_(*conditions))
        result = await self.session.execute(query)
        return result.scalar() > 0

    async def find_one(self, filters: Dict[str, Any]) -> Optional[ModelType]:
        """Find one record matching the given filters."""
        conditions = []
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                conditions.append(getattr(self.model_class, key) == value)

        if not conditions:
            return None

        query = select(self.model_class).where(and_(*conditions))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def find_many(
        self,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """Find many records matching optional filters."""
        query = select(self.model_class)

        if filters:
            conditions = []
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    conditions.append(getattr(self.model_class, key) == value)

            if conditions:
                query = query.where(and_(*conditions))

        if order_by and hasattr(self.model_class, order_by):
            query = query.order_by(getattr(self.model_class, order_by))

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()


class FilterBuilder:
    """Helper class for building complex filter queries."""

    def __init__(self, model_class: type[ModelType]):
        self.model_class = model_class
        self.conditions = []

    def add_filter(self, field: str, value: Any, operator: str = "eq") -> FilterBuilder:
        """Add a filter condition."""
        if not hasattr(self.model_class, field):
            return self

        field_attr = getattr(self.model_class, field)

        if operator == "eq":
            self.conditions.append(field_attr == value)
        elif operator == "ne":
            self.conditions.append(field_attr != value)
        elif operator == "like":
            self.conditions.append(field_attr.like(value))
        elif operator == "ilike":
            self.conditions.append(field_attr.ilike(value))
        elif operator == "in":
            self.conditions.append(field_attr.in_(value))
        elif operator == "not_in":
            self.conditions.append(field_attr.notin_(value))
        elif operator == "gt":
            self.conditions.append(field_attr > value)
        elif operator == "gte":
            self.conditions.append(field_attr >= value)
        elif operator == "lt":
            self.conditions.append(field_attr < value)
        elif operator == "lte":
            self.conditions.append(field_attr <= value)

        return self

    def add_date_range_filter(
        self,
        field: str,
        start_date: Optional[Any],
        end_date: Optional[Any]
    ) -> FilterBuilder:
        """Add a date range filter."""
        if not hasattr(self.model_class, field):
            return self

        field_attr = getattr(self.model_class, field)

        if start_date:
            self.conditions.append(field_attr >= start_date)

        if end_date:
            self.conditions.append(field_attr <= end_date)

        return self

    def build(self):
        """Return the built conditions."""
        return self.conditions