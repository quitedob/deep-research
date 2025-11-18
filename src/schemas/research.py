#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
研究相关的Pydantic Schema定义
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


class ResearchRequest(BaseModel):
    """研究请求"""
    query: str = Field(..., description="研究查询")
    research_type: str = Field(default="comprehensive", description="研究类型")
    sources: Optional[List[str]] = Field(default=None, description="指定的信息源")
    include_images: bool = Field(default=False, description="是否包含图像分析")
    llm_config: Optional[Dict[str, Any]] = Field(default=None, description="LLM配置")
    multimodal_llm_config: Optional[Dict[str, Any]] = Field(default=None, description="多模态LLM配置")
    session_id: Optional[str] = Field(default=None, description="会话ID")


class ResearchResponse(BaseModel):
    """研究响应"""
    success: bool = Field(..., description="是否成功")
    session_id: str = Field(..., description="会话ID")
    status: str = Field(..., description="状态")
    message: str = Field(..., description="消息")
    started_at: Optional[str] = Field(default=None, description="开始时间")
    error: Optional[str] = Field(default=None, description="错误信息")


class ResearchStatusResponse(BaseModel):
    """研究状态响应"""
    success: bool = Field(..., description="是否成功")
    session_id: str = Field(..., description="会话ID")
    status_data: Dict[str, Any] = Field(..., description="状态数据")
    message: str = Field(..., description="消息")


class ResearchListResponse(BaseModel):
    """研究列表响应"""
    success: bool = Field(..., description="是否成功")
    sessions: List[Dict[str, Any]] = Field(..., description="会话列表")
    total: int = Field(..., description="总数")
    message: str = Field(..., description="消息")


class ResearchExportResponse(BaseModel):
    """研究导出响应"""
    success: bool = Field(..., description="是否成功")
    session_id: str = Field(..., description="会话ID")
    data: Dict[str, Any] = Field(..., description="导出数据")
    exported_at: str = Field(..., description="导出时间")
    message: str = Field(..., description="消息")


class ReportMetadata(BaseModel):
    """报告元数据"""
    generated_at: str = Field(..., description="生成时间")
    total_findings: int = Field(..., description="发现总数")
    total_citations: int = Field(..., description="引用总数")
    quality_score: float = Field(..., description="质量评分")
    tools_count: int = Field(..., description="使用的工具数量")


class ReportSection(BaseModel):
    """报告分段"""
    title: str = Field(..., description="分段标题")
    content: str = Field(..., description="分段内容")


class FinalReport(BaseModel):
    """最终研究报告"""
    title: str = Field(..., description="报告标题")
    summary: str = Field(..., description="执行摘要")
    sections: List[ReportSection] = Field(..., description="报告分段")
    methodology: str = Field(..., description="研究方法")
    conclusions: str = Field(..., description="主要结论")
    references: str = Field(..., description="参考文献")
    metadata: ReportMetadata = Field(..., description="报告元数据")
    error: Optional[str] = Field(default=None, description="错误信息（如果生成失败）")
