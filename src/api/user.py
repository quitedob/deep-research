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
from src.config.loader.config_loader import get_settings
from src.services.user_preferences_service import UserPreferencesService
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
    处理用户引导流程 - 通过UserPreferencesService处理业务逻辑

    记录用户的引导状态，提供个性化的引导体验
    """
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from src.core.db import get_async_session

        async for session in get_async_session():
            preferences_service = UserPreferencesService(session)

            if request.action == "start":
                result = await preferences_service.start_onboarding(
                    user_id=str(current_user.id),
                    step=request.step
                )
                if result.get("success"):
                    return UserOnboardingResponse(
                        success=True,
                        message=result.get("message"),
                        next_step=result.get("next_step"),
                        progress=result.get("progress")
                    )
                else:
                    raise HTTPException(status_code=500, detail=result.get("message"))

            elif request.action == "complete":
                result = await preferences_service.complete_onboarding(
                    user_id=str(current_user.id),
                    step=request.step
                )
                if result.get("success"):
                    return UserOnboardingResponse(
                        success=True,
                        message=result.get("message"),
                        progress=result.get("progress")
                    )
                else:
                    raise HTTPException(status_code=500, detail=result.get("message"))

            elif request.action == "skip":
                result = await preferences_service.skip_onboarding(
                    user_id=str(current_user.id)
                )
                if result.get("success"):
                    return UserOnboardingResponse(
                        success=True,
                        message=result.get("message"),
                        progress=result.get("progress")
                    )
                else:
                    raise HTTPException(status_code=500, detail=result.get("message"))

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
    获取用户引导状态 - 通过UserPreferencesService处理业务逻辑
    """
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from src.core.db import get_async_session

        async for session in get_async_session():
            preferences_service = UserPreferencesService(session)
            status = await preferences_service.get_onboarding_status(str(current_user.id))
            return status

    except Exception as e:
        logger.error(f"获取引导状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/user/preferences")
async def update_user_preferences(
    request: UserPreferencesRequest,
    current_user: User = Depends(require_auth)
):
    """
    更新用户偏好设置 - 通过UserPreferencesService处理业务逻辑

    包括主题、语言、通知设置等
    """
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from src.core.db import get_async_session

        async for session in get_async_session():
            preferences_service = UserPreferencesService(session)
            result = await preferences_service.update_user_preferences(
                user_id=str(current_user.id),
                preferences=request.preferences
            )

            if result.get("success"):
                return {
                    "success": True,
                    "message": result.get("message"),
                    "preferences": result.get("preferences")
                }
            else:
                raise HTTPException(status_code=500, detail=result.get("message"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户偏好失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/preferences")
async def get_user_preferences(
    current_user: User = Depends(require_auth)
):
    """
    获取用户偏好设置 - 通过UserPreferencesService处理业务逻辑
    """
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from src.core.db import get_async_session

        async for session in get_async_session():
            preferences_service = UserPreferencesService(session)
            preferences = await preferences_service.get_user_preferences(str(current_user.id))
            return preferences

    except Exception as e:
        logger.error(f"获取用户偏好失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/info")
async def get_system_info():
    """
    获取系统信息 - 通过UserPreferencesService处理业务逻辑

    用于欢迎页面展示平台能力
    """
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from src.core.db import get_async_session

        async for session in get_async_session():
            preferences_service = UserPreferencesService(session)
            system_info = await preferences_service.get_system_info()
            return system_info

    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))