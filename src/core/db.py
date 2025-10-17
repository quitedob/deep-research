# -*- coding: utf-8 -*-
"""
数据库连接和会话管理模块
提供数据库引擎初始化和会话获取功能
"""

from __future__ import annotations

import contextlib
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.config.config_loader import get_settings


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        """初始化数据库管理器"""
        self.settings = get_settings()
        self._engine = None
        self._async_session_factory = None

    def init_engine(self) -> None:
        """初始化数据库引擎"""
        if self._engine is None:
            database_url = self.settings.database_url

            # 如果是SQLite，使用StaticPool以支持多线程
            if database_url.startswith("sqlite"):
                connect_args = {
                    "check_same_thread": False,
                }
                poolclass = StaticPool
            else:
                connect_args = {}
                poolclass = None

            self._engine = create_async_engine(
                database_url,
                echo=self.settings.debug,
                future=True,
                connect_args=connect_args,
                poolclass=poolclass,
            )

            self._async_session_factory = async_sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False
            )

    @property
    def engine(self):
        """获取数据库引擎"""
        if self._engine is None:
            self.init_engine()
        return self._engine

    @contextlib.asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        if self._async_session_factory is None:
            self.init_engine()

        async with self._async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# 全局数据库管理器实例
db_manager = DatabaseManager()


def init_engine() -> None:
    """初始化数据库引擎（兼容旧接口）"""
    db_manager.init_engine()


@contextlib.asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（兼容旧接口）"""
    async with db_manager.get_session() as session:
        yield session


# 为向后兼容添加别名
get_async_session = get_db_session
