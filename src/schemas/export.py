# -*- coding: utf-8 -*-
"""
导出功能Schema模型
"""

from typing import Optional
from pydantic import BaseModel, Field

class MDExportReq(BaseModel):
    title: str
    content: str
    out_path: Optional[str] = None

class PPTExportReq(BaseModel):
    title: str
    content: str
    out_path: Optional[str] = None

class TTSExportReq(BaseModel):
    title: str
    content: str
    out_path: Optional[str] = None
    voice: Optional[str] = None
    speed: Optional[float] = None
    language: Optional[str] = None
    stream: bool = False