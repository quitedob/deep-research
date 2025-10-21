# -*- coding: utf-8 -*-
"""
聊天相关数据模型（Chat Schema）
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChatItem(BaseModel):
    """
    聊天消息项
    表示单个聊天消息
    """
    role: str = Field(description="消息角色: user, assistant, system")
    content: str = Field(description="消息内容")

    class Config:
        from_attributes = True


class ChatReq(BaseModel):
    """
    聊天请求模型
    用于向LLM发送聊天请求
    """
    messages: List[ChatItem] = Field(description="消息列表")
    task: str = Field(default="general", description="任务类型")
    size: str = Field(default="medium", description="模型规模")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(default=None, description="最大令牌数")

    class Config:
        from_attributes = True


class ChatResp(BaseModel):
    """
    聊天响应模型
    LLM返回的聊天结果
    """
    model: str = Field(description="使用的模型名称")
    content: str = Field(description="生成的内容")
    tokens_used: Optional[int] = Field(default=None, description="使用的令牌数")

    class Config:
        from_attributes = True
