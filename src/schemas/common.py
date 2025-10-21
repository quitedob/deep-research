# -*- coding: utf-8 -*-
"""
通用数据模型（Common Schema）
"""

from typing import List, TypeVar, Generic
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginationParams(BaseModel):
    """
    分页参数模型
    """
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页数量")
    sort_by: str = Field(default="created_at", description="排序字段")
    order: str = Field(default="desc", regex="^(asc|desc)$", description="排序顺序")

    class Config:
        from_attributes = True


class ListResponse(BaseModel, Generic[T]):
    """
    列表响应模型
    返回分页列表数据
    """
    items: List[T] = Field(default=[], description="数据项")
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
