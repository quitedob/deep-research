# -*- coding: utf-8 -*-
"""
统一搜索 API
支持 Doubao 和 Kimi 联网搜索
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..api.deps import require_auth
from ..sqlmodel.models import User
from ..services.unified_search import get_unified_search_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


# ==================== 请求/响应模型 ====================

class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    provider: Optional[str] = None  # 指定搜索提供商 (doubao/kimi)
    system_prompt: Optional[str] = None
    search_limit: int = 10


class SearchResponse(BaseModel):
    """搜索响应"""
    success: bool
    query: str
    answer: str
    search_results: list
    sources: list
    provider: str
    error: Optional[str] = None


class ProvidersResponse(BaseModel):
    """搜索提供商响应"""
    current_provider: str
    available_providers: dict


class SetProviderRequest(BaseModel):
    """设置提供商请求"""
    provider: str


# ==================== API 端点 ====================

@router.get("/providers", response_model=ProvidersResponse)
async def get_search_providers(
    current_user: User = Depends(require_auth)
):
    """获取所有可用的搜索提供商"""
    try:
        service = get_unified_search_service()
        providers = service.get_available_providers()
        return ProvidersResponse(
            current_provider=service.current_provider.value,
            available_providers=providers
        )
    except Exception as e:
        logger.error(f"获取搜索提供商失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/providers/set")
async def set_search_provider(
    request: SetProviderRequest,
    current_user: User = Depends(require_auth)
):
    """设置当前搜索提供商"""
    try:
        service = get_unified_search_service()
        success = service.set_provider(request.provider)
        
        if success:
            return {
                "success": True,
                "message": f"搜索提供商已切换到: {request.provider}",
                "current_provider": service.current_provider.value
            }
        else:
            raise HTTPException(status_code=400, detail=f"无法切换到提供商: {request.provider}")
    
    except Exception as e:
        logger.error(f"设置搜索提供商失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=SearchResponse)
async def web_search(
    request: SearchRequest,
    current_user: User = Depends(require_auth)
):
    """执行联网搜索"""
    try:
        service = get_unified_search_service()
        result = await service.search(
            query=request.query,
            provider_id=request.provider,
            system_prompt=request.system_prompt,
            search_limit=request.search_limit
        )
        
        return SearchResponse(
            success=result.get("success", False),
            query=result.get("query", request.query),
            answer=result.get("answer", ""),
            search_results=result.get("search_results", []),
            sources=result.get("sources", []),
            provider=result.get("provider", request.provider or "unknown"),
            error=result.get("error")
        )
    
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/{provider}")
async def test_provider(
    provider: str,
    current_user: User = Depends(require_auth)
):
    """测试指定提供商的连接状态"""
    try:
        service = get_unified_search_service()
        result = service.test_provider(provider)
        return result
    
    except Exception as e:
        logger.error(f"测试提供商失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
