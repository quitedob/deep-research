#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话相关的Pydantic模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    """对话消息"""
    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容")
    model_name: Optional[str] = Field(None, description="模型名称")
    tokens_used: Optional[int] = Field(None, description="使用的token数")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    created_at: Optional[datetime] = None


class ChatSessionCreate(BaseModel):
    """创建对话会话"""
    title: str = Field(..., max_length=500, description="会话标题")
    llm_provider: str = Field(..., description="LLM提供商")
    model_name: str = Field(..., description="模型名称")
    system_prompt: Optional[str] = Field(None, description="系统提示词")


class ChatSessionUpdate(BaseModel):
    """更新对话会话"""
    title: Optional[str] = Field(None, max_length=500)
    llm_provider: Optional[str] = None
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None
    status: Optional[str] = None


class ChatSessionResponse(BaseModel):
    """对话会话响应"""
    id: str
    user_id: str
    title: str
    llm_provider: str
    model_name: str
    system_prompt: Optional[str] = None
    status: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class ChatRequest(BaseModel):
    """对话请求"""
    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="用户消息")
    stream: bool = Field(False, description="是否流式输出")


class ChatResponse(BaseModel):
    """对话响应"""
    session_id: str
    message: ChatMessage
    usage: Optional[Dict[str, int]] = None


class ModelInfo(BaseModel):
    """模型信息"""
    provider: str = Field(..., description="提供商")
    model_name: str = Field(..., description="模型名称")
    display_name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="描述")
    context_length: Optional[int] = Field(None, description="上下文长度")
    capabilities: List[str] = Field(default_factory=list, description="能力列表")
    is_available: bool = Field(True, description="是否可用")


class ModelListResponse(BaseModel):
    """模型列表响应"""
    models: List[ModelInfo]
    default_provider: str
    default_model: str
