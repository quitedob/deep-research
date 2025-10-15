# -*- coding: utf-8 -*-
"""
管理员操作审计服务
提供自动化的管理员操作记录功能
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from sqlalchemy import select, func

from ..sqlmodel.models import AdminAuditLog, User

logger = logging.getLogger(__name__)


class AuditService:
    """审计日志服务"""

    # 操作类型常量
    ACTION_USER_BAN = "USER_BAN"
    ACTION_USER_UNBAN = "USER_UNBAN"
    ACTION_USER_UPDATE = "USER_UPDATE"
    ACTION_USER_VIEW = "USER_VIEW"
    ACTION_SUBSCRIPTION_UPDATE = "SUBSCRIPTION_UPDATE"
    ACTION_SYSTEM_HEALTH_CHECK = "SYSTEM_HEALTH_CHECK"
    ACTION_VIEW_REPORTS = "VIEW_REPORTS"
    ACTION_EXPORT_DATA = "EXPORT_DATA"
    ACTION_MODERATION = "CONTENT_MODERATION"

    @staticmethod
    async def log_admin_action(
        session: AsyncSession,
        admin_user_id: str,
        action: str,
        target_user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> AdminAuditLog:
        """
        记录管理员操作

        Args:
            session: 数据库会话
            admin_user_id: 管理员用户ID
            action: 操作类型
            target_user_id: 目标用户ID（可选）
            details: 操作详情（可选）
            ip_address: IP地址（可选）
            user_agent: 用户代理（可选）
            endpoint: API端点（可选）
            status: 操作状态
            error_message: 错误信息（可选）

        Returns:
            AdminAuditLog: 创建的审计日志记录
        """
        try:
            audit_log = AdminAuditLog(
                admin_user_id=admin_user_id,
                action=action,
                target_user_id=target_user_id,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                endpoint=endpoint,
                status=status,
                error_message=error_message
            )

            session.add(audit_log)
            await session.commit()
            await session.refresh(audit_log)

            logger.info(
                f"管理员操作已记录: admin_id={admin_user_id}, action={action}, "
                f"target_id={target_user_id}, status={status}"
            )

            return audit_log

        except Exception as e:
            logger.error(f"记录审计日志失败: {e}")
            await session.rollback()
            raise

    @staticmethod
    async def get_audit_logs(
        session: AsyncSession,
        admin_user_id: Optional[str] = None,
        action: Optional[str] = None,
        target_user_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[list[AdminAuditLog], int]:
        """
        获取审计日志

        Args:
            session: 数据库会话
            admin_user_id: 管理员ID筛选
            action: 操作类型筛选
            target_user_id: 目标用户ID筛选
            status: 状态筛选
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制数量
            offset: 偏移量

        Returns:
            tuple[list[AdminAuditLog], int]: 审计日志列表和总数
        """
        try:
            # 构建查询
            query = select(AdminAuditLog)
            count_query = select(func.count(AdminAuditLog.id))

            # 添加筛选条件
            conditions = []
            if admin_user_id:
                conditions.append(AdminAuditLog.admin_user_id == admin_user_id)
            if action:
                conditions.append(AdminAuditLog.action == action)
            if target_user_id:
                conditions.append(AdminAuditLog.target_user_id == target_user_id)
            if status:
                conditions.append(AdminAuditLog.status == status)
            if start_date:
                conditions.append(AdminAuditLog.timestamp >= start_date)
            if end_date:
                conditions.append(AdminAuditLog.timestamp <= end_date)

            if conditions:
                query = query.where(*conditions)
                count_query = count_query.where(*conditions)

            # 排序和分页
            query = query.order_by(AdminAuditLog.timestamp.desc()).offset(offset).limit(limit)

            # 执行查询
            result = await session.execute(query)
            audit_logs = result.scalars().all()

            count_result = await session.execute(count_query)
            total = count_result.scalar()

            return audit_logs, total

        except Exception as e:
            logger.error(f"获取审计日志失败: {e}")
            raise

    @staticmethod
    def extract_request_info(request: Request) -> tuple[str, str]:
        """从请求中提取IP地址和用户代理"""
        # 获取IP地址
        ip_address = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()

        # 获取用户代理
        user_agent = request.headers.get("User-Agent", "")

        return ip_address, user_agent


# 创建审计依赖函数
from fastapi import Depends
from ..core.db import get_async_session
from ..api.deps import get_current_user


async def log_admin_action_dependency(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    FastAPI依赖函数，用于自动记录管理员操作
    """
    if current_user.role != "admin":
        return None  # 非管理员不记录

    async def log_action(
        action: str,
        target_user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ):
        ip_address, user_agent = AuditService.extract_request_info(request)
        endpoint = f"{request.method} {request.url.path}"

        await AuditService.log_admin_action(
            session=session,
            admin_user_id=current_user.id,
            action=action,
            target_user_id=target_user_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            status=status,
            error_message=error_message
        )

    return log_action


# 审计装饰器
def audit_admin_action(action: str, include_target: bool = True):
    """
    管理员操作审计装饰器

    Args:
        action: 操作类型
        include_target: 是否包含目标用户ID
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 获取相关参数
            request = kwargs.get('request')
            current_user = kwargs.get('current_admin') or kwargs.get('current_user')
            session = kwargs.get('session')

            if not all([request, current_user, session]) or current_user.role != "admin":
                # 如果不是管理员或缺少必要参数，直接执行原函数
                return await func(*args, **kwargs)

            ip_address, user_agent = AuditService.extract_request_info(request)
            endpoint = f"{request.method} {request.url.path}"

            # 尝试从函数参数中获取目标用户ID
            target_user_id = None
            if include_target:
                # 常见的参数名
                for param_name in ['user_id', 'target_user_id', 'id']:
                    if param_name in kwargs:
                        target_user_id = kwargs[param_name]
                        break

            try:
                # 执行原函数
                result = await func(*args, **kwargs)

                # 记录成功的操作
                await AuditService.log_admin_action(
                    session=session,
                    admin_user_id=current_user.id,
                    action=action,
                    target_user_id=target_user_id,
                    details={
                        "function": func.__name__,
                        "args": str(args),
                        "kwargs": {k: v for k, v in kwargs.items() if k not in ['session', 'current_admin', 'request']}
                    },
                    ip_address=ip_address,
                    user_agent=user_agent,
                    endpoint=endpoint,
                    status="success"
                )

                return result

            except Exception as e:
                # 记录失败的操作
                await AuditService.log_admin_action(
                    session=session,
                    admin_user_id=current_user.id,
                    action=action,
                    target_user_id=target_user_id,
                    details={
                        "function": func.__name__,
                        "error": str(e)
                    },
                    ip_address=ip_address,
                    user_agent=user_agent,
                    endpoint=endpoint,
                    status="failed",
                    error_message=str(e)
                )
                raise

        return wrapper
    return decorator