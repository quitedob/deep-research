# -*- coding: utf-8 -*-
"""
AdminService: 管理员业务逻辑
提供高级管理功能，包括用户统计、系统监控、审计日志等
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from ..sqlmodel.models import User
from ..dao import AdminDAO, SubscriptionDAO, DocumentProcessingJobDAO, AgentConfigurationDAO
from ..dao.users import UsersDAO
from .base_service import BaseService


class AdminService(BaseService[User]):
    """管理员业务逻辑服务"""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.admin_dao = AdminDAO(session)
        self.subscription_dao = SubscriptionDAO(session)
        self.document_dao = DocumentProcessingJobDAO(session)
        self.agent_config_dao = AgentConfigurationDAO(session)
        self.users_dao = UsersDAO(session)

    async def get_dashboard_statistics(self) -> Dict[str, Any]:
        """
        获取管理员仪表板统计信息

        Returns:
            包含各种统计数据的字典
        """
        # 获取用户统计
        user_stats = await self.admin_dao.get_user_statistics()

        # 获取订阅统计
        subscription_stats = await self.subscription_dao.get_subscription_statistics()

        # 获取文档处理统计
        try:
            document_stats = await self.document_dao.get_job_statistics()
        except:
            document_stats = {"total_jobs": 0, "by_status": {}}

        # 获取系统运行时间
        uptime = datetime.utcnow() - timedelta(hours=24)  # 简化实现

        # 获取活跃的智能体配置
        agent_configs = await self.agent_config_dao.get_all_active_configs()

        return {
            "user_statistics": user_stats,
            "subscription_statistics": subscription_stats,
            "document_statistics": document_stats,
            "system_info": {
                "uptime_hours": uptime.total_seconds() / 3600,
                "active_agent_configs": len(agent_configs),
                "last_updated": datetime.utcnow()
            }
        }

    async def get_user_management_data(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取用户管理数据

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            role: 角色筛选
            is_active: 激活状态筛选
            search: 搜索关键词

        Returns:
            包含用户列表和统计信息的字典
        """
        users = await self.admin_dao.get_users_with_filters(
            skip=skip,
            limit=limit,
            role=role,
            is_active=is_active,
            search=search
        )

        # 获取总数（简化实现，实际应该有专门的计数方法）
        total_count = len(users) + skip  # 简化实现

        return {
            "users": [
                {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "is_active": user.is_active,
                    "created_at": user.created_at
                }
                for user in users
            ],
            "total": total_count,
            "filters": {
                "role": role,
                "is_active": is_active,
                "search": search
            }
        }

    async def get_system_health_report(self) -> Dict[str, Any]:
        """
        获取系统健康报告

        Returns:
            系统健康状况的详细信息
        """
        health_report = {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "components": {}
        }

        # 检查数据库连接（简化实现）
        try:
            # 尝试执行一个简单的查询
            user_count = await self.users_dao.count({})
            health_report["components"]["database"] = {
                "status": "healthy",
                "details": {"connected_users": user_count}
            }
        except Exception as e:
            health_report["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_report["status"] = "degraded"

        # 检查文档处理服务
        try:
            document_stats = await self.document_dao.get_job_statistics()
            failed_jobs = document_stats.get("by_status", {}).get("failed", 0)

            if failed_jobs > 10:  # 如果失败任务过多
                health_report["components"]["document_processing"] = {
                    "status": "degraded",
                    "details": {"failed_jobs": failed_jobs}
                }
                if health_report["status"] == "healthy":
                    health_report["status"] = "degraded"
            else:
                health_report["components"]["document_processing"] = {
                    "status": "healthy",
                    "details": {"failed_jobs": failed_jobs}
                }
        except Exception as e:
            health_report["components"]["document_processing"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_report["status"] = "degraded"

        # 检查智能体配置
        try:
            agent_configs = await self.agent_config_dao.get_all_active_configs()
            health_report["components"]["agent_configurations"] = {
                "status": "healthy",
                "details": {"active_configs": len(agent_configs)}
            }
        except Exception as e:
            health_report["components"]["agent_configurations"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_report["status"] = "degraded"

        return health_report

    async def get_audit_summary(
        self,
        days: int = 30,
        admin_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取审计日志摘要

        Args:
            days: 统计天数
            admin_user_id: 特定管理员ID（可选）

        Returns:
            审计日志统计摘要
        """
        summary = await self.admin_dao.get_audit_log_summary(days=days)

        # 如果指定了特定管理员，过滤数据
        if admin_user_id:
            # 这里可以添加针对特定管理员的过滤逻辑
            pass

        return summary

    async def get_recent_activities(
        self,
        hours: int = 24,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取最近的系统活动

        Args:
            hours: 时间范围（小时）
            limit: 返回的最大记录数

        Returns:
            最近的系统活动列表
        """
        start_time = datetime.utcnow() - timedelta(hours=hours)

        # 获取最近的审计日志
        logs, _ = await self.admin_dao.get_audit_logs_with_filters(
            start_date=start_time,
            skip=0,
            limit=limit
        )

        # 获取最近的文档处理任务
        recent_jobs = await self.document_dao.get_jobs_by_status("processing", limit=20)

        # 获取最近的订阅变更
        recent_subscriptions = await self.subscription_dao.get_all_subscriptions_with_users(
            skip=0,
            limit=20
        )

        activities = []

        # 添加审计日志活动
        for log in logs:
            activities.append({
                "type": "admin_action",
                "timestamp": log.timestamp,
                "description": f"管理员执行操作: {log.action}",
                "details": {
                    "admin_user_id": log.admin_user_id,
                    "target_user_id": log.target_user_id,
                    "status": log.status
                }
            })

        # 添加文档处理活动
        for job in recent_jobs:
            activities.append({
                "type": "document_processing",
                "timestamp": job.updated_at or job.created_at,
                "description": f"文档处理: {job.filename}",
                "details": {
                    "status": job.status,
                    "progress": job.progress,
                    "user_id": job.user_id
                }
            })

        # 按时间排序
        activities.sort(key=lambda x: x["timestamp"], reverse=True)

        return activities[:limit]

    async def perform_bulk_user_operation(
        self,
        operation: str,
        user_ids: List[str],
        operator_id: str,
        operation_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行批量用户操作

        Args:
            operation: 操作类型 (activate, deactivate, update_role)
            user_ids: 用户ID列表
            operator_id: 操作者ID
            operation_params: 操作参数

        Returns:
            操作结果统计
        """
        if not await self.validate_permissions(operator_id, "admin"):
            raise PermissionError("没有权限执行批量用户操作")

        results = {
            "total": len(user_ids),
            "successful": 0,
            "failed": 0,
            "errors": []
        }

        try:
            await self.begin_transaction()

            for user_id in user_ids:
                try:
                    if operation == "activate":
                        success = await self.users_dao.update_active_status(user_id, True)
                    elif operation == "deactivate":
                        # 防止管理员停用自己
                        if user_id == operator_id:
                            raise ValueError("不能停用自己的账户")
                        success = await self.users_dao.update_active_status(user_id, False)
                    elif operation == "update_role":
                        new_role = operation_params.get("role") if operation_params else None
                        if not new_role:
                            raise ValueError("缺少角色参数")
                        success = await self.users_dao.update_role(user_id, new_role)
                    else:
                        raise ValueError(f"不支持的操作: {operation}")

                    if success:
                        results["successful"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"用户 {user_id} 操作失败")

                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"用户 {user_id}: {str(e)}")

            await self.commit_transaction()

            # 记录批量操作日志
            await self.log_operation(
                user_id=operator_id,
                operation=f"bulk_user_{operation}",
                details={
                    "total_users": len(user_ids),
                    "successful": results["successful"],
                    "failed": results["failed"],
                    "operation_params": operation_params
                }
            )

        except Exception as e:
            await self.rollback_transaction()
            raise e

        return results

    async def get_system_configuration_status(self) -> Dict[str, Any]:
        """
        获取系统配置状态

        Returns:
            系统配置的当前状态
        """
        # 获取智能体配置状态
        agent_configs = await self.agent_config_dao.get_all_configs_with_users()

        # 按提供商分组统计
        provider_stats = {}
        for config in agent_configs:
            provider = config["llm_provider"]
            if provider not in provider_stats:
                provider_stats[provider] = {"active": 0, "inactive": 0}

            if config["is_active"]:
                provider_stats[provider]["active"] += 1
            else:
                provider_stats[provider]["inactive"] += 1

        return {
            "agent_configurations": {
                "total": len(agent_configs),
                "active": sum(1 for c in agent_configs if c["is_active"]),
                "inactive": sum(1 for c in agent_configs if not c["is_active"]),
                "by_provider": provider_stats
            },
            "last_checked": datetime.utcnow()
        }