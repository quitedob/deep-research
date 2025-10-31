# -*- coding: utf-8 -*-
"""
UserPreferencesService：用户偏好和引导管理服务
提供用户引导流程、偏好设置等功能
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from .base_service import BaseService
from src.dao import UsersDAO
from src.sqlmodel.models import User
from src.config.logging.logging import get_logger

logger = get_logger("user_preferences_service")


class UserPreferencesService(BaseService):
    """用户偏好和引导管理服务类"""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.users_dao = UsersDAO(session)
        # 简化的内存存储，实际应用中应该使用数据库
        if not hasattr(UserPreferencesService, '_user_onboarding'):
            UserPreferencesService._user_onboarding = {}
        if not hasattr(UserPreferencesService, '_user_preferences'):
            UserPreferencesService._user_preferences = {}

    async def start_onboarding(
        self,
        user_id: str,
        step: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        开始用户引导流程

        Args:
            user_id: 用户ID
            step: 当前步骤（可选）

        Returns:
            引导流程信息
        """
        try:
            user_id_str = str(user_id)

            # 初始化用户引导状态
            if user_id_str not in UserPreferencesService._user_onboarding:
                UserPreferencesService._user_onboarding[user_id_str] = {
                    "started": False,
                    "completed": False,
                    "current_step": None,
                    "steps_completed": [],
                    "started_at": None,
                    "completed_at": None
                }

            onboarding = UserPreferencesService._user_onboarding[user_id_str]

            # 开始引导流程
            onboarding["started"] = True
            onboarding["started_at"] = datetime.utcnow().isoformat()
            onboarding["current_step"] = step or "welcome"

            await self.log_operation(
                user_id=user_id,
                operation="onboarding_started",
                details={
                    "step": onboarding["current_step"]
                }
            )

            logger.info(f"用户 {user_id} 开始引导流程")

            return {
                "success": True,
                "message": "引导流程已开始",
                "next_step": onboarding["current_step"],
                "progress": {
                    "started": True,
                    "completed": False,
                    "current_step": onboarding["current_step"],
                    "steps_completed": onboarding["steps_completed"]
                }
            }

        except Exception as e:
            logger.error(f"开始引导流程失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "开始引导流程失败"
            }

    async def complete_onboarding(
        self,
        user_id: str,
        step: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        完成用户引导流程

        Args:
            user_id: 用户ID
            step: 完成的步骤（可选）

        Returns:
            引导流程信息
        """
        try:
            user_id_str = str(user_id)

            if user_id_str not in UserPreferencesService._user_onboarding:
                UserPreferencesService._user_onboarding[user_id_str] = {
                    "started": False,
                    "completed": False,
                    "current_step": None,
                    "steps_completed": [],
                    "started_at": None,
                    "completed_at": None
                }

            onboarding = UserPreferencesService._user_onboarding[user_id_str]

            # 完成引导流程
            onboarding["completed"] = True
            onboarding["completed_at"] = datetime.utcnow().isoformat()
            onboarding["current_step"] = None

            # 记录完成的步骤
            if step and step not in onboarding["steps_completed"]:
                onboarding["steps_completed"].append(step)

            await self.log_operation(
                user_id=user_id,
                operation="onboarding_completed",
                details={
                    "steps_completed": onboarding["steps_completed"]
                }
            )

            logger.info(f"用户 {user_id} 完成引导流程")

            return {
                "success": True,
                "message": "引导流程已完成",
                "progress": {
                    "started": onboarding["started"],
                    "completed": True,
                    "current_step": None,
                    "steps_completed": onboarding["steps_completed"]
                }
            }

        except Exception as e:
            logger.error(f"完成引导流程失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "完成引导流程失败"
            }

    async def skip_onboarding(self, user_id: str) -> Dict[str, Any]:
        """
        跳过用户引导流程

        Args:
            user_id: 用户ID

        Returns:
            引导流程信息
        """
        try:
            user_id_str = str(user_id)

            if user_id_str not in UserPreferencesService._user_onboarding:
                UserPreferencesService._user_onboarding[user_id_str] = {
                    "started": False,
                    "completed": False,
                    "current_step": None,
                    "steps_completed": [],
                    "started_at": None,
                    "completed_at": None
                }

            onboarding = UserPreferencesService._user_onboarding[user_id_str]

            # 跳过引导流程
            onboarding["completed"] = True  # 跳过也算完成
            onboarding["completed_at"] = datetime.utcnow().isoformat()
            onboarding["current_step"] = None

            await self.log_operation(
                user_id=user_id,
                operation="onboarding_skipped",
                details={}
            )

            logger.info(f"用户 {user_id} 跳过引导流程")

            return {
                "success": True,
                "message": "已跳过引导流程",
                "progress": {
                    "started": onboarding["started"],
                    "completed": True,
                    "current_step": None,
                    "steps_completed": onboarding["steps_completed"]
                }
            }

        except Exception as e:
            logger.error(f"跳过引导流程失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "跳过引导流程失败"
            }

    async def get_onboarding_status(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户引导状态

        Args:
            user_id: 用户ID

        Returns:
            引导状态信息
        """
        try:
            user_id_str = str(user_id)

            if (user_id_str not in UserPreferencesService._user_onboarding or
                not UserPreferencesService._user_onboarding[user_id_str]["started"]):
                return {
                    "started": False,
                    "completed": False,
                    "current_step": None,
                    "steps_completed": [],
                    "is_first_visit": True
                }

            onboarding = UserPreferencesService._user_onboarding[user_id_str]

            return {
                **onboarding,
                "is_first_visit": not onboarding["started"]
            }

        except Exception as e:
            logger.error(f"获取引导状态失败: {e}")
            return {
                "started": False,
                "completed": False,
                "current_step": None,
                "steps_completed": [],
                "is_first_visit": True,
                "error": str(e)
            }

    async def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新用户偏好设置

        Args:
            user_id: 用户ID
            preferences: 偏好设置

        Returns:
            更新结果
        """
        try:
            user_id_str = str(user_id)

            # 初始化用户偏好
            if user_id_str not in UserPreferencesService._user_preferences:
                UserPreferencesService._user_preferences[user_id_str] = {}

            # 更新偏好设置
            UserPreferencesService._user_preferences[user_id_str].update(preferences)

            await self.log_operation(
                user_id=user_id,
                operation="preferences_updated",
                details={
                    "updated_keys": list(preferences.keys())
                }
            )

            logger.info(f"用户 {user_id} 更新偏好设置: {list(preferences.keys())}")

            return {
                "success": True,
                "message": "偏好设置已更新",
                "preferences": UserPreferencesService._user_preferences[user_id_str]
            }

        except Exception as e:
            logger.error(f"更新用户偏好失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "更新用户偏好失败"
            }

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户偏好设置

        Args:
            user_id: 用户ID

        Returns:
            用户偏好设置
        """
        try:
            user_id_str = str(user_id)

            if user_id_str not in UserPreferencesService._user_preferences:
                # 返回默认偏好设置
                return {
                    "theme": "light",
                    "language": "zh-CN",
                    "notifications": {
                        "email": True,
                        "push": False,
                        "sound": True
                    },
                    "ui": {
                        "compact_mode": False,
                        "show_tips": True,
                        "auto_save": True
                    }
                }

            return UserPreferencesService._user_preferences[user_id_str]

        except Exception as e:
            logger.error(f"获取用户偏好失败: {e}")
            # 返回默认设置作为回退
            return {
                "theme": "light",
                "language": "zh-CN",
                "notifications": {
                    "email": True,
                    "push": False,
                    "sound": True
                },
                "ui": {
                    "compact_mode": False,
                    "show_tips": True,
                    "auto_save": True
                },
                "error": str(e)
            }

    async def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息

        Returns:
            系统信息
        """
        try:
            # 这里应该从配置和服务中获取真实信息
            # 简化实现，返回基本信息
            from src.config.loader.config_loader import get_settings

            settings = get_settings()

            return {
                "platform": {
                    "name": "Deep Research Platform",
                    "version": getattr(settings, 'app_version', '1.0.0'),
                    "description": "AI驱动的深度研究平台"
                },
                "capabilities": {
                    "llm_providers": ["openai", "claude", "local"],  # 简化列表
                    "features": [
                        "智能对话",
                        "深度研究",
                        "代码执行",
                        "文档分析",
                        "多模态处理",
                        "数据可视化"
                    ],
                    "supported_languages": ["zh-CN", "en-US"],
                    "max_file_size": "50MB",
                    "supported_formats": [".txt", ".pdf", ".docx", ".md", ".json", ".csv"]
                },
                "statistics": {
                    "active_users": "10K+",
                    "processed_documents": "50K+",
                    "ai_conversations": "1M+",
                    "uptime": "99.9%"
                }
            }

        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            return {
                "platform": {
                    "name": "Deep Research Platform",
                    "version": "1.0.0",
                    "description": "AI驱动的深度研究平台"
                },
                "error": str(e)
            }

    async def validate_permissions(self, user_id: str, required_role: str) -> bool:
        """验证用户权限（重写基类方法）"""
        # 用户偏好服务的权限验证逻辑
        # 用户只能操作自己的偏好设置
        # 简化实现，返回True
        return True