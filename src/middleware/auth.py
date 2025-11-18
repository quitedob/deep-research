#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证中间件
提供JWT token认证功能
"""

from fastapi import Header, HTTPException, status
from typing import Dict, Any, Optional
import os


async def get_current_user(
    authorization: Optional[str] = Header(None, description="JWT Token")
) -> Dict[str, Any]:
    """
    获取当前用户信息（使用JWT token认证）
    
    Args:
        authorization: Authorization header with Bearer token
    
    Returns:
        用户信息字典
        
    Raises:
        HTTPException: 如果认证失败
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证格式错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    
    # 导入 UserService 来验证 token
    try:
        from src.services.user_service import UserService
        user_service = UserService()
        user = await user_service.get_current_user(token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="认证失败",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "user_id": user['id'],
            "username": user.get('username', ''),
            "email": user.get('email', ''),
            "is_admin": user.get('role') == 'admin',
            "is_anonymous": False
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"认证失败: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    authorization: Optional[str] = Header(None, description="JWT Token（可选）")
) -> Optional[Dict[str, Any]]:
    """
    获取可选的用户信息（不强制要求认证）
    
    Args:
        authorization: Authorization header with Bearer token
    
    Returns:
        用户信息字典，如果未提供则返回 None
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None
