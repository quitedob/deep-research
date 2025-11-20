#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化和验证
自动检查数据库、表结构，不符合要求则重建
"""

import asyncpg
import logging
from typing import Dict, List, Optional
from src.dao.db_config import db_config
from src.dao.db_schema import ALL_TABLES, TABLE_SCHEMAS

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """数据库初始化器"""
    
    def __init__(self):
        self.config = db_config
    
    async def check_and_init_database(self) -> bool:
        """
        检查并初始化数据库
        
        Returns:
            是否成功初始化
        """
        try:
            # 1. 验证配置
            is_valid, error = self.config.validate()
            if not is_valid:
                logger.warning(f"数据库配置无效: {error}")
                logger.info("将使用内存模式运行（数据不会持久化）")
                return False
            
            # 2. 检查数据库是否存在
            logger.info("检查数据库连接...")
            db_exists = await self._check_database_exists()
            
            if not db_exists:
                logger.info(f"数据库 '{self.config.database}' 不存在，尝试创建...")
                created = await self._create_database()
                if not created:
                    logger.warning("无法创建数据库，将使用内存模式")
                    return False
            
            # 3. 检查并初始化表
            logger.info("检查数据库表结构...")
            await self._check_and_init_tables()
            
            logger.info("✓ 数据库初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            logger.info("将使用内存模式运行（数据不会持久化）")
            return False
    
    async def _check_database_exists(self) -> bool:
        """检查数据库是否存在"""
        try:
            # 连接到 postgres 数据库检查目标数据库是否存在
            conn = await asyncpg.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database='postgres'
            )
            
            result = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                self.config.database
            )
            
            await conn.close()
            return result is not None
            
        except Exception as e:
            logger.error(f"检查数据库存在性失败: {e}")
            return False
    
    async def _create_database(self) -> bool:
        """创建数据库"""
        try:
            conn = await asyncpg.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database='postgres'
            )
            
            # 不能在事务中创建数据库
            await conn.execute(f'CREATE DATABASE {self.config.database}')
            await conn.close()
            
            logger.info(f"✓ 数据库 '{self.config.database}' 创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建数据库失败: {e}")
            return False
    
    async def _check_and_init_tables(self):
        """检查并初始化所有表"""
        conn = await asyncpg.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database
        )
        
        try:
            for table_name, create_sql in ALL_TABLES.items():
                logger.info(f"检查表: {table_name}")
                
                # 检查表是否存在
                table_exists = await self._table_exists(conn, table_name)
                
                if table_exists:
                    # 验证表结构
                    is_valid = await self._validate_table_schema(conn, table_name)
                    
                    if not is_valid:
                        logger.warning(f"表 '{table_name}' 结构不符合要求，重建中...")
                        await self._drop_table(conn, table_name)
                        await self._create_table(conn, table_name, create_sql)
                    else:
                        logger.info(f"✓ 表 '{table_name}' 结构正确")
                else:
                    logger.info(f"表 '{table_name}' 不存在，创建中...")
                    await self._create_table(conn, table_name, create_sql)
            
            # 创建测试用户（如果不存在）
            await self._create_test_users(conn)
                    
        finally:
            await conn.close()
    
    async def _table_exists(self, conn: asyncpg.Connection, table_name: str) -> bool:
        """检查表是否存在"""
        result = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = $1
            )
            """,
            table_name
        )
        return result
    
    async def _validate_table_schema(
        self, 
        conn: asyncpg.Connection, 
        table_name: str
    ) -> bool:
        """
        验证表结构是否符合要求
        
        Returns:
            True 如果结构正确，False 如果需要重建
        """
        if table_name not in TABLE_SCHEMAS:
            return True  # 没有定义验证规则，认为正确
        
        expected_schema = TABLE_SCHEMAS[table_name]
        expected_columns = expected_schema["columns"]
        
        # 获取实际的列信息
        actual_columns = await conn.fetch(
            """
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = $1
            ORDER BY ordinal_position
            """,
            table_name
        )
        
        actual_column_dict = {}
        for col in actual_columns:
            col_name = col['column_name']
            # 处理数组类型
            if col['data_type'] == 'ARRAY':
                data_type = 'ARRAY'
            else:
                data_type = col['data_type']
            actual_column_dict[col_name] = data_type
        
        # 检查列是否匹配
        for col_name, expected_type in expected_columns.items():
            if col_name not in actual_column_dict:
                logger.warning(f"表 '{table_name}' 缺少列: {col_name}")
                return False
            
            actual_type = actual_column_dict[col_name]
            
            # 类型匹配检查（简化版）
            if not self._types_match(expected_type, actual_type):
                logger.warning(
                    f"表 '{table_name}' 列 '{col_name}' 类型不匹配: "
                    f"期望 {expected_type}, 实际 {actual_type}"
                )
                return False
        
        return True
    
    def _types_match(self, expected: str, actual: str) -> bool:
        """检查数据类型是否匹配"""
        # 简化的类型匹配
        type_mappings = {
            "character varying": ["character varying", "varchar", "text"],
            "text": ["text", "character varying"],
            "integer": ["integer", "int", "int4"],
            "double precision": ["double precision", "float8"],
            "timestamp without time zone": ["timestamp without time zone", "timestamp"],
            "ARRAY": ["ARRAY"],
        }
        
        if expected in type_mappings:
            return actual in type_mappings[expected]
        
        return expected.lower() == actual.lower()
    
    async def _drop_table(self, conn: asyncpg.Connection, table_name: str):
        """删除表"""
        await conn.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
        logger.info(f"✓ 表 '{table_name}' 已删除")
    
    async def _create_table(
        self, 
        conn: asyncpg.Connection, 
        table_name: str, 
        create_sql: str
    ):
        """创建表"""
        await conn.execute(create_sql)
        logger.info(f"✓ 表 '{table_name}' 创建成功")
    
    async def _create_test_users(self, conn: asyncpg.Connection):
        """创建测试用户（用于开发和测试）"""
        from datetime import datetime
        
        test_users = [
            ("demo_user_001", "demo_user_001", "demo001@example.com", "Demo User 001"),
            ("demo_user_002", "demo_user_002", "demo002@example.com", "Demo User 002"),
            ("demo_user_003", "demo_user_003", "demo003@example.com", "Demo User 003"),
            ("test_user", "test_user", "test@example.com", "Test User"),
        ]
        
        for user_id, username, email, full_name in test_users:
            # 检查用户是否已存在
            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM users WHERE id = $1)",
                user_id
            )
            
            if not exists:
                now = datetime.utcnow()
                await conn.execute(
                    """
                    INSERT INTO users (id, username, email, password_hash, full_name, is_active, is_verified, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    user_id, username, email, "dummy_hash_for_testing", 
                    full_name, True, True, now, now
                )
                logger.info(f"✓ 创建测试用户: {username}")
            else:
                logger.debug(f"测试用户已存在: {username}")


# 全局初始化器实例
db_initializer = DatabaseInitializer()


async def init_database() -> bool:
    """
    初始化数据库（供外部调用）
    
    Returns:
        是否成功初始化
    """
    return await db_initializer.check_and_init_database()
