# -*- coding: utf-8 -*-
"""
用户相关API端点
"""

from typing import Optional, dict
from datetime import datetime
from pathlib import Path
import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.api.deps import require_auth
from src.sqlmodel.models import User
from src.config.config_loader import get_settings
from src.llms.router import ModelRouter

logger = logging.getLogger(__name__)

router = APIRouter()
_settings = get_settings()
_router = ModelRouter.from_conf(Path("conf.yaml"))

class UserOnboardingRequest(BaseModel):
    """用户引导请求"""
    action: str = Field(..., description="引导动作", examples=["start", "complete", "skip"])
    step: Optional[str] = Field(None, description="当前步骤")
    data: Optional[dict] = Field(default_factory=dict, description="额外数据")

class UserOnboardingResponse(BaseModel):
    """用户引导响应"""
    success: bool
    message: str
    next_step: Optional[str] = None
    progress: Optional[dict] = None

class UserPreferencesRequest(BaseModel):
    """用户偏好设置请求"""
    preferences: dict = Field(..., description="用户偏好设置")

@router.post("/user/onboarding", response_model=UserOnboardingResponse)
async def handle_user_onboarding(
    request: UserOnboardingRequest,
    current_user: User = Depends(require_auth)
):
    """
    处理用户引导流程

    记录用户的引导状态，提供个性化的引导体验
    """
    try:
        # 简单的内存存储（实际应用中应使用数据库）
        if not hasattr(handle_user_onboarding, '_user_onboarding'):
            handle_user_onboarding._user_onboarding = {}

        user_id = str(current_user.id)

        if user_id not in handle_user_onboarding._user_onboarding:
            handle_user_onboarding._user_onboarding[user_id] = {
                "started": False,
                "completed": False,
                "current_step": None,
                "steps_completed": [],
                "started_at": None,
                "completed_at": None
            }

        onboarding = handle_user_onboarding._user_onboarding[user_id]

        if request.action == "start":
            onboarding["started"] = True
            onboarding["started_at"] = datetime.utcnow().isoformat()
            onboarding["current_step"] = request.step or "welcome"

            logger.info(f"用户 {current_user.id} 开始引导流程")

            return UserOnboardingResponse(
                success=True,
                message="引导流程已开始",
                next_step="welcome",
                progress={
                    "started": True,
                    "completed": False,
                    "current_step": "welcome",
                    "steps_completed": []
                }
            )

        elif request.action == "complete":
            onboarding["completed"] = True
            onboarding["completed_at"] = datetime.utcnow().isoformat()
            onboarding["current_step"] = None

            if request.step and request.step not in onboarding["steps_completed"]:
                onboarding["steps_completed"].append(request.step)

            logger.info(f"用户 {current_user.id} 完成引导流程")

            return UserOnboardingResponse(
                success=True,
                message="引导流程已完成",
                progress={
                    "started": True,
                    "completed": True,
                    "current_step": None,
                    "steps_completed": onboarding["steps_completed"]
                }
            )

        elif request.action == "skip":
            onboarding["completed"] = True  # 跳过也算完成
            onboarding["completed_at"] = datetime.utcnow().isoformat()
            onboarding["current_step"] = None

            logger.info(f"用户 {current_user.id} 跳过引导流程")

            return UserOnboardingResponse(
                success=True,
                message="已跳过引导流程",
                progress={
                    "started": onboarding["started"],
                    "completed": True,
                    "current_step": None,
                    "steps_completed": onboarding["steps_completed"]
                }
            )

        else:
            raise HTTPException(status_code=400, detail="无效的引导动作")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理用户引导失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/onboarding/status")
async def get_onboarding_status(
    current_user: User = Depends(require_auth)
):
    """
    获取用户引导状态
    """
    try:
        user_id = str(current_user.id)

        if not hasattr(handle_user_onboarding, '_user_onboarding') or user_id not in handle_user_onboarding._user_onboarding:
            return {
                "started": False,
                "completed": False,
                "current_step": None,
                "steps_completed": [],
                "is_first_visit": True
            }

        onboarding = handle_user_onboarding._user_onboarding[user_id]

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

@router.post("/user/preferences")
async def update_user_preferences(
    request: UserPreferencesRequest,
    current_user: User = Depends(require_auth)
):
    """
    更新用户偏好设置

    包括主题、语言、通知设置等
    """
    try:
        # 简单的内存存储（实际应用中应使用数据库）
        if not hasattr(update_user_preferences, '_user_preferences'):
            update_user_preferences._user_preferences = {}

        user_id = str(current_user.id)

        if user_id not in update_user_preferences._user_preferences:
            update_user_preferences._user_preferences[user_id] = {}

        # 更新偏好设置
        preferences = request.preferences
        update_user_preferences._user_preferences[user_id].update(preferences)

        logger.info(f"用户 {current_user.id} 更新偏好设置: {list(preferences.keys())}")

        return {
            "success": True,
            "message": "偏好设置已更新",
            "preferences": update_user_preferences._user_preferences[user_id]
        }

    except Exception as e:
        logger.error(f"更新用户偏好失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/preferences")
async def get_user_preferences(
    current_user: User = Depends(require_auth)
):
    """
    获取用户偏好设置
    """
    try:
        user_id = str(current_user.id)

        if not hasattr(update_user_preferences, '_user_preferences') or user_id not in update_user_preferences._user_preferences:
            # 返回默认偏好设置
            default_preferences = {
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
            return default_preferences

        return update_user_preferences._user_preferences[user_id]

    except Exception as e:
        logger.error(f"获取用户偏好失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/info")
async def get_system_info():
    """
    获取系统信息

    用于欢迎页面展示平台能力
    """
    try:
        # 获取LLM提供商信息
        providers_info = await _router.health()

        return {
            "platform": {
                "name": "Deep Research Platform",
                "version": _settings.app_version,
                "description": "AI驱动的深度研究平台"
            },
            "capabilities": {
                "llm_providers": list(providers_info.get("providers", {}).keys()),
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
        raise HTTPException(status_code=500, detail=str(e))