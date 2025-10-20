# -*- coding: utf-8 -*-
"""
API v1 版本路由
"""

from fastapi import APIRouter
from ..chat import router as chat_router
from ..export import router as export_router
from ..research import router as research_router
from ..history import router as history_router
from ..search_full import router as search_full_router
from ..share import router as share_router
from ..user import router as user_router
from ..billing import router as billing_router
from ..rag import router as rag_router
from ..llm_config import router as llm_config_router
from ..conversation import router as conversation_router
from ..evidence import router as evidence_router
from ..health import router as health_router
from ..admin import router as admin_router
from ..ppt import router as ppt_router
from ..quota import router as quota_router

# 创建v1路由器
v1_router = APIRouter()

# 注册所有v1端点
v1_router.include_router(chat_router, tags=["chat"])
v1_router.include_router(export_router, tags=["export"])
v1_router.include_router(research_router, tags=["research"])
v1_router.include_router(history_router, tags=["history"])
v1_router.include_router(search_full_router, tags=["search"])
v1_router.include_router(share_router, tags=["share"])
v1_router.include_router(user_router, tags=["user"])
v1_router.include_router(billing_router, tags=["billing"])
v1_router.include_router(rag_router, tags=["rag"])
v1_router.include_router(llm_config_router, tags=["llm-config"])
v1_router.include_router(conversation_router, tags=["conversation"])
v1_router.include_router(evidence_router, tags=["evidence"])
v1_router.include_router(health_router, tags=["health"])
v1_router.include_router(admin_router, tags=["admin"])
v1_router.include_router(ppt_router, tags=["ppt"])
v1_router.include_router(quota_router, tags=["quota"])

__all__ = ["v1_router"]