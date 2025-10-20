# -*- coding: utf-8 -*-
"""
搜索功能Schema模型
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class ConversationSearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    limit: int = Field(20, le=100, description="返回结果数量限制")
    offset: int = Field(0, ge=0, description="偏移量")
    filters: Optional[Dict] = Field(default_factory=dict)

class ConversationSearchResponse(BaseModel):
    total: int
    results: List[Dict]
    query: str
    suggestions: List[str] = []
    search_time: float