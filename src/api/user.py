#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户API路由
处理用户注册、登录、资料管理等接口
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional

from src.schemas.user import (
    UserRegister, UserLogin, UserResponse, UserUpdate,
    UserPreferences, TokenResponse
)
from src.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["用户管理"])
user_service = UserService()


async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """从请求头获取当前用户ID"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证信息")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证格式错误")
    
    token = authorization.replace("Bearer ", "")
    user = await user_service.get_current_user(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="认证失败")
    
    return user['id']


@router.post("/register", response_model=TokenResponse, summary="用户注册")
async def register(user_data: UserRegister):
    """
    用户注册
    
    - **username**: 用户名（3-50字符，只能包含字母、数字、下划线和连字符）
    - **email**: 邮箱地址
    - **password**: 密码（至少6个字符）
    - **full_name**: 全名（可选）
    """
    try:
        result = await user_service.register(user_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"用户注册失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="注册失败")


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(login_data: UserLogin):
    """
    用户登录
    
    - **username**: 用户名或邮箱
    - **password**: 密码
    """
    try:
        result = await user_service.login(login_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"用户登录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="登录失败")


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """获取当前登录用户的信息"""
    user = await user_service.user_dao.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/me", summary="更新用户资料")
async def update_profile(
    update_data: UserUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """更新当前用户的资料"""
    success = await user_service.update_profile(user_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="更新失败")
    return {"success": True, "message": "资料更新成功"}


@router.get("/preferences", response_model=UserPreferences, summary="获取用户偏好设置")
async def get_preferences(user_id: str = Depends(get_current_user_id)):
    """获取当前用户的偏好设置"""
    preferences = await user_service.get_preferences(user_id)
    if not preferences:
        # 返回默认偏好
        return UserPreferences()
    return preferences


@router.put("/preferences", summary="更新用户偏好设置")
async def update_preferences(
    preferences: UserPreferences,
    user_id: str = Depends(get_current_user_id)
):
    """更新当前用户的偏好设置"""
    success = await user_service.update_preferences(user_id, preferences)
    if not success:
        raise HTTPException(status_code=500, detail="更新失败")
    return {"success": True, "message": "偏好设置更新成功"}


@router.post("/refresh", summary="刷新访问令牌")
async def refresh_token(refresh_token: str):
    """
    使用刷新令牌获取新的访问令牌
    
    - **refresh_token**: 刷新令牌
    """
    try:
        result = await user_service.refresh_token(refresh_token)
        if not result:
            raise HTTPException(status_code=401, detail="刷新令牌无效或已过期")
        return result
    except Exception as e:
        logger.error(f"刷新令牌失败: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail="刷新令牌失败")


@router.post("/logout", summary="用户登出")
async def logout(
    authorization: Optional[str] = Header(None),
    user_id: str = Depends(get_current_user_id)
):
    """
    用户登出，撤销Token
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证信息")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        success = await user_service.logout(token, user_id)
        if success:
            return {"success": True, "message": "登出成功"}
        else:
            raise HTTPException(status_code=500, detail="登出失败")
    except Exception as e:
        logger.error(f"登出失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="登出失败")
