# -*- coding: utf-8 -*-
"""
研究功能Schema模型
"""

from typing import Optional
from pydantic import BaseModel

class ResearchReq(BaseModel):
    query: str
    session_id: Optional[str] = None