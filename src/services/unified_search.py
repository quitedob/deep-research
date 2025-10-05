# -*- coding: utf-8 -*-
"""
统一搜索服务
管理 Doubao 和 Kimi 的联网搜索功能
"""
import logging
from typing import Dict, Any, Optional, List
from enum import Enum

from ..config.config_loader import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SearchProvider(str, Enum):
    """搜索提供商枚举"""
    DOUBAO = "doubao"
    KIMI = "kimi"


class UnifiedSearchService:
    """统一搜索服务"""
    
    def __init__(self):
        self.current_provider = SearchProvider(settings.default_search_provider)
        self.services = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """初始化搜索服务"""
        try:
            # 初始化 Doubao 搜索服务
            if settings.doubao_api_key:
                from ..llms.providers.doubao_llm import DoubaoProvider
                self.services[SearchProvider.DOUBAO] = DoubaoProvider(
                    model_name=settings.doubao_model,
                    api_key=settings.doubao_api_key,
                    base_url=settings.doubao_base_url
                )
                logger.info("Doubao 搜索服务已初始化")
            
            # TODO: 初始化 Kimi 搜索服务
            # if settings.kimi_api_key:
            #     from .kimi_service import KimiService
            #     self.services[SearchProvider.KIMI] = KimiService(...)
            #     logger.info("Kimi 搜索服务已初始化")
            
            # 设置默认提供商
            if self.current_provider not in self.services and self.services:
                self.current_provider = list(self.services.keys())[0]
                logger.warning(f"默认搜索提供商不可用，切换到: {self.current_provider.value}")
            
        except Exception as e:
            logger.error(f"初始化搜索服务失败: {e}")
    
    def get_available_providers(self) -> Dict[str, Dict[str, Any]]:
        """获取所有可用的搜索提供商"""
        providers = {}
        
        for provider in SearchProvider:
            is_available = provider in self.services
            is_current = provider == self.current_provider
            
            provider_info = {
                "id": provider.value,
                "name": provider.value.title(),
                "is_available": is_available,
                "is_current": is_current,
                "supports_search": True
            }
            
            if provider == SearchProvider.DOUBAO:
                provider_info.update({
                    "display_name": "豆包 (Doubao)",
                    "description": "字节跳动豆包，支持联网搜索、视觉理解",
                    "features": ["联网搜索", "视觉理解", "函数调用", "上下文缓存"],
                    "model": settings.doubao_model
                })
            elif provider == SearchProvider.KIMI:
                provider_info.update({
                    "display_name": "Kimi (月之暗面)",
                    "description": "Moonshot AI Kimi，超长上下文联网搜索",
                    "features": ["联网搜索", "超长上下文", "函数调用"],
                    "model": settings.kimi_model
                })
            
            providers[provider.value] = provider_info
        
        return providers
    
    def set_provider(self, provider_id: str) -> bool:
        """设置当前搜索提供商"""
        try:
            provider = SearchProvider(provider_id)
            if provider in self.services:
                self.current_provider = provider
                logger.info(f"搜索提供商已切换到: {provider.value}")
                return True
            else:
                logger.error(f"搜索提供商 {provider_id} 不可用")
                return False
        except ValueError:
            logger.error(f"无效的搜索提供商: {provider_id}")
            return False
    
    async def search(
        self, 
        query: str, 
        provider_id: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行搜索
        
        Args:
            query: 搜索查询
            provider_id: 指定的提供商 ID（可选）
            **kwargs: 其他参数
        
        Returns:
            搜索结果
        """
        # 确定使用的提供商
        if provider_id:
            try:
                provider = SearchProvider(provider_id)
            except ValueError:
                return {
                    "success": False,
                    "error": f"无效的搜索提供商: {provider_id}",
                    "query": query
                }
        else:
            provider = self.current_provider
        
        # 检查提供商是否可用
        if provider not in self.services:
            return {
                "success": False,
                "error": f"搜索提供商 {provider.value} 不可用",
                "query": query
            }
        
        # 执行搜索
        try:
            service = self.services[provider]
            
            if provider == SearchProvider.DOUBAO:
                # 使用 Doubao Provider 的联网搜索功能
                messages = [{"role": "user", "content": query}]
                
                # 添加系统提示词（如果提供）
                system_prompt = kwargs.get('system_prompt')
                if system_prompt:
                    messages.insert(0, {"role": "system", "content": system_prompt})
                
                # 执行搜索
                response = await service.generate_with_search(
                    messages=messages,
                    search_limit=kwargs.get('search_limit', 10),
                    sources=kwargs.get('sources')
                )
                
                # 转换为统一格式
                result = {
                    "success": True,
                    "query": query,
                    "answer": response.content,
                    "search_results": response.references or [],
                    "sources": [ref["url"] for ref in (response.references or [])],
                    "model": response.model,
                    "provider": "doubao"
                }
                return result
            # TODO: 添加 Kimi 搜索逻辑
            # elif provider == SearchProvider.KIMI:
            #     result = await service.web_search(query, **kwargs)
            #     return result
            else:
                return {
                    "success": False,
                    "error": f"提供商 {provider.value} 的搜索功能尚未实现",
                    "query": query
                }
        
        except Exception as e:
            logger.error(f"搜索执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "provider": provider.value
            }
    
    def test_provider(self, provider_id: str) -> Dict[str, Any]:
        """测试指定提供商的连接状态"""
        try:
            provider = SearchProvider(provider_id)
            if provider not in self.services:
                return {
                    "success": False,
                    "provider": provider_id,
                    "message": f"提供商 {provider_id} 不可用或未配置"
                }
            
            service = self.services[provider]
            if hasattr(service, 'test_connection'):
                return service.test_connection()
            else:
                return {
                    "success": True,
                    "provider": provider_id,
                    "message": f"提供商 {provider_id} 已配置"
                }
        except ValueError:
            return {
                "success": False,
                "provider": provider_id,
                "message": f"无效的提供商 ID: {provider_id}"
            }
        except Exception as e:
            return {
                "success": False,
                "provider": provider_id,
                "message": f"测试失败: {str(e)}"
            }


# 全局搜索服务实例
_unified_search_service = None


def get_unified_search_service() -> UnifiedSearchService:
    """获取统一搜索服务实例"""
    global _unified_search_service
    if _unified_search_service is None:
        _unified_search_service = UnifiedSearchService()
    return _unified_search_service
