# -*- coding: utf-8 -*-
"""
分享功能Schema模型
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class ShareConversationRequest(BaseModel):
    session_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    expire_days: int = Field(30, ge=1, le=365, description="分享链接有效期（天）")

class ShareConversationResponse(BaseModel):
    share_id: str
    public_url: str
    title: str
    expires_at: str
    created_at: str

class PublicConversationResponse(BaseModel):
    share_id: str
    title: str
    description: Optional[str]
    messages: List[Dict]
    created_at: str
    expires_at: str
    view_count: int