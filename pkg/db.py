# -*- coding: utf-8 -*-
"""
数据库连接与会话管理（PostgreSQL + 可选 pgvector 初始化）。
最小可用：读取环境/配置，提供 asyncpg/SQLAlchemy 2.0 异步引擎与会话生成器。
"""

from __future__ import annotations

import os
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker, AsyncSession


_engine: Optional[AsyncEngine] = None
_sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None


def _database_url_from_env() -> str:
    """从环境变量构造数据库 URL，默认本地 Postgres；无则退回 SQLite 内存占位。"""
    url = os.getenv("DATABASE_URL")
    if url:
        # 统一为 async 驱动（psycopg）
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url
    # 占位（开发无 Postgres 时可运行）
    return "sqlite+aiosqlite:///:memory:"


def init_engine(echo: bool = False) -> AsyncEngine:
    """初始化全局异步引擎。重复调用将复用现有实例。"""
    global _engine, _sessionmaker
    if _engine is not None:
        return _engine
    db_url = _database_url_from_env()
    _engine = create_async_engine(db_url, echo=echo, future=True)
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """获取全局 sessionmaker（若未初始化则自动初始化）。"""
    global _sessionmaker
    if _sessionmaker is None:
        init_engine(echo=False)
    assert _sessionmaker is not None
    return _sessionmaker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：获取一个异步会话。"""
    session_maker = get_sessionmaker()
    async with session_maker() as session:
        yield session


