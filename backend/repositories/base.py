"""Shared PostgreSQL access; unavailable or failed storage never looks like success."""

from abc import ABC
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import json
import logging

import asyncpg

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Match existing PostgreSQL TIMESTAMP columns, which store naive UTC."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DatabaseUnavailableError(RuntimeError):
    """The required database connection pool is unavailable."""


class BaseDAO(ABC):
    _pool: Optional[asyncpg.Pool] = None
    _use_database: bool = False

    @classmethod
    async def init_pool(cls, dsn: str, min_size: int = 5, max_size: int = 20):
        if BaseDAO._pool is None:
            BaseDAO._pool = await asyncpg.create_pool(
                dsn, min_size=min_size, max_size=max_size,
                server_settings={"timezone": "UTC"},
            )
            BaseDAO._use_database = True
            logger.info("Database connection pool initialized")

    @classmethod
    async def close_pool(cls):
        pool = BaseDAO._pool
        BaseDAO._pool = None
        BaseDAO._use_database = False
        if pool is not None:
            await pool.close()

    @classmethod
    def is_database_enabled(cls) -> bool:
        return BaseDAO._use_database and BaseDAO._pool is not None

    def _require_pool(self):
        if not self.is_database_enabled():
            raise DatabaseUnavailableError("Database is not initialized")
        return BaseDAO._pool

    @staticmethod
    def _row_to_dict(row) -> Dict[str, Any]:
        result = dict(row)
        # asyncpg returns JSON/JSONB as strings unless a codec is configured.
        for key in ("metadata", "preferences"):
            if isinstance(result.get(key), str):
                result[key] = json.loads(result[key])
        return result

    async def execute_query(self, query: str, params: Optional[Tuple] = None) -> Any:
        async with self._require_pool().acquire() as conn:
            return await conn.execute(query, *(params or ()))

    async def fetch_one(
        self, query: str, params: Optional[Tuple] = None
    ) -> Optional[Dict[str, Any]]:
        async with self._require_pool().acquire() as conn:
            row = await conn.fetchrow(query, *(params or ()))
            return self._row_to_dict(row) if row is not None else None

    async def fetch_all(
        self, query: str, params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        async with self._require_pool().acquire() as conn:
            rows = await conn.fetch(query, *(params or ()))
            return [self._row_to_dict(row) for row in rows]
