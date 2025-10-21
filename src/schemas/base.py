# -*- coding: utf-8 -*-
"""
基础数据模型（Base Schema）
提供所有API的标准响应格式和基础验证
"""

from typing import TypeVar, Generic, Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# 通用类型变量
T = TypeVar('T')


class BaseResponse(BaseModel):
    """
    基础响应模型
    所有API响应的标准格式
    """
    success: bool = Field(default=True, description="请求是否成功")
    message: Optional[str] = Field(default=None, description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间戳")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SuccessResponse(BaseResponse, Generic[T]):
    """
    成功响应模型
    包含返回的数据
    """
    success: bool = Field(default=True)
    data: Optional[T] = Field(default=None, description="返回的数据")

    class Config:
        from_attributes = True


class ErrorResponse(BaseResponse):
    """
    错误响应模型
    包含错误详情
    """
    success: bool = Field(default=False)
    error_code: Optional[str] = Field(default=None, description="错误代码")
    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")
    trace_id: Optional[str] = Field(default=None, description="追踪ID")

    class Config:
        from_attributes = True


class PaginatedResponse(BaseResponse, Generic[T]):
    """
    分页响应模型
    包含分页数据和元数据
    """
    success: bool = Field(default=True)
    data: List[T] = Field(default=[], description="数据列表")
    total: int = Field(default=0, description="总数")
    page: int = Field(default=1, description="当前页")
    page_size: int = Field(default=10, description="每页大小")
    total_pages: int = Field(default=0, description="总页数")

    class Config:
        from_attributes = True

    def __init__(self, **data):
        super().__init__(**data)
        if self.total > 0 and self.page_size > 0:
            self.total_pages = (self.total + self.page_size - 1) // self.page_size
