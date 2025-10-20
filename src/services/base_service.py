# -*- coding: utf-8 -*-
"""
Base Service Class
为所有服务类提供基础功能和通用方法
"""

from __future__ import annotations

from typing import TypeVar, Generic, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from abc import ABC, abstractmethod

# Generic type for model classes
ModelType = TypeVar("ModelType")


class BaseService(ABC, Generic[ModelType]):
    """
    基础服务类，提供通用的服务层功能
    所有具体服务都应该继承自这个基类
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def begin_transaction(self):
        """开始数据库事务"""
        await self.session.begin()

    async def commit_transaction(self):
        """提交数据库事务"""
        await self.session.commit()

    async def rollback_transaction(self):
        """回滚数据库事务"""
        await self.session.rollback()

    async def validate_permissions(self, user_id: str, required_role: str) -> bool:
        """
        验证用户权限
        子类应该实现具体的权限验证逻辑
        """
        # 这里可以实现通用的权限验证逻辑
        # 具体实现可以由子类覆盖
        return True

    async def log_operation(
        self,
        user_id: str,
        operation: str,
        details: Optional[dict] = None,
        success: bool = True
    ):
        """
        记录操作日志
        子类可以实现具体的日志记录逻辑
        """
        # 这里可以实现通用的操作日志记录
        pass

    def validate_input_data(self, data: dict, required_fields: list) -> bool:
        """
        验证输入数据
        检查必需字段是否存在
        """
        for field in required_fields:
            if field not in data or data[field] is None:
                return False
        return True

    def sanitize_input(self, data: dict) -> dict:
        """
        清理输入数据
        移除不安全的字段或内容
        """
        # 基本的数据清理逻辑
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                # 移除潜在的恶意字符
                sanitized[key] = value.strip()
            else:
                sanitized[key] = value
        return sanitized