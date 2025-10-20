# -*- coding: utf-8 -*-
"""
用户功能Schema模型
"""

from typing import Optional, Dict
from pydantic import BaseModel, Field

class UserOnboardingRequest(BaseModel):
    action: str = Field(..., description="引导动作", examples=["start", "complete", "skip"])
    step: Optional[str] = Field(None, description="当前步骤")
    data: Optional[Dict] = Field(default_factory=dict, description="额外数据")

class UserOnboardingResponse(BaseModel):
    success: bool
    message: str
    next_step: Optional[str] = None
    progress: Optional[Dict] = None

class UserPreferencesRequest(BaseModel):
    preferences: Dict = Field(..., description="用户偏好设置")