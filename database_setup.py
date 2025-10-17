#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
检查数据库状态，提供警告和自动创建选项
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import asyncpg
import psycopg2
from sqlalchemy import text
from src.config.config_loader import get_settings
from src.core.db import db_manager
from src.sqlmodel.models import Base
from src.sqlmodel import rag_models


class DatabaseManager:
    """数据库管理器，负责检查和初始化数据库"""

    def __init__(self):
        self.settings = get_settings()
        self.db_url = self.settings.database_url
        # 解析数据库连接信息
        self._parse_connection_info()

    def _parse_connection_info(self):
        """解析数据库连接信息"""
        # 示例: postgresql+asyncpg://postgres:1234@localhost:5432/deep_research
        if self.db_url.startswith("postgresql+asyncpg://"):
            # 移除 asyncpg 前缀以使用 psycopg2 检查数据库
            sync_url = self.db_url.replace("postgresql+asyncpg://", "postgresql://")

            # 解析连接信息
            # 格式: postgresql://user:password@host:port/database
            if "@" in sync_url:
                auth_part, host_port_db = sync_url.split("@")
                self.user, self.password = auth_part.replace("postgresql://", "").split(":")

                if "/" in host_port_db:
                    host_port, self.database = host_port_db.split("/")
                    if ":" in host_port:
                        self.host, self.port = host_port.split(":")
                        self.port = int(self.port)
                    else:
                        self.host = host_port
                        self.port = 5432
                else:
                    self.host = "localhost"
                    self.port = 5432
                    self.database = host_port_db

    async def check_database_exists(self) -> bool:
        """检查数据库是否存在"""
        try:
            # 连接到PostgreSQL默认数据库（通常是postgres）
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database='postgres'  # 默认数据库
            )

            # 检查目标数据库是否存在
            result = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", self.database
            )

            await conn.close()
            return result is not None

        except Exception as e:
            print(f"检查数据库存在性时出错: {e}")
            return False

    async def create_database(self) -> bool:
        """创建数据库"""
        try:
            # 连接到默认数据库
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database='postgres'
            )

            # 创建数据库
            await conn.execute(f'CREATE DATABASE "{self.database}"')
            await conn.close()

            print(f"数据库 '{self.database}' 创建成功")
            return True

        except Exception as e:
            print(f"❌ 创建数据库失败: {e}")
            return False

    async def check_database_has_data(self) -> bool:
        """检查数据库是否包含数据"""
        try:
            # 初始化数据库引擎
            db_manager.init_engine()

            async with db_manager.get_session() as session:
                # 检查关键表是否有数据
                tables_to_check = [
                    'users', 'conversation_sessions', 'conversation_messages',
                    'documents', 'chunks', 'evidence'
                ]

                for table_name in tables_to_check:
                    try:
                        result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        count = result.scalar()
                        if count > 0:
                            print(f"⚠️  表 '{table_name}' 包含 {count} 条记录")
                            return True
                    except Exception:
                        # 表可能不存在，继续检查下一个
                        continue

                print("✅ 数据库为空，可以安全初始化")
                return False

        except Exception as e:
            print(f"检查数据库数据时出错: {e}")
            return False

    async def check_tables_exist(self) -> list:
        """检查哪些表已存在"""
        existing_tables = []
        try:
            db_manager.init_engine()

            async with db_manager.get_session() as session:
                # 获取所有表名
                result = await session.execute(text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """))
                tables = [row[0] for row in result.fetchall()]
                existing_tables = tables

        except Exception as e:
            print(f"检查表存在性时出错: {e}")

        return existing_tables

    async def create_tables(self) -> bool:
        """创建所有表"""
        try:
            print("🔧 正在创建数据库表...")

            # 初始化数据库引擎
            db_manager.init_engine()

            # 创建所有表
            async with db_manager.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            print("✅ 所有数据库表创建成功")
            return True

        except Exception as e:
            print(f"❌ 创建表失败: {e}")
            return False

    async def drop_all_tables(self) -> bool:
        """删除所有表（危险操作）"""
        try:
            print("🗑️  正在删除所有数据库表...")

            # 初始化数据库引擎
            db_manager.init_engine()

            # 删除所有表
            async with db_manager.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

            print("✅ 所有表已删除")
            return True

        except Exception as e:
            print(f"❌ 删除表失败: {e}")
            return False

    async def get_user_confirmation(self, message: str) -> bool:
        """获取用户确认"""
        while True:
            response = input(f"{message} (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("请输入 'y' 或 'n'")

    async def initialize_database(self, force_recreate: bool = False) -> bool:
        """完整的数据库初始化流程"""
        print("🚀 开始数据库初始化流程...")
        print(f"📍 数据库连接: {self.host}:{self.port}/{self.database}")

        # 1. 检查数据库是否存在
        print("\n📋 检查数据库是否存在...")
        db_exists = await self.check_database_exists()

        if not db_exists:
            print("❌ 数据库不存在")
            if await self.get_user_confirmation("是否创建新数据库？"):
                if not await self.create_database():
                    print("❌ 数据库初始化失败")
                    return False
            else:
                print("❌ 用户取消操作")
                return False
        else:
            print("✅ 数据库已存在")

        # 2. 检查表和数据状态
        print("\n📋 检查数据库状态...")
        existing_tables = await self.check_tables_exist()
        has_data = await self.check_database_has_data()

        if existing_tables:
            print(f"📊 已存在的表: {', '.join(existing_tables)}")

        # 3. 根据情况处理
        if has_data and not force_recreate:
            print("\n⚠️  警告：数据库包含数据！")
            print("选项:")
            print("1. 关闭程序，手动备份数据")
            print("2. 强制删除所有数据并重新创建（危险）")
            print("3. 尝试只创建缺失的表（保守）")

            choice = input("请选择 (1/2/3): ").strip()

            if choice == '1':
                print("❌ 用户选择关闭程序")
                print("请手动备份数据库后重新运行")
                return False
            elif choice == '2':
                if await self.get_user_confirmation("⚠️  确认要删除所有数据吗？此操作不可撤销！"):
                    await self.drop_all_tables()
                    return await self.create_tables()
                else:
                    print("❌ 用户取消操作")
                    return False
            elif choice == '3':
                print("🔧 尝试只创建缺失的表...")
                return await self.create_tables()
            else:
                print("❌ 无效选择")
                return False
        else:
            # 数据库为空或强制重建
            if force_recreate and existing_tables:
                if await self.get_user_confirmation("⚠️  确认要删除现有表并重新创建吗？"):
                    await self.drop_all_tables()

            return await self.create_tables()

    async def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            db_manager.init_engine()
            async with db_manager.get_session() as session:
                await session.execute(text("SELECT 1"))
            print("✅ 数据库连接测试成功")
            return True
        except Exception as e:
            print(f"❌ 数据库连接测试失败: {e}")
            return False


async def main():
    """主函数"""
    print("=" * 60)
    print("Deep Research Platform - 数据库初始化工具")
    print("=" * 60)

    # 创建数据库管理器
    db_mgr = DatabaseManager()

    # 测试基础连接
    print("\n🔌 测试数据库连接...")
    if not await db_mgr.test_connection():
        print("❌ 无法连接到数据库，请检查:")
        print("1. PostgreSQL 服务是否运行")
        print("2. 连接参数是否正确")
        print("3. 用户权限是否足够")
        return False

    # 检查命令行参数
    force_recreate = '--force' in sys.argv or '--recreate' in sys.argv

    if force_recreate:
        print("⚠️  强制重建模式：将删除所有现有数据")

    # 执行初始化
    try:
        success = await db_mgr.initialize_database(force_recreate=force_recreate)

        if success:
            print("\n🎉 数据库初始化完成！")
            print("现在可以启动应用程序了:")
            print("source .venv/Scripts/activate && python app.py")
        else:
            print("\n❌ 数据库初始化失败")
            return False

    except KeyboardInterrupt:
        print("\n❌ 用户中断操作")
        return False
    except Exception as e:
        print(f"\n❌ 初始化过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    # 运行初始化
    success = asyncio.run(main())
    sys.exit(0 if success else 1)