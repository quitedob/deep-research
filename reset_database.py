#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置PostgreSQL数据库 - 删除并重新创建
"""

import asyncio
import logging
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv
import os

load_dotenv()

async def reset_database():
    """删除并重新创建PostgreSQL数据库"""
    try:
        # 使用PostgreSQL默认配置
        default_postgres_url = "postgresql+asyncpg://deerflow:deerflow123@localhost:5432/deerflow"
        database_url = os.getenv("DATABASE_URL", default_postgres_url)

        # 解析数据库URL
        parsed = urlparse(database_url)

        # 验证是PostgreSQL URL
        if not parsed.scheme.startswith('postgresql'):
            print(f"❌ 不支持的数据库类型: {parsed.scheme}，只支持PostgreSQL")
            return False

        database_name = parsed.path.lstrip('/')
        server_url = f"{parsed.scheme}://{parsed.netloc}/postgres"

        print(f"🗑️  删除PostgreSQL数据库 '{database_name}'...")

        # 连接到默认的postgres数据库
        engine = create_async_engine(server_url, echo=False)

        async with engine.begin() as conn:
            # 强制断开所有连接到目标数据库的连接
            await conn.execute(
                text("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = :db_name AND pid <> pg_backend_pid()
                """),
                {"db_name": database_name}
            )

            # 删除数据库（如果存在）
            await conn.execute(text("DROP DATABASE IF EXISTS :db_name"), {"db_name": database_name})
            print(f"✅ 数据库 '{database_name}' 已删除")

            # 重新创建数据库
            await conn.execute(
                text("""
                    CREATE DATABASE :db_name
                    WITH ENCODING 'UTF8'
                    LC_COLLATE='en_US.UTF-8'
                    LC_CTYPE='en_US.UTF-8'
                    TEMPLATE=template0
                """),
                {"db_name": database_name}
            )
            print(f"✅ 数据库 '{database_name}' 已重新创建")

        await engine.dispose()

        # 现在初始化表
        print("🏗️  创建数据库表...")
        from pkg.db_init import init_database_and_tables

        success = await init_database_and_tables(database_url)
        if success:
            print("✅ PostgreSQL数据库重置成功！")
            return True
        else:
            print("❌ 表创建失败")
            return False

    except Exception as e:
        print(f"❌ PostgreSQL数据库重置失败: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(reset_database())