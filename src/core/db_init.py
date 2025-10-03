# -*- coding: utf-8 -*-
"""
数据库初始化模块
负责数据库连接测试和表结构创建
"""

from __future__ import annotations

import logging
from typing import List

from sqlalchemy.ext.asyncio import AsyncEngine

from src.core.db import db_manager
from src.sqlmodel.models import Base
from src.sqlmodel import rag_models

logger = logging.getLogger(__name__)


async def init_database_and_tables(database_url: str) -> bool:
    """
    初始化数据库连接并创建表结构

    Args:
        database_url: 数据库连接字符串

    Returns:
        bool: 初始化是否成功
    """
    try:
        # 初始化数据库引擎
        db_manager.init_engine()

        # 测试数据库连接
        engine = db_manager.engine
        async with engine.begin() as conn:
            # 测试连接
            await conn.execute("SELECT 1")

        logger.info("数据库连接测试成功")

        # 如果启用了自动创建表，则创建表结构
        settings = db_manager.settings
        if settings.auto_create_tables:
            await _create_tables(engine)
            logger.info("数据库表结构创建完成")

        return True

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


async def _create_tables(engine: AsyncEngine) -> None:
    """创建数据库表结构"""
    try:
        # 创建基础表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("基础表创建完成")

        # 创建RAG相关表
        if rag_models.RAGBase:
            async with engine.begin() as conn:
                await conn.run_sync(rag_models.RAGBase.metadata.create_all)
                logger.info("RAG表创建完成")

    except Exception as e:
        logger.error(f"表创建失败: {e}")
        raise


async def check_database_connection() -> bool:
    """检查数据库连接状态"""
    try:
        db_manager.init_engine()
        engine = db_manager.engine

        async with engine.begin() as conn:
            await conn.execute("SELECT 1")

        return True

    except Exception as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False
