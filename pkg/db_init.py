#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化工具 - PostgreSQL专用，自动创建数据库和表
"""

import asyncio
import logging
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

logger = logging.getLogger(__name__)


async def create_database_if_not_exists(database_url: str) -> bool:
    """
    检查PostgreSQL数据库是否存在，如果不存在则创建

    Args:
        database_url: 完整的PostgreSQL数据库连接URL

    Returns:
        bool: 是否成功创建或确认数据库存在
    """
    try:
        # 解析数据库URL
        parsed = urlparse(database_url)

        # 验证是PostgreSQL URL
        if not parsed.scheme.startswith('postgresql'):
            logger.error(f"不支持的数据库类型: {parsed.scheme}，只支持PostgreSQL")
            return False

        database_name = parsed.path.lstrip('/')

        if not database_name:
            logger.error("数据库名称为空")
            return False

        # 构造连接到默认数据库（postgres）的URL
        server_url = f"{parsed.scheme}://{parsed.netloc}/postgres"

        logger.info(f"连接到PostgreSQL服务器: {server_url}")
        logger.info(f"检查数据库: {database_name}")

        # 连接到默认的postgres数据库
        engine = create_async_engine(server_url, echo=False)

        async with engine.begin() as conn:
            # 检查数据库是否存在
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": database_name}
            )

            if result.fetchone():
                logger.info(f"数据库 '{database_name}' 已存在")
            else:
                # 创建数据库
                logger.info(f"创建数据库 '{database_name}'...")
                await conn.execute(
                    text("CREATE DATABASE :db_name WITH ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8' TEMPLATE=template0"),
                    {"db_name": database_name}
                )
                logger.info(f"数据库 '{database_name}' 创建成功")

        await engine.dispose()
        return True

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


async def init_database_and_tables(database_url: str) -> bool:
    """
    初始化数据库和表
    
    Args:
        database_url: 数据库连接URL
        
    Returns:
        bool: 是否成功初始化
    """
    try:
        # 1. 创建数据库（如果不存在）
        if not await create_database_if_not_exists(database_url):
            return False
        
        # 2. 连接到指定数据库并创建表
        logger.info("连接到数据库并创建表...")
        engine = create_async_engine(database_url, echo=False)
        
        # 导入所有模型以确保它们被注册到Base
        from src.sqlmodel.models import Base
        from src.sqlmodel import rag_models  # 确保RAG模型被导入
        
        async with engine.begin() as conn:
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
            logger.info("数据库表创建成功")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        logger.error(f"数据库和表初始化失败: {e}")
        return False


if __name__ == "__main__":
    # 测试用
    import os
    import sys
    from pathlib import Path
    from dotenv import load_dotenv

    # 添加项目根目录到Python路径
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    load_dotenv()

    async def test():
        # 使用PostgreSQL默认配置
        default_postgres_url = "postgresql+asyncpg://deerflow:deerflow123@localhost:5432/deerflow"
        db_url = os.getenv("DATABASE_URL", default_postgres_url)
        success = await init_database_and_tables(db_url)
        if success:
            print("✅ PostgreSQL数据库初始化成功")
        else:
            print("❌ PostgreSQL数据库初始化失败")

    asyncio.run(test())