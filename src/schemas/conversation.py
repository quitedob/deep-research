# -*- coding: utf-8 -*-
"""
对话相关数据模型（Conversation Schema）
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ConversationCreateRequest(BaseModel):
    """
    创建对话请求模型
    """
    title: Optional[str] = Field(default=None, description="对话标题")
    initial_message: Optional[str] = Field(default=None, description="初始消息")

    class Config:
        from_attributes = True


class ConversationMessageResponse(BaseModel):
    """
    对话消息响应模型
    """
    id: str = Field(description="消息ID")
    role: str = Field(description="消息角色: user, assistant, system")
    content: str = Field(description="消息内容")
    message_type: Optional[str] = Field(default="text", description="消息类型")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")
    created_at: datetime = Field(description="创建时间")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConversationSessionResponse(BaseModel):
    """
    对话会话响应模型
    """
    id: str = Field(description="会话ID")
    title: str = Field(description="会话标题")
    message_count: int = Field(default=0, description="消息数")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    messages: Optional[list[ConversationMessageResponse]] = Field(
        default=None, 
        description="消息列表（可选）"
    )

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
