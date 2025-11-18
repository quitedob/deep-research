#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户相关的Pydantic模型
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户信息响应"""
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UserUpdate(BaseModel):
    """用户信息更新"""
    full_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None


class UserPreferences(BaseModel):
    """用户偏好设置"""
    default_llm_provider: Optional[str] = Field("deepseek", description="默认LLM提供商")
    default_model: Optional[str] = Field(None, description="默认模型")
    theme: Optional[str] = Field("light", description="主题")
    language: Optional[str] = Field("zh", description="语言")
    preferences: Optional[dict] = Field(None, description="其他偏好设置")


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserResponse
