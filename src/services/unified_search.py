# -*- coding: utf-8 -*-
"""
统一搜索服务
管理 Doubao 和 Kimi 的联网搜索功能
支持搜索结果后处理、来源引用生成、结果去重和排序
"""
import logging
import hashlib
from typing import Dict, Any, Optional, List, Set
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse

from ..config.config_loader import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SearchProvider(str, Enum):
    """搜索提供商枚举"""
    DOUBAO = "doubao"
    KIMI = "kimi"
    TAVILY = "tavily"


@dataclass
class SearchResult:
    """搜索结果数据类"""
    title: str
    url: str
    content: str
    score: float = 0.0
    source: str = "web"
    published_date: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "score": self.score,
            "source": self.source,
            "published_date": self.published_date,
            "metadata": self.metadata
        }
    
    def get_domain(self) -> str:
        """获取域名"""
        try:
            parsed = urlparse(self.url)
            return parsed.netloc
        except:
            return "unknown"
    
    def get_content_hash(self) -> str:
        """获取内容哈希（用于去重）"""
        content_str = f"{self.title}:{self.content[:200]}"
        return hashlib.md5(content_str.encode()).hexdigest()


@dataclass
class SearchResponse:
    """搜索响应数据类"""
    success: bool
    query: str
    results: List[SearchResult]
    answer: Optional[str] = None
    total_results: int = 0
    search_time: float = 0.0
    provider: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "answer": self.answer,
            "total_results": self.total_results,
            "search_time": self.search_time,
            "provider": self.provider,
            "metadata": self.metadata
        }


