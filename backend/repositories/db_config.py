#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库配置
PostgreSQL 连接配置和管理
"""

import os
from urllib.parse import quote, urlparse
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "5432"))
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "")
        self.database = os.getenv("DB_NAME", "deep_research")
        self.min_pool_size = int(os.getenv("DB_MIN_POOL_SIZE", "5"))
        self.max_pool_size = int(os.getenv("DB_MAX_POOL_SIZE", "20"))
        if self.database_url:
            parsed = urlparse(self.database_url)
            if parsed.scheme not in ("postgres", "postgresql"):
                raise ValueError("DATABASE_URL must use postgres:// or postgresql://")
            from urllib.parse import unquote
            self.host = parsed.hostname or self.host
            self.port = parsed.port or self.port
            self.user = unquote(parsed.username) if parsed.username else self.user
            self.password = unquote(parsed.password) if parsed.password else self.password
            self.database = unquote(parsed.path.lstrip("/")) or self.database
    
    def get_dsn(self) -> str:
        """获取数据库连接字符串"""
        if self.database_url:
            return self.database_url
        host = f"[{self.host}]" if ":" in self.host else self.host
        return f"postgresql://{quote(self.user, safe='')}:{quote(self.password, safe='')}@{host}:{self.port}/{quote(self.database, safe='')}"
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """验证配置是否完整"""
        if not self.password and not self.database_url:
            return False, "数据库密码未配置，请设置 DB_PASSWORD 环境变量"
        if not self.user:
            return False, "数据库用户未配置，请设置 DB_USER 环境变量"
        return True, None


# 全局配置实例
db_config = DatabaseConfig()
