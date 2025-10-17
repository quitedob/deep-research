#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化的数据库初始化脚本
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import asyncpg
from sqlalchemy import text
from src.config.config_loader import get_settings
from src.core.db import db_manager
from src.sqlmodel.models import Base
from src.sqlmodel import rag_models


def get_connection_info():
    """获取数据库连接信息"""
    settings = get_settings()
    db_url = settings.database_url

    # 解析连接信息
    if db_url.startswith("postgresql+asyncpg://"):
        sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

        # 格式: postgresql://user:password@host:port/database
        if "@" in sync_url:
            auth_part, host_port_db = sync_url.split("@")
            user, password = auth_part.replace("postgresql://", "").split(":")

            if "/" in host_port_db:
                host_port, database = host_port_db.split("/")
                if ":" in host_port:
                    host, port = host_port.split(":")
                    port = int(port)
                else:
                    host = host_port
                    port = 5432
            else:
                host = "localhost"
                port = 5432
                database = host_port_db

            return {
                'host': host,
                'port': port,
                'user': user,
                'password': password,
                'database': database
            }

    return None


async def check_database_exists(conn_info):
    """检查数据库是否存在"""
    try:
        conn = await asyncpg.connect(
            host=conn_info['host'],
            port=conn_info['port'],
            user=conn_info['user'],
            password=conn_info['password'],
            database='postgres'
        )

        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", conn_info['database']
        )

        await conn.close()
        return result is not None

    except Exception as e:
        print(f"检查数据库存在性时出错: {e}")
        return False


async def create_database(conn_info):
    """创建数据库"""
    try:
        conn = await asyncpg.connect(
            host=conn_info['host'],
            port=conn_info['port'],
            user=conn_info['user'],
            password=conn_info['password'],
            database='postgres'
        )

        await conn.execute(f'CREATE DATABASE "{conn_info["database"]}"')
        await conn.close()

        print(f"数据库 '{conn_info['database']}' 创建成功")
        return True

    except Exception as e:
        print(f"创建数据库失败: {e}")
        return False


async def check_has_data():
    """检查数据库是否包含数据"""
    try:
        db_manager.init_engine()

        async with db_manager.get_session() as session:
            tables_to_check = [
                'users', 'conversation_sessions', 'conversation_messages',
                'documents', 'chunks', 'evidence'
            ]

            for table_name in tables_to_check:
                try:
                    result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    if count > 0:
                        print(f"警告: 表 '{table_name}' 包含 {count} 条记录")
                        return True
                except Exception:
                    continue

            print("数据库为空，可以安全初始化")
            return False

    except Exception as e:
        print(f"检查数据库数据时出错: {e}")
        return False


async def create_tables():
    """创建所有表"""
    try:
        print("正在创建数据库表...")

        db_manager.init_engine()

        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("所有数据库表创建成功")
        return True

    except Exception as e:
        print(f"创建表失败: {e}")
        return False


async def test_connection():
    """测试数据库连接"""
    try:
        db_manager.init_engine()
        async with db_manager.get_session() as session:
            await session.execute(text("SELECT 1"))
        print("数据库连接测试成功")
        return True
    except Exception as e:
        print(f"数据库连接测试失败: {e}")
        return False


async def main():
    """主函数"""
    print("=" * 60)
    print("Deep Research Platform - 数据库初始化工具")
    print("=" * 60)

    # 获取连接信息
    conn_info = get_connection_info()
    if not conn_info:
        print("无法解析数据库连接信息")
        return False

    print(f"数据库连接: {conn_info['host']}:{conn_info['port']}/{conn_info['database']}")

    # 测试基础连接
    print("\n测试数据库连接...")
    if not await test_connection():
        print("无法连接到数据库，请检查:")
        print("1. PostgreSQL 服务是否运行")
        print("2. 连接参数是否正确")
        print("3. 用户权限是否足够")
        return False

    # 检查数据库是否存在
    print("\n检查数据库是否存在...")
    db_exists = await check_database_exists(conn_info)

    if not db_exists:
        print("数据库不存在")
        response = input("是否创建新数据库？(y/n): ").strip().lower()
        if response in ['y', 'yes']:
            if not await create_database(conn_info):
                print("数据库创建失败")
                return False
        else:
            print("用户取消操作")
            return False
    else:
        print("数据库已存在")

    # 检查数据状态
    print("\n检查数据库状态...")
    has_data = await check_has_data()

    if has_data:
        print("\n警告: 数据库包含数据！")
        print("选项:")
        print("1. 关闭程序，手动备份数据")
        print("2. 强制删除所有数据并重新创建（危险）")
        print("3. 尝试只创建缺失的表（保守）")

        choice = input("请选择 (1/2/3): ").strip()

        if choice == '1':
            print("用户选择关闭程序")
            print("请手动备份数据库后重新运行")
            return False
        elif choice == '2':
            response = input("确认要删除所有数据吗？此操作不可撤销！(y/n): ").strip().lower()
            if response in ['y', 'yes']:
                # 删除所有表
                try:
                    async with db_manager.engine.begin() as conn:
                        await conn.run_sync(Base.metadata.drop_all)
                    print("所有表已删除")
                    return await create_tables()
                except Exception as e:
                    print(f"删除表失败: {e}")
                    return False
            else:
                print("用户取消操作")
                return False
        elif choice == '3':
            print("尝试只创建缺失的表...")
            return await create_tables()
        else:
            print("无效选择")
            return False
    else:
        # 数据库为空，直接创建表
        return await create_tables()


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if success:
            print("\n数据库初始化完成！")
            print("现在可以启动应用程序了:")
            print("source .venv/Scripts/activate && python app.py")
        else:
            print("\n数据库初始化失败")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n初始化过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)