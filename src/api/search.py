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


class DomainFilterRequest(BaseModel):
    """域名过滤请求"""
    blocked_domains: Optional[list] = None
    allowed_domains: Optional[list] = None


class SearchConfigRequest(BaseModel):
    """搜索配置请求"""
    enable_deduplication: Optional[bool] = None
    enable_domain_filter: Optional[bool] = None
    enable_result_ranking: Optional[bool] = None
    max_results: Optional[int] = None
    min_content_length: Optional[int] = None


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


# ==================== 搜索结果后处理 API ====================

@router.get("/config")
async def get_search_config(
    current_user: User = Depends(require_auth)
):
    """获取搜索配置"""
    try:
        service = get_unified_search_service()
        return {
            "success": True,
            "config": {
                "enable_deduplication": service.enable_deduplication,
                "enable_domain_filter": service.enable_domain_filter,
                "enable_result_ranking": service.enable_result_ranking,
                "max_results": service.max_results,
                "min_content_length": service.min_content_length
            },
            "domain_filters": service.get_domain_filters()
        }
    except Exception as e:
        logger.error(f"获取搜索配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def update_search_config(
    request: SearchConfigRequest,
    current_user: User = Depends(require_auth)
):
    """更新搜索配置"""
    try:
        service = get_unified_search_service()
        
        if request.enable_deduplication is not None:
            service.enable_deduplication = request.enable_deduplication
        
        if request.enable_domain_filter is not None:
            service.enable_domain_filter = request.enable_domain_filter
        
        if request.enable_result_ranking is not None:
            service.enable_result_ranking = request.enable_result_ranking
        
        if request.max_results is not None:
            service.max_results = request.max_results
        
        if request.min_content_length is not None:
            service.min_content_length = request.min_content_length
        
        return {
            "success": True,
            "message": "搜索配置已更新",
            "config": {
                "enable_deduplication": service.enable_deduplication,
                "enable_domain_filter": service.enable_domain_filter,
                "enable_result_ranking": service.enable_result_ranking,
                "max_results": service.max_results,
                "min_content_length": service.min_content_length
            }
        }
    except Exception as e:
        logger.error(f"更新搜索配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/domains")
async def get_domain_filters(
    current_user: User = Depends(require_auth)
):
    """获取域名过滤配置"""
    try:
        service = get_unified_search_service()
        filters = service.get_domain_filters()
        return {
            "success": True,
            "filters": filters
        }
    except Exception as e:
        logger.error(f"获取域名过滤配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/domains")
async def update_domain_filters(
    request: DomainFilterRequest,
    current_user: User = Depends(require_auth)
):
    """更新域名过滤配置"""
    try:
        service = get_unified_search_service()
        service.set_domain_filters(
            blocked_domains=request.blocked_domains,
            allowed_domains=request.allowed_domains
        )
        
        return {
            "success": True,
            "message": "域名过滤配置已更新",
            "filters": service.get_domain_filters()
        }
    except Exception as e:
        logger.error(f"更新域名过滤配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/domains/block")
async def add_blocked_domain(
    domain: str,
    current_user: User = Depends(require_auth)
):
    """添加黑名单域名"""
    try:
        service = get_unified_search_service()
        service.add_blocked_domain(domain)
        return {
            "success": True,
            "message": f"已添加黑名单域名: {domain}",
            "blocked_domains": list(service.blocked_domains)
        }
    except Exception as e:
        logger.error(f"添加黑名单域名失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/domains/block/{domain}")
async def remove_blocked_domain(
    domain: str,
    current_user: User = Depends(require_auth)
):
    """移除黑名单域名"""
    try:
        service = get_unified_search_service()
        service.remove_blocked_domain(domain)
        return {
            "success": True,
            "message": f"已移除黑名单域名: {domain}",
            "blocked_domains": list(service.blocked_domains)
        }
    except Exception as e:
        logger.error(f"移除黑名单域名失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/domains/allow")
async def add_allowed_domain(
    domain: str,
    current_user: User = Depends(require_auth)
):
    """添加白名单域名"""
    try:
        service = get_unified_search_service()
        service.add_allowed_domain(domain)
        return {
            "success": True,
            "message": f"已添加白名单域名: {domain}",
            "allowed_domains": list(service.allowed_domains)
        }
    except Exception as e:
        logger.error(f"添加白名单域名失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/domains/allow/{domain}")
async def remove_allowed_domain(
    domain: str,
    current_user: User = Depends(require_auth)
):
    """移除白名单域名"""
    try:
        service = get_unified_search_service()
        service.remove_allowed_domain(domain)
        return {
            "success": True,
            "message": f"已移除白名单域名: {domain}",
            "allowed_domains": list(service.allowed_domains)
        }
    except Exception as e:
        logger.error(f"移除白名单域名失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
