# -*- coding: utf-8 -*-
"""
arXiv学术论文搜索工具
用于搜索和获取学术论文信息
"""

import aiohttp
import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import re

logger = logging.getLogger(__name__)

@dataclass
class ArxivPaper:
    """arXiv论文数据类"""
    id: str
    title: str
    summary: str
    authors: List[str]
    published: str
    updated: str
    categories: List[str]
    pdf_url: str
    abs_url: str
    doi: Optional[str] = None
    comment: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "authors": self.authors,
            "published": self.published,
            "updated": self.updated,
            "categories": self.categories,
            "pdf_url": self.pdf_url,
            "abs_url": self.abs_url,
            "doi": self.doi,
            "comment": self.comment
        }

class ArxivSearchTool:
    """arXiv搜索工具"""
    
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
        self.session = None
        
        # arXiv分类映射
        self.categories = {
            "cs": "Computer Science",
            "math": "Mathematics", 
            "physics": "Physics",
            "q-bio": "Quantitative Biology",
            "q-fin": "Quantitative Finance",
            "stat": "Statistics",
            "eess": "Electrical Engineering and Systems Science",
            "econ": "Economics"
        }
        
    async def initialize(self) -> bool:
        """初始化arXiv工具"""
        try:
            connector = aiohttp.TCPConnector(limit=10)
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "User-Agent": "DeepResearch/1.0"
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize arXiv tool: {e}")
            return False
    
    async def search(
        self, 
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "descending",
        start: int = 0
    ) -> List[ArxivPaper]:
        """搜索arXiv论文"""
        if not self.session:
            await self.initialize()
        
        try:
            params = {
                "search_query": query,
                "start": start,
                "max_results": max_results,
                "sortBy": sort_by,
                "sortOrder": sort_order
            }
            
            async with self.session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"arXiv search failed: {response.status}")
                    return []
                
                content = await response.text()
                return self._parse_xml_response(content)
                
        except Exception as e:
            logger.error(f"arXiv search error: {e}")
            return []
    
    async def search_by_category(
        self,
        category: str,
        max_results: int = 10,
        sort_by: str = "lastUpdatedDate"
    ) -> List[ArxivPaper]:
        """按类别搜索论文"""
        query = f"cat:{category}"
        return await self.search(query, max_results, sort_by)
    
    async def search_by_author(
        self,
        author: str,
        max_results: int = 10
    ) -> List[ArxivPaper]:
        """按作者搜索论文"""
        query = f"au:{author}"
        return await self.search(query, max_results)
    
    async def search_by_title(
        self,
        title: str,
        max_results: int = 10
    ) -> List[ArxivPaper]:
        """按标题搜索论文"""
        query = f"ti:{title}"
        return await self.search(query, max_results)
    
    async def get_paper_by_id(self, arxiv_id: str) -> Optional[ArxivPaper]:
        """根据arXiv ID获取论文"""
        if not self.session:
            await self.initialize()
        
        try:
            params = {
                "id_list": arxiv_id,
                "max_results": 1
            }
            
            async with self.session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    return None
                
                content = await response.text()
                papers = self._parse_xml_response(content)
                
                return papers[0] if papers else None
                
        except Exception as e:
            logger.error(f"arXiv paper retrieval error: {e}")
            return None
    
    def _parse_xml_response(self, xml_content: str) -> List[ArxivPaper]:
        """解析XML响应"""
        try:
            root = ET.fromstring(xml_content)
            
            # 定义命名空间
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            papers = []
            
            for entry in root.findall('atom:entry', namespaces):
                try:
                    # 提取基本信息
                    id_elem = entry.find('atom:id', namespaces)
                    arxiv_id = id_elem.text.split('/')[-1] if id_elem is not None else ""
                    
                    title_elem = entry.find('atom:title', namespaces)
                    title = title_elem.text.strip() if title_elem is not None else ""
                    
                    summary_elem = entry.find('atom:summary', namespaces)
                    summary = summary_elem.text.strip() if summary_elem is not None else ""
                    
                    # 提取作者
                    authors = []
                    for author in entry.findall('atom:author', namespaces):
                        name_elem = author.find('atom:name', namespaces)
                        if name_elem is not None:
                            authors.append(name_elem.text.strip())
                    
                    # 提取日期
                    published_elem = entry.find('atom:published', namespaces)
                    published = published_elem.text if published_elem is not None else ""
                    
                    updated_elem = entry.find('atom:updated', namespaces)
                    updated = updated_elem.text if updated_elem is not None else ""
                    
                    # 提取分类
                    categories = []
                    for category in entry.findall('atom:category', namespaces):
                        term = category.get('term', '')
                        if term:
                            categories.append(term)
                    
                    # 提取链接
                    pdf_url = ""
                    abs_url = ""
                    for link in entry.findall('atom:link', namespaces):
                        href = link.get('href', '')
                        title_attr = link.get('title', '')
                        
                        if title_attr == 'pdf':
                            pdf_url = href
                        elif href and 'abs' in href:
                            abs_url = href
                    
                    # 提取DOI和注释
                    doi_elem = entry.find('arxiv:doi', namespaces)
                    doi = doi_elem.text if doi_elem is not None else None
                    
                    comment_elem = entry.find('arxiv:comment', namespaces)
                    comment = comment_elem.text if comment_elem is not None else None
                    
                    paper = ArxivPaper(
                        id=arxiv_id,
                        title=title,
                        summary=summary,
                        authors=authors,
                        published=published,
                        updated=updated,
                        categories=categories,
                        pdf_url=pdf_url,
                        abs_url=abs_url,
                        doi=doi,
                        comment=comment
                    )
                    
                    papers.append(paper)
                    
                except Exception as e:
                    logger.warning(f"Error parsing entry: {e}")
                    continue
            
            logger.info(f"Parsed {len(papers)} papers from arXiv response")
            return papers
            
        except Exception as e:
            logger.error(f"Error parsing XML response: {e}")
            return []
    
    async def get_recent_papers(
        self,
        category: Optional[str] = None,
        max_results: int = 10
    ) -> List[ArxivPaper]:
        """获取最近论文"""
        if category:
            query = f"cat:{category}"
        else:
            query = "all"
        
        return await self.search(
            query=query,
            max_results=max_results,
            sort_by="lastUpdatedDate",
            sort_order="descending"
        )
    
    async def search_advanced(
        self,
        title: Optional[str] = None,
        author: Optional[str] = None,
        abstract: Optional[str] = None,
        category: Optional[str] = None,
        all_fields: Optional[str] = None,
        max_results: int = 10
    ) -> List[ArxivPaper]:
        """高级搜索"""
        query_parts = []
        
        if title:
            query_parts.append(f"ti:{title}")
        if author:
            query_parts.append(f"au:{author}")
        if abstract:
            query_parts.append(f"abs:{abstract}")
        if category:
            query_parts.append(f"cat:{category}")
        if all_fields:
            query_parts.append(f"all:{all_fields}")
        
        if not query_parts:
            return []
        
        query = " AND ".join(query_parts)
        return await self.search(query, max_results)
    
    def get_categories(self) -> Dict[str, str]:
        """获取支持的分类"""
        return self.categories.copy()
    
    async def cleanup(self):
        """清理资源"""
        if self.session:
            await self.session.close()
            self.session = None