class UnifiedSearchService:
    """统一搜索服务"""
    
    def __init__(self):
        self.current_provider = SearchProvider(settings.default_search_provider)
        self.services = {}
        self._initialize_services()
        
        # 搜索配置
        self.enable_deduplication = True
        self.enable_domain_filter = True
        self.enable_result_ranking = True
        self.max_results = 10
        self.min_content_length = 50
        
        # 域名过滤配置（Tavily风格）
        self.blocked_domains: Set[str] = set()
        self.allowed_domains: Set[str] = set()
    
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
                
                # 后处理搜索结果
                processed_response = self.post_process_results(
                    raw_results=response.references or [],
                    query=query,
                    provider="doubao",
                    answer=response.content,
                    max_results=kwargs.get('max_results', self.max_results),
                    include_citations=kwargs.get('include_citations', True)
                )
                
                # 转换为字典格式
                result = processed_response.to_dict()
                result["model"] = response.model
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
    
    # === 搜索结果后处理方法 ===
    
    def _parse_search_results(self, raw_results: List[Dict[str, Any]], provider: str) -> List[SearchResult]:
        """解析原始搜索结果为标准格式"""
        parsed_results = []
        
        for item in raw_results:
            try:
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", "") or item.get("snippet", ""),
                    score=item.get("score", 0.0),
                    source=provider,
                    published_date=item.get("published_date"),
                    metadata=item
                )
                parsed_results.append(result)
            except Exception as e:
                logger.warning(f"解析搜索结果失败: {e}")
                continue
        
        return parsed_results
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """去重搜索结果"""
        if not self.enable_deduplication:
            return results
        
        seen_hashes = set()
        seen_urls = set()
        unique_results = []
        
        for result in results:
            # 基于URL去重
            if result.url in seen_urls:
                continue
            
            # 基于内容哈希去重
            content_hash = result.get_content_hash()
            if content_hash in seen_hashes:
                continue
            
            seen_urls.add(result.url)
            seen_hashes.add(content_hash)
            unique_results.append(result)
        
        logger.info(f"去重: {len(results)} -> {len(unique_results)} 个结果")
        return unique_results
    
    def _filter_by_domain(self, results: List[SearchResult]) -> List[SearchResult]:
        """按域名过滤结果"""
        if not self.enable_domain_filter:
            return results
        
        filtered_results = []
        
        for result in results:
            domain = result.get_domain()
            
            # 检查黑名单
            if self.blocked_domains and domain in self.blocked_domains:
                logger.debug(f"过滤黑名单域名: {domain}")
                continue
            
            # 检查白名单（如果设置了白名单）
            if self.allowed_domains and domain not in self.allowed_domains:
                logger.debug(f"域名不在白名单: {domain}")
                continue
            
            filtered_results.append(result)
        
        if len(filtered_results) < len(results):
            logger.info(f"域名过滤: {len(results)} -> {len(filtered_results)} 个结果")
        
        return filtered_results
    
    def _filter_by_content_quality(self, results: List[SearchResult]) -> List[SearchResult]:
        """按内容质量过滤"""
        filtered_results = []
        
        for result in results:
            # 过滤内容过短的结果
            if len(result.content) < self.min_content_length:
                logger.debug(f"过滤内容过短的结果: {result.title}")
                continue
            
            # 过滤空标题
            if not result.title or result.title.strip() == "":
                logger.debug(f"过滤空标题结果")
                continue
            
            # 过滤无效URL
            if not result.url or not result.url.startswith(("http://", "https://")):
                logger.debug(f"过滤无效URL: {result.url}")
                continue
            
            filtered_results.append(result)
        
        if len(filtered_results) < len(results):
            logger.info(f"质量过滤: {len(results)} -> {len(filtered_results)} 个结果")
        
        return filtered_results
    
    def _rank_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """对搜索结果进行排序"""
        if not self.enable_result_ranking:
            return results
        
        # 计算相关性分数
        for result in results:
            relevance_score = self._calculate_relevance(result, query)
            # 综合原始分数和相关性分数
            result.score = (result.score * 0.6) + (relevance_score * 0.4)
        
        # 按分数降序排序
        ranked_results = sorted(results, key=lambda x: x.score, reverse=True)
        
        logger.info(f"结果排序完成，top 3 分数: {[r.score for r in ranked_results[:3]]}")
        return ranked_results
    
    def _calculate_relevance(self, result: SearchResult, query: str) -> float:
        """计算结果与查询的相关性"""
        query_lower = query.lower()
        title_lower = result.title.lower()
        content_lower = result.content.lower()
        
        score = 0.0
        
        # 标题匹配（权重更高）
        if query_lower in title_lower:
            score += 0.5
        
        # 内容匹配
        if query_lower in content_lower:
            score += 0.3
        
        # 查询词分词匹配
        query_words = set(query_lower.split())
        title_words = set(title_lower.split())
        content_words = set(content_lower.split())
        
        # 标题词匹配率
        if title_words:
            title_match_rate = len(query_words & title_words) / len(query_words)
            score += title_match_rate * 0.3
        
        # 内容词匹配率
        if content_words:
            content_match_rate = len(query_words & content_words) / len(query_words)
            score += content_match_rate * 0.2
        
        return min(score, 1.0)
    
    def _generate_citations(self, results: List[SearchResult]) -> List[Dict[str, Any]]:
        """生成来源引用"""
        citations = []
        
        for i, result in enumerate(results, 1):
            citation = {
                "id": i,
                "title": result.title,
                "url": result.url,
                "domain": result.get_domain(),
                "published_date": result.published_date,
                "citation_text": f"[{i}] {result.title} - {result.get_domain()}"
            }
            citations.append(citation)
        
        return citations
    
    def _format_answer_with_citations(self, answer: str, citations: List[Dict[str, Any]]) -> str:
        """格式化答案并添加引用"""
        if not answer or not citations:
            return answer
        
        # 在答案末尾添加引用列表
        formatted_answer = answer + "\n\n**参考来源:**\n"
        for citation in citations:
            formatted_answer += f"{citation['citation_text']}\n"
        
        return formatted_answer
    
    def post_process_results(
        self,
        raw_results: List[Dict[str, Any]],
        query: str,
        provider: str,
        **options
    ) -> SearchResponse:
        """
        搜索结果后处理
        
        Args:
            raw_results: 原始搜索结果
            query: 搜索查询
            provider: 提供商名称
            **options: 其他选项
        
        Returns:
            处理后的搜索响应
        """
        start_time = datetime.now()
        
        # 1. 解析结果
        results = self._parse_search_results(raw_results, provider)
        logger.info(f"解析了 {len(results)} 个搜索结果")
        
        # 2. 去重
        results = self._deduplicate_results(results)
        
        # 3. 域名过滤
        results = self._filter_by_domain(results)
        
        # 4. 质量过滤
        results = self._filter_by_content_quality(results)
        
        # 5. 排序
        results = self._rank_results(results, query)
        
        # 6. 限制数量
        max_results = options.get('max_results', self.max_results)
        results = results[:max_results]
        
        # 7. 生成引用
        citations = self._generate_citations(results)
        
        # 8. 格式化答案（如果有）
        answer = options.get('answer')
        if answer and options.get('include_citations', True):
            answer = self._format_answer_with_citations(answer, citations)
        
        # 计算处理时间
        search_time = (datetime.now() - start_time).total_seconds()
        
        return SearchResponse(
            success=True,
            query=query,
            results=results,
            answer=answer,
            total_results=len(results),
            search_time=search_time,
            provider=provider,
            metadata={
                "citations": citations,
                "original_count": len(raw_results),
                "filtered_count": len(results)
            }
        )
    
    # === 域名管理方法 ===
    
    def add_blocked_domain(self, domain: str) -> None:
        """添加黑名单域名"""
        self.blocked_domains.add(domain)
        logger.info(f"添加黑名单域名: {domain}")
    
    def remove_blocked_domain(self, domain: str) -> None:
        """移除黑名单域名"""
        self.blocked_domains.discard(domain)
        logger.info(f"移除黑名单域名: {domain}")
    
    def add_allowed_domain(self, domain: str) -> None:
        """添加白名单域名"""
        self.allowed_domains.add(domain)
        logger.info(f"添加白名单域名: {domain}")
    
    def remove_allowed_domain(self, domain: str) -> None:
        """移除白名单域名"""
        self.allowed_domains.discard(domain)
        logger.info(f"移除白名单域名: {domain}")
    
    def get_domain_filters(self) -> Dict[str, List[str]]:
        """获取域名过滤配置"""
        return {
            "blocked_domains": list(self.blocked_domains),
            "allowed_domains": list(self.allowed_domains)
        }
    
    def set_domain_filters(
        self,
        blocked_domains: Optional[List[str]] = None,
        allowed_domains: Optional[List[str]] = None
    ) -> None:
        """设置域名过滤配置"""
        if blocked_domains is not None:
            self.blocked_domains = set(blocked_domains)
            logger.info(f"设置黑名单域名: {len(blocked_domains)} 个")
        
        if allowed_domains is not None:
            self.allowed_domains = set(allowed_domains)
            logger.info(f"设置白名单域名: {len(allowed_domains)} 个")


# 全局搜索服务实例
_unified_search_service = None


def get_unified_search_service() -> UnifiedSearchService:
    """获取统一搜索服务实例"""
    global _unified_search_service
    if _unified_search_service is None:
        _unified_search_service = UnifiedSearchService()
    return _unified_search_service
