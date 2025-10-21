# -*- coding: utf-8 -*-
"""
Wikipedia搜索工具
支持多语言搜索和内容提取
"""

import aiohttp
import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class WikipediaPage:
    """Wikipedia页面数据类"""
    title: str
    extract: str
    url: str
    page_id: int
    language: str = "zh"
    categories: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "extract": self.extract,
            "url": self.url,
            "page_id": self.page_id,
            "language": self.language,
            "categories": self.categories or []
        }

@dataclass 
class WikipediaSearchResult:
    """Wikipedia搜索结果"""
    title: str
    snippet: str
    page_id: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "snippet": self.snippet,
            "page_id": self.page_id
        }

class WikipediaSearchTool:
    """Wikipedia搜索工具"""
    
    def __init__(self, default_language: str = "zh"):
        self.default_language = default_language
        self.session = None
        
        self.supported_languages = {
            "zh": "zh.wikipedia.org",
            "en": "en.wikipedia.org", 
            "ja": "ja.wikipedia.org"
        }
        
    async def initialize(self) -> bool:
        try:
            connector = aiohttp.TCPConnector(limit=20)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "User-Agent": "DeepResearch/1.0"
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Wikipedia tool: {e}")
            return False
    
    async def search(
        self, 
        query: str, 
        language: Optional[str] = None,
        limit: int = 10
    ) -> List[WikipediaSearchResult]:
        if not self.session:
            await self.initialize()
        
        language = language or self.default_language
        if language not in self.supported_languages:
            language = self.default_language
        
        try:
            base_url = f"https://{self.supported_languages[language]}/w/api.php"
            
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srlimit": limit,
                "srprop": "snippet"
            }
            
            async with self.session.get(base_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Wikipedia search failed: {response.status}")
                    return []
                
                data = await response.json()
                
                results = []
                for item in data.get("query", {}).get("search", []):
                    result = WikipediaSearchResult(
                        title=item.get("title", ""),
                        snippet=self._clean_snippet(item.get("snippet", "")),
                        page_id=item.get("pageid", 0)
                    )
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return []
    
    async def get_page(
        self, 
        title: str, 
        language: Optional[str] = None
    ) -> Optional[WikipediaPage]:
        if not self.session:
            await self.initialize()
        
        language = language or self.default_language
        if language not in self.supported_languages:
            language = self.default_language
        
        try:
            base_url = f"https://{self.supported_languages[language]}/w/api.php"
            
            params = {
                "action": "query",
                "format": "json",
                "titles": title,
                "prop": "extracts|info|categories",
                "exintro": True,
                "explaintext": True,
                "inprop": "url"
            }
            
            async with self.session.get(base_url, params=params) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                pages = data.get("query", {}).get("pages", {})
                
                if pages:
                    page_data = next(iter(pages.values()))
                    
                    if page_data.get("pageid", -1) == -1:
                        return None
                    
                    categories = []
                    for cat in page_data.get("categories", []):
                        cat_title = cat.get("title", "")
                        if cat_title.startswith("Category:"):
                            categories.append(cat_title[9:])
                    
                    return WikipediaPage(
                        title=page_data.get("title", ""),
                        extract=page_data.get("extract", ""),
                        url=page_data.get("fullurl", ""),
                        page_id=page_data.get("pageid", 0),
                        language=language,
                        categories=categories
                    )
                
                return None
                
        except Exception as e:
            logger.error(f"Wikipedia page retrieval error: {e}")
            return None
    
    def _clean_snippet(self, snippet: str) -> str:
        if not snippet:
            return ""
        
        clean_text = re.sub(r'<[^>]+>', '', snippet)
        clean_text = clean_text.replace('&quot;', '"')
        clean_text = clean_text.replace('&amp;', '&')
        
        return clean_text.strip()
    
    async def cleanup(self):
        if self.session:
            await self.session.close()
            self.session = None

# 全局实例
_wikipedia_tool = None

def get_wikipedia_tool() -> WikipediaSearchTool:
    global _wikipedia_tool
    if _wikipedia_tool is None:
        _wikipedia_tool = WikipediaSearchTool()
    return _wikipedia_tool