class ArxivService:
    """arXiv服务管理器"""
    
    def __init__(self):
        self.tool = ArxivSearchTool()
        
    async def search_papers(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance"
    ) -> List[ArxivPaper]:
        """搜索论文"""
        return await self.tool.search(query, max_results, sort_by)
    
    async def get_paper(self, arxiv_id: str) -> Optional[ArxivPaper]:
        """获取单篇论文"""
        return await self.tool.get_paper_by_id(arxiv_id)
    
    async def get_trending_papers(
        self,
        category: str = "cs.AI",
        max_results: int = 20
    ) -> List[ArxivPaper]:
        """获取热门论文"""
        return await self.tool.get_recent_papers(category, max_results)
    
    async def search_by_keywords(
        self,
        keywords: List[str],
        max_results: int = 10
    ) -> List[ArxivPaper]:
        """按关键词搜索"""
        query = " AND ".join([f"all:{keyword}" for keyword in keywords])
        return await self.tool.search(query, max_results)
    
    async def cleanup(self):
        """清理资源"""
        await self.tool.cleanup()

# 全局arXiv服务实例
_arxiv_service = None

def get_arxiv_service() -> ArxivService:
    """获取全局arXiv服务实例"""
    global _arxiv_service
    if _arxiv_service is None:
        _arxiv_service = ArxivService()
    return _arxiv_service

# 便捷函数
async def search_arxiv(query: str, max_results: int = 10) -> List[ArxivPaper]:
    """便捷的arXiv搜索函数"""
    service = get_arxiv_service()
    return await service.search_papers(query, max_results)
