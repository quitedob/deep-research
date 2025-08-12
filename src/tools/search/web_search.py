# -*- coding: utf-8 -*-
"""
通用Web搜索工具
支持kimi引擎
"""

import os
import aiohttp
import asyncio
import logging
import time
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """搜索结果数据类"""
    title: str
    url: str
    snippet: str
    source: str = ""
    score: float = 0.0
    published_date: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "score": self.score,
            "published_date": self.published_date
        }

class BaseSearchEngine(ABC):
    """搜索引擎基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.session = None
        
    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """执行搜索"""
        pass
    
    async def initialize(self) -> bool:
        """初始化搜索引擎"""
        try:
            connector = aiohttp.TCPConnector(limit=20)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize {self.name}: {e}")
            return False
    
    async def cleanup(self):
        """清理资源"""
        if self.session:
            await self.session.close()
            self.session = None

class TavilySearchEngine(BaseSearchEngine):
    """Tavily搜索引擎"""
    
    def __init__(self, api_key: str = None):
        super().__init__("tavily")
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.base_url = "https://api.tavily.com"
        
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """使用Tavily搜索"""
        if not self.api_key:
            logger.error("Tavily API key not provided")
            return []
        
        if not self.session:
            await self.initialize()
        
        try:
            request_data = {
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
                "include_answer": False,
                "include_images": False,
                "include_raw_content": False
            }
            
            async with self.session.post(
                f"{self.base_url}/search",
                json=request_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Tavily search failed: {response.status} - {error_text}")
                    return []
                
                data = await response.json()
                results = []
                
                for item in data.get("results", []):
                    result = SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("content", ""),
                        source="tavily",
                        score=item.get("score", 0.0),
                        published_date=item.get("published_date")
                    )
                    results.append(result)
                
                logger.info(f"Tavily search returned {len(results)} results")
                return results
                
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return []

class DuckDuckGoSearchEngine(BaseSearchEngine):
    """DuckDuckGo搜索引擎"""
    
    def __init__(self):
        super().__init__("duckduckgo")
        
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """使用DuckDuckGo搜索"""
        if not self.session:
            await self.initialize()
        
        try:
            # DuckDuckGo instant answer API
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            async with self.session.get(
                "https://api.duckduckgo.com/",
                params=params
            ) as response:
                if response.status != 200:
                    logger.error(f"DuckDuckGo search failed: {response.status}")
                    return []
                
                data = await response.json()
                results = []
                
                # 处理即时答案
                if data.get("Abstract"):
                    result = SearchResult(
                        title=data.get("Heading", "DuckDuckGo Answer"),
                        url=data.get("AbstractURL", ""),
                        snippet=data.get("Abstract", ""),
                        source="duckduckgo",
                        score=1.0
                    )
                    results.append(result)
                
                # 处理相关主题
                for topic in data.get("RelatedTopics", [])[:max_results-1]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        result = SearchResult(
                            title=topic.get("Text", "").split(" - ")[0],
                            url=topic.get("FirstURL", ""),
                            snippet=topic.get("Text", ""),
                            source="duckduckgo",
                            score=0.8
                        )
                        results.append(result)
                
                logger.info(f"DuckDuckGo search returned {len(results)} results")
                return results[:max_results]
                
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []

class WebSearchService:
    """Web搜索服务管理器"""
    
    def __init__(self):
        self.engines: Dict[str, BaseSearchEngine] = {}
        self.default_engines = []
        self._initialize_engines()
        
    def _initialize_engines(self):
        """初始化搜索引擎"""
        try:
            # 按优先级初始化搜索引擎
            engines_config = [
                ("tavily", TavilySearchEngine),
                ("duckduckgo", DuckDuckGoSearchEngine)
            ]
            
            for name, engine_class in engines_config:
                try:
                    engine = engine_class()
                    self.engines[name] = engine
                    
                    # 检查是否可用（有API密钥等）
                    if self._is_engine_available(engine):
                        self.default_engines.append(name)
                        
                except Exception as e:
                    logger.warning(f"Failed to initialize {name} engine: {e}")
            
            logger.info(f"Initialized {len(self.engines)} search engines: {list(self.engines.keys())}")
            logger.info(f"Available engines: {self.default_engines}")
            
        except Exception as e:
            logger.error(f"Failed to initialize search engines: {e}")
    
    def _is_engine_available(self, engine: BaseSearchEngine) -> bool:
        """检查搜索引擎是否可用"""
        if isinstance(engine, TavilySearchEngine):
            return bool(engine.api_key)
        elif isinstance(engine, DuckDuckGoSearchEngine):
            return True  # DuckDuckGo不需要API密钥
        else:
            return True
    
    async def search(
        self, 
        query: str, 
        max_results: int = 10,
        engines: Optional[List[str]] = None,
        fallback: bool = True
    ) -> List[SearchResult]:
        """执行搜索"""
        if not engines:
            engines = self.default_engines[:2] if len(self.default_engines) >= 2 else self.default_engines
        
        all_results = []
        successful_engines = []
        
        # 并行搜索多个引擎
        search_tasks = []
        for engine_name in engines:
            if engine_name in self.engines:
                engine = self.engines[engine_name]
                task = asyncio.create_task(
                    self._search_with_engine(engine, query, max_results)
                )
                search_tasks.append((engine_name, task))
        
        # 等待所有搜索完成
        for engine_name, task in search_tasks:
            try:
                results = await task
                if results:
                    all_results.extend(results)
                    successful_engines.append(engine_name)
                    logger.info(f"Engine {engine_name} returned {len(results)} results")
            except Exception as e:
                logger.error(f"Search failed for engine {engine_name}: {e}")
        
        # 如果没有结果且启用回退，尝试其他引擎
        if not all_results and fallback:
            for engine_name, engine in self.engines.items():
                if engine_name not in engines:
                    try:
                        results = await self._search_with_engine(engine, query, max_results)
                        if results:
                            all_results.extend(results)
                            successful_engines.append(engine_name)
                            logger.info(f"Fallback engine {engine_name} returned {len(results)} results")
                            break
                    except Exception as e:
                        logger.warning(f"Fallback search failed for {engine_name}: {e}")
        
        # 去重和排序
        unique_results = self._deduplicate_results(all_results)
        sorted_results = sorted(unique_results, key=lambda x: x.score, reverse=True)
        
        logger.info(f"Total unique results: {len(sorted_results)} from engines: {successful_engines}")
        return sorted_results[:max_results]
    
    async def _search_with_engine(self, engine: BaseSearchEngine, query: str, max_results: int) -> List[SearchResult]:
        """使用指定引擎搜索"""
        try:
            if not engine.session:
                await engine.initialize()
            return await engine.search(query, max_results)
        except Exception as e:
            logger.error(f"Search failed for {engine.name}: {e}")
            return []
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """去重搜索结果"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        return unique_results

# 全局搜索服务实例
_web_search_service = None

def get_web_search_service() -> WebSearchService:
    """获取全局Web搜索服务实例"""
    global _web_search_service
    if _web_search_service is None:
        _web_search_service = WebSearchService()
    return _web_search_service

# 便捷函数
async def search_web(query: str, max_results: int = 10, engines: Optional[List[str]] = None) -> List[SearchResult]:
    """便捷的Web搜索函数"""
    service = get_web_search_service()
    return await service.search(query, max_results, engines)
