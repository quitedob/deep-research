#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Data Access Object
Provides common database operations for all DAOs
"""

from abc import ABC
from typing import Any, Dict, List, Optional, Tuple
import asyncpg
import logging

logger = logging.getLogger(__name__)


class BaseDAO(ABC):
    """
    Base Data Access Object class
    Provides common database operations and utilities
    """
    
    # 全局连接池
    _pool: Optional[asyncpg.Pool] = None
    _use_database: bool = False

    def __init__(self):
        """Initialize the base DAO"""
        pass
    
    @classmethod
    async def init_pool(cls, dsn: str, min_size: int = 5, max_size: int = 20):
        """
        初始化数据库连接池
        
        Args:
            dsn: 数据库连接字符串
            min_size: 最小连接数
            max_size: 最大连接数
        """
        if cls._pool is None:
            try:
                cls._pool = await asyncpg.create_pool(
                    dsn,
                    min_size=min_size,
                    max_size=max_size
                )
                cls._use_database = True
                logger.info("✓ 数据库连接池初始化成功")
            except Exception as e:
                logger.error(f"数据库连接池初始化失败: {e}")
                cls._use_database = False
    
    @classmethod
    async def close_pool(cls):
        """关闭数据库连接池"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            cls._use_database = False
            logger.info("数据库连接池已关闭")
    
    @classmethod
    def is_database_enabled(cls) -> bool:
        """检查数据库是否启用"""
        return cls._use_database and cls._pool is not None

    async def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None
    ) -> Any:
        """
        Execute a database query
        
        Args:
            query: SQL query string
            params: Query parameters as tuple
            
        Returns:
            Query result
        """
        if not self.is_database_enabled():
            logger.debug("数据库未启用，跳过查询")
            return None
        
        try:
            async with self._pool.acquire() as conn:
                if params:
                    return await conn.execute(query, *params)
                else:
                    return await conn.execute(query)
        except Exception as e:
            logger.error(f"执行查询失败: {e}")
            logger.debug(f"查询: {query}")
            logger.debug(f"参数: {params}")
            raise

    async def fetch_one(
        self, 
        query: str, 
        params: Optional[Tuple] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row from the database
        
        Args:
            query: SQL query string
            params: Query parameters as tuple
            
        Returns:
            Single row as dictionary or None
        """
        if not self.is_database_enabled():
            logger.debug("数据库未启用，返回 None")
            return None
        
        try:
            async with self._pool.acquire() as conn:
                if params:
                    row = await conn.fetchrow(query, *params)
                else:
                    row = await conn.fetchrow(query)
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"查询单行失败: {e}")
            logger.debug(f"查询: {query}")
            logger.debug(f"参数: {params}")
            return None

    async def fetch_all(
        self, 
        query: str, 
        params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all rows from the database
        
        Args:
            query: SQL query string
            params: Query parameters as tuple
            
        Returns:
            List of rows as dictionaries
        """
        if not self.is_database_enabled():
            logger.debug("数据库未启用，返回空列表")
            return []
        
        try:
            async with self._pool.acquire() as conn:
                if params:
                    rows = await conn.fetch(query, *params)
                else:
                    rows = await conn.fetch(query)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"查询多行失败: {e}")
            logger.debug(f"查询: {query}")
            logger.debug(f"参数: {params}")
            return []
