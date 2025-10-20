# -*- coding: utf-8 -*-
"""
聊天相关Schema模型
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ChatItem(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ChatReq(BaseModel):
    task: Literal["triage", "simple_chat", "code", "reasoning", "research", "creative"] = "general"
    size: Literal["small", "medium", "large"] = "medium"
    messages: List[ChatItem] = Field(min_items=1)
    temperature: float = 0.7
    max_tokens: Optional[int] = None

class ChatResp(BaseModel):
    model: str
    content: str