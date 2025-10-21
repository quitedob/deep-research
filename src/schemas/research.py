# -*- coding: utf-8 -*-
"""
研究相关数据模型（Research Schema）
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ResearchReq(BaseModel):
    """
    研究请求模型
    启动研究任务的请求
    """
    query: str = Field(description="研究查询")
    session_id: Optional[str] = Field(default=None, description="会话ID")

    class Config:
        from_attributes = True


class ResearchResponse(BaseModel):
    """
    研究响应模型
    研究结果的标准返回格式
    """
    session_id: str = Field(description="会话ID")
    status: str = Field(description="状态: completed, failed, error")
    documents_found: int = Field(default=0, description="找到的文档数")
    iterations: int = Field(default=0, description="迭代次数")
    error: Optional[str] = Field(default=None, description="错误信息")

    class Config:
        from_attributes = True


class ResearchStreamResponse(BaseModel):
    """
    研究流式响应模型
    研究进度的流式更新
    """
    phase: Optional[str] = Field(default=None, description="当前阶段: planning, collecting, synthesizing")
    message: Optional[str] = Field(default=None, description="进度消息")
    status: str = Field(description="状态: running, completed, failed")
    progress: Optional[int] = Field(default=None, description="进度百分比 0-100")
    error: Optional[str] = Field(default=None, description="错误信息")

    class Config:
        from_attributes = True
