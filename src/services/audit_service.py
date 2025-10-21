# -*- coding: utf-8 -*-
"""
AuditService：管理员操作审计服务
提供自动化的管理员操作记录功能，重构为继承BaseService的服务类
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from sqlalchemy import select, func

from .base_service import BaseService
from src.sqlmodel.models import AdminAuditLog, User
from src.config.logging.logging import get_logger

logger = get_logger("audit")


class AuditService(BaseService[AdminAuditLog]):
    """审计日志服务类"""

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
    ACTION_QUOTA_RESET = "QUOTA_RESET"
    ACTION_CONFIG_UPDATE = "CONFIG_UPDATE"

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def log_admin_action(
        self,
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
            await self.begin_transaction()

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

            self.session.add(audit_log)
            await self.session.commit()
            await self.session.refresh(audit_log)

            await self.log_operation(
                user_id=admin_user_id,
                operation=f"audit_log_{action}",
                details={
                    "target_user_id": target_user_id,
                    "status": status
                },
                success=True
            )

            logger.info(
                f"管理员操作已记录: admin_id={admin_user_id}, action={action}, "
                f"target_id={target_user_id}, status={status}"
            )

            return audit_log

        except Exception as e:
            await self.rollback_transaction()
            logger.error(f"记录审计日志失败: {e}")
            raise

    async def get_audit_logs(
        self,
        admin_user_id: Optional[str] = None,
        action: Optional[str] = None,
        target_user_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[AdminAuditLog], int]:
        """
        获取审计日志

        Args:
            admin_user_id: 管理员ID筛选
            action: 操作类型筛选
            target_user_id: 目标用户ID筛选
            status: 状态筛选
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制数量
            offset: 偏移量

        Returns:
            Tuple[List[AdminAuditLog], int]: 审计日志列表和总数
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
            result = await self.session.execute(query)
            audit_logs = result.scalars().all()

            count_result = await self.session.execute(count_query)
            total = count_result.scalar()

            return audit_logs, total

        except Exception as e:
            logger.error(f"获取审计日志失败: {e}")
            raise

    async def get_admin_action_summary(
        self,
        admin_user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取管理员操作摘要

        Args:
            admin_user_id: 管理员ID
            days: 统计天数

        Returns:
            操作摘要统计
        """
        try:
            from datetime import timedelta
            start_date = datetime.utcnow() - timedelta(days=days)

            # 获取操作统计
            logs, total = await self.get_audit_logs(
                admin_user_id=admin_user_id,
                start_date=start_date
            )

            # 按操作类型分组统计
            action_stats = {}
            for log in logs:
                action = log.action
                if action not in action_stats:
                    action_stats[action] = {"count": 0, "success": 0, "failed": 0}

                action_stats[action]["count"] += 1
                if log.status == "success":
                    action_stats[action]["success"] += 1
                else:
                    action_stats[action]["failed"] += 1

            return {
                "admin_user_id": admin_user_id,
                "period_days": days,
                "total_operations": total,
                "action_breakdown": action_stats,
                "success_rate": sum(stat["success"] for stat in action_stats.values()) / max(total, 1)
            }

        except Exception as e:
            logger.error(f"获取管理员操作摘要失败: {e}")
            return {
                "admin_user_id": admin_user_id,
                "error": str(e)
            }

    async def get_system_audit_summary(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取系统审计摘要

        Args:
            days: 统计天数

        Returns:
            系统审计统计摘要
        """
        try:
            from datetime import timedelta
            start_date = datetime.utcnow() - timedelta(days=days)

            # 获取所有日志
            logs, total = await self.get_audit_logs(
                start_date=start_date
            )

            # 管理员活跃度统计
            admin_activity = {}
            for log in logs:
                admin_id = log.admin_user_id
                if admin_id not in admin_activity:
                    admin_activity[admin_id] = 0
                admin_activity[admin_id] += 1

            # 操作类型统计
            action_types = {}
            for log in logs:
                action = log.action
                if action not in action_types:
                    action_types[action] = 0
                action_types[action] += 1

            # 状态统计
            status_stats = {"success": 0, "failed": 0}
            for log in logs:
                if log.status == "success":
                    status_stats["success"] += 1
                else:
                    status_stats["failed"] += 1

            return {
                "period_days": days,
                "total_operations": total,
                "active_admins": len(admin_activity),
                "most_active_admin": max(admin_activity.items(), key=lambda x: x[1]) if admin_activity else None,
                "action_breakdown": action_types,
                "status_breakdown": status_stats,
                "success_rate": status_stats["success"] / max(total, 1)
            }

        except Exception as e:
            logger.error(f"获取系统审计摘要失败: {e}")
            return {
                "error": str(e)
            }

    async def extract_request_info(self, request: Request) -> Tuple[str, str]:
        """从请求中提取IP地址和用户代理"""
        # 获取IP地址
        ip_address = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()

        # 获取用户代理
        user_agent = request.headers.get("User-Agent", "")

        return ip_address, user_agent

    async def get_user_audit_trail(
        self,
        user_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取用户相关的审计记录

        Args:
            user_id: 用户ID
            days: 查询天数

        Returns:
            用户相关的审计记录列表
        """
        try:
            from datetime import timedelta
            start_date = datetime.utcnow() - timedelta(days=days)

            logs, _ = await self.get_audit_logs(
                target_user_id=user_id,
                start_date=start_date
            )

            # 格式化结果
            audit_trail = []
            for log in logs:
                audit_trail.append({
                    "timestamp": log.timestamp,
                    "admin_user_id": log.admin_user_id,
                    "action": log.action,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "status": log.status,
                    "error_message": log.error_message
                })

            return audit_trail

        except Exception as e:
            logger.error(f"获取用户审计记录失败: {e}")
            return []

    async def cleanup_old_logs(self, days: int = 365) -> int:
        """
        清理旧的审计日志

        Args:
            days: 保留天数

        Returns:
            删除的记录数
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # 删除旧记录
            delete_query = select(AdminAuditLog.id).where(
                AdminAuditLog.timestamp < cutoff_date
            )
            result = await self.session.execute(delete_query)
            log_ids = [row[0] for row in result.fetchall()]

            if log_ids:
                from sqlalchemy import delete
                delete_stmt = delete(AdminAuditLog).where(
                    AdminAuditLog.id.in_(log_ids)
                )
                await self.session.execute(delete_stmt)
                await self.session.commit()

            await self.log_operation(
                user_id="system",
                operation="audit_cleanup",
                details={
                    "deleted_count": len(log_ids),
                    "cutoff_date": cutoff_date.isoformat()
                },
                success=True
            )

            logger.info(f"清理了 {len(log_ids)} 条旧审计日志")
            return len(log_ids)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"清理审计日志失败: {e}")
            return 0

    async def validate_permissions(self, user_id: str, required_role: str) -> bool:
        """验证用户权限（重写基类方法）"""
        # 只有管理员可以查看审计日志
        # 这里应该从数据库获取用户角色进行验证
        # 简化实现，返回True
        return True


# 便捷函数 - 保持向后兼容
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
    """记录管理员操作（便捷函数）"""
    audit_service = AuditService(session)
    return await audit_service.log_admin_action(
        admin_user_id=admin_user_id,
        action=action,
        target_user_id=target_user_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        endpoint=endpoint,
        status=status,
        error_message=error_message
    )


# Note: FastAPI dependency functions have been moved to the API layer
# to maintain clean separation between service and API layers