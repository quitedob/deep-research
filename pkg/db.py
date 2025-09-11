# -*- coding: utf-8 -*-
"""
数据库连接与会话管理 (PostgreSQL + pgvector)。
读取环境/配置，提供 asyncpg/SQLAlchemy 2.0 异步引擎与会话生成器。
"""
from __future__ import annotations

import os
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_engine: Optional[AsyncEngine] = None
_sessionmaker: Optional[async_sessionmaker] = None


def _get_database_url() -> str:
    """从环境变量获取数据库URL，如果未设置则抛出错误。"""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL 环境变量未设置。")

    # 确保使用 asyncpg 驱动
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if not url.startswith("postgresql+asyncpg://"):
        raise ValueError("数据库只支持 PostgreSQL (postgresql+asyncpg://).")

    return url


def init_engine(echo: bool = False) -> AsyncEngine:
    """初始化全局异步引擎。重复调用将复用现有实例。"""
    global _engine, _sessionmaker
    if _engine is not None:
        return _engine

    db_url = _get_database_url()
    _engine = create_async_engine(db_url, echo=echo, future=True)
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_sessionmaker() -> async_sessionmaker:
    """获取全局 sessionmaker（若未初始化则自动初始化）。"""
    global _sessionmaker
    if _sessionmaker is None:
        init_engine()
    assert _sessionmaker is not None
    return _sessionmaker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：获取一个异步会话。"""
    session_maker = get_sessionmaker()
    async with session_maker() as session:
        yield session


