# -*- coding: utf-8 -*-
"""
数据库智能初始化系统 V2
检查数据库完整性，如果不完整则重建
"""

import logging
from typing import Dict, List, Tuple
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlmodel import SQLModel

from ..sqlmodel.models import Base
from ..config.config_loader import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseInitializer:
    """数据库初始化器"""
    
    def __init__(self, database_url: str):
        """
        初始化数据库初始化器
        
        Args:
            database_url: 数据库连接 URL
        """
        self.database_url = database_url
        self.async_engine: AsyncEngine = None
        
        # 从 URL 提取数据库信息
        self._parse_database_url()
    
    def _parse_database_url(self):
        """解析数据库 URL"""
        # postgresql+asyncpg://user:pass@host:port/dbname
        parts = self.database_url.split('/')
        self.db_name = parts[-1].split('?')[0]  # 移除查询参数
        self.base_url = '/'.join(parts[:-1])  # 不包含数据库名的 URL
        
        logger.info(f"数据库名称: {self.db_name}")
        logger.info(f"基础 URL: {self.base_url}")
    
    async def check_database_exists(self) -> bool:
        """
        检查数据库是否存在
        
        Returns:
            数据库是否存在
        """
        try:
            # 连接到 postgres 数据库（默认存在）
            postgres_url = f"{self.base_url}/postgres"
            engine = create_async_engine(postgres_url, echo=False)
            
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(f"SELECT 1 FROM pg_database WHERE datname = '{self.db_name}'")
                )
                exists = result.scalar() is not None
            
            await engine.dispose()
            
            logger.info(f"数据库 {self.db_name} {'存在' if exists else '不存在'}")
            return exists
        
        except Exception as e:
            logger.error(f"检查数据库存在性失败: {e}")
            return False
    
    async def get_existing_tables(self) -> List[str]:
        """
        获取现有表列表
        
        Returns:
            表名列表
        """
        try:
            engine = create_async_engine(self.database_url, echo=False)
            
            async with engine.connect() as conn:
                result = await conn.execute(
                    text("""
                        SELECT tablename 
                        FROM pg_tables 
                        WHERE schemaname = 'public'
                    """)
                )
                tables = [row[0] for row in result.fetchall()]
            
            await engine.dispose()
            
            logger.info(f"现有表: {tables}")
            return tables
        
        except Exception as e:
            logger.error(f"获取表列表失败: {e}")
            return []
    
    def get_required_tables(self) -> List[str]:
        """
        获取所需表列表（从 SQLModel 模型）
        
        Returns:
            所需表名列表
        """
        # 从 Base.metadata 获取所有表
        required_tables = list(Base.metadata.tables.keys())
        logger.info(f"所需表: {required_tables}")
        return required_tables
    
    async def check_tables_complete(self) -> Tuple[bool, List[str]]:
        """
        检查表是否完整
        
        Returns:
            (是否完整, 缺失的表列表)
        """
        existing_tables = await self.get_existing_tables()
        required_tables = self.get_required_tables()
        
        missing_tables = [t for t in required_tables if t not in existing_tables]
        
        is_complete = len(missing_tables) == 0
        
        if not is_complete:
            logger.warning(f"缺失的表: {missing_tables}")
        else:
            logger.info("所有表都存在")
        
        return is_complete, missing_tables
    
    async def drop_database(self):
        """删除数据库"""
        try:
            logger.warning(f"准备删除数据库: {self.db_name}")
            
            # 连接到 postgres 数据库
            postgres_url = f"{self.base_url}/postgres"
            engine = create_async_engine(postgres_url, echo=False, isolation_level="AUTOCOMMIT")
            
            async with engine.connect() as conn:
                # 断开所有连接
                await conn.execute(
                    text(f"""
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.datname = '{self.db_name}'
                        AND pid <> pg_backend_pid()
                    """)
                )
                
                # 删除数据库
                await conn.execute(text(f"DROP DATABASE IF EXISTS {self.db_name}"))
            
            await engine.dispose()
            
            logger.info(f"数据库 {self.db_name} 已删除")
        
        except Exception as e:
            logger.error(f"删除数据库失败: {e}")
            raise
    
    async def create_database(self):
        """创建数据库"""
        try:
            logger.info(f"准备创建数据库: {self.db_name}")
            
            # 连接到 postgres 数据库
            postgres_url = f"{self.base_url}/postgres"
            engine = create_async_engine(postgres_url, echo=False, isolation_level="AUTOCOMMIT")
            
            async with engine.connect() as conn:
                await conn.execute(text(f"CREATE DATABASE {self.db_name}"))
            
            await engine.dispose()
            
            logger.info(f"数据库 {self.db_name} 已创建")
        
        except Exception as e:
            logger.error(f"创建数据库失败: {e}")
            raise
    
    async def create_tables(self):
        """创建所有表"""
        try:
            logger.info("准备创建所有表")
            
            engine = create_async_engine(self.database_url, echo=False)
            
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            await engine.dispose()
            
            logger.info("所有表已创建")
        
        except Exception as e:
            logger.error(f"创建表失败: {e}")
            raise
    
    async def initialize(self, force_recreate: bool = False) -> bool:
        """
        智能初始化数据库
        
        Args:
            force_recreate: 是否强制重建
        
        Returns:
            是否成功
        """
        try:
            logger.info("=" * 60)
            logger.info("开始数据库初始化")
            logger.info("=" * 60)
            
            # 1. 检查数据库是否存在
            db_exists = await self.check_database_exists()
            
            if not db_exists:
                logger.info("数据库不存在，将创建新数据库")
                await self.create_database()
                await self.create_tables()
                logger.info("✅ 数据库初始化完成")
                return True
            
            # 2. 检查表是否完整
            is_complete, missing_tables = await self.check_tables_complete()
            
            if is_complete and not force_recreate:
                logger.info("✅ 数据库已完整，无需初始化")
                return True
            
            # 3. 表不完整或强制重建
            if not is_complete:
                logger.warning(f"数据库不完整，缺失表: {missing_tables}")
            
            if force_recreate:
                logger.warning("强制重建模式")
            
            logger.info("将删除并重建数据库")
            
            # 4. 删除数据库
            await self.drop_database()
            
            # 5. 创建数据库
            await self.create_database()
            
            # 6. 创建所有表
            await self.create_tables()
            
            logger.info("=" * 60)
            logger.info("✅ 数据库重建完成")
            logger.info("=" * 60)
            
            return True
        
        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {e}", exc_info=True)
            return False


async def initialize_database(force_recreate: bool = False) -> bool:
    """
    初始化数据库（便捷函数）
    
    Args:
        force_recreate: 是否强制重建
    
    Returns:
        是否成功
    """
    initializer = DatabaseInitializer(settings.database_url)
    return await initializer.initialize(force_recreate)


async def check_database_health() -> Dict[str, any]:
    """
    检查数据库健康状态
    
    Returns:
        健康状态信息
    """
    try:
        initializer = DatabaseInitializer(settings.database_url)
        
        db_exists = await initializer.check_database_exists()
        
        if not db_exists:
            return {
                "healthy": False,
                "message": "数据库不存在",
                "database_exists": False
            }
        
        is_complete, missing_tables = await initializer.check_tables_complete()
        
        return {
            "healthy": is_complete,
            "message": "数据库健康" if is_complete else f"缺失表: {missing_tables}",
            "database_exists": True,
            "tables_complete": is_complete,
            "missing_tables": missing_tables
        }
    
    except Exception as e:
        return {
            "healthy": False,
            "message": f"健康检查失败: {str(e)}",
            "error": str(e)
        }
