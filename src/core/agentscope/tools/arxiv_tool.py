#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArXiv学术论文搜索工具
基于test_arxiv_api.py的arXiv论文检索功能
"""

import asyncio
from typing import Any, Dict, List, Optional
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

# ArXiv工具简单实现 (fallback)
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET


class ArXivTool:
    """
    ArXiv学术论文搜索工具
    用于搜索和获取学术论文信息
    """

    def __init__(self):
        """
        初始化ArXiv工具
        """
        self.arxiv_base_url = "http://export.arxiv.org/api/query"

    async def search_arxiv_papers(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "descending"
    ) -> ToolResponse:
        """
        搜索ArXiv论文

        Args:
            query: 搜索查询
            max_results: 最大结果数量
            sort_by: 排序方式 (relevance, lastUpdatedDate, submittedDate)
            sort_order: 排序顺序 (ascending, descending)

        Returns:
            搜索结果的ToolResponse
        """
        try:
            # 搜索arXiv论文
            papers = await self._search_arxiv(query, max_results, sort_by, sort_order)

            if not papers:
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"未找到关于 '{query}' 的arXiv论文。"
                    )])

            # 格式化搜索结果
            formatted_content = self._format_papers(papers, query)
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=formatted_content
                )])

        except Exception as e:
            error_msg = f"ArXiv搜索失败: {str(e)}"
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=error_msg
                )])

    async def search_by_category(
        self,
        category: str,
        max_results: int = 10
    ) -> ToolResponse:
        """
        按分类搜索ArXiv论文

        Args:
            category: ArXiv分类 (例如: cs.AI, physics.optics)
            max_results: 最大结果数量

        Returns:
            分类搜索结果的ToolResponse
        """
        try:
            # ✅ 修复：直接调用自身的 _search_arxiv 方法，使用分类查询
            query = f"cat:{category}"
            papers = await self._search_arxiv(query, max_results)

            if not papers:
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"未找到分类 '{category}' 下的arXiv论文。"
                    )])

            formatted_content = self._format_papers(papers, f"分类: {category}")
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=formatted_content
                )])

        except Exception as e:
            error_msg = f"按分类搜索ArXiv失败: {str(e)}"
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=error_msg
                )])

    async def search_by_author(
        self,
        author: str,
        max_results: int = 10
    ) -> ToolResponse:
        """
        按作者搜索ArXiv论文

        Args:
            author: 作者姓名
            max_results: 最大结果数量

        Returns:
            作者搜索结果的ToolResponse
        """
        try:
            # ✅ 修复：直接调用自身的 _search_arxiv 方法，使用作者查询
            query = f"au:{author}"
            papers = await self._search_arxiv(query, max_results)

            if not papers:
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"未找到作者 '{author}' 的arXiv论文。"
                    )])

            formatted_content = self._format_papers(papers, f"作者: {author}")
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=formatted_content
                )])

        except Exception as e:
            error_msg = f"按作者搜索ArXiv失败: {str(e)}"
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=error_msg
                )])

    async def get_paper_details(
        self,
        paper_id: str
    ) -> ToolResponse:
        """
        获取论文详细信息

        Args:
            paper_id: 论文ID (例如: "hep-ex/0307015" 或 "0307015")

        Returns:
            论文详细信息的ToolResponse
        """
        try:
            # ✅ 修复：直接调用自身的 _search_arxiv 方法，使用ID查询
            query = f"id:{paper_id}"
            papers = await self._search_arxiv(query, max_results=1)

            if not papers:
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"未找到论文ID '{paper_id}' 的详细信息。"
                    )])

            paper_details = papers[0]
            formatted_content = self._format_paper_details(paper_details)
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=formatted_content
                )])

        except Exception as e:
            error_msg = f"获取论文详细信息失败: {str(e)}"
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=error_msg
                )])

    async def get_recent_papers(
        self,
        category: str,
        days: int = 7,
        max_results: int = 20
    ) -> ToolResponse:
        """
        获取最近提交的论文

        Args:
            category: ArXiv分类
            days: 最近天数
            max_results: 最大结果数量

        Returns:
            最近论文的ToolResponse
        """
        try:
            # ✅ 修复：直接调用自身的 _search_arxiv 方法，按提交日期排序
            query = f"cat:{category}"
            recent_papers = await self._search_arxiv(
                query, 
                max_results=max_results,
                sort_by="submittedDate",
                sort_order="descending"
            )

            if not recent_papers:
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"未找到分类 '{category}' 最近 {days} 天内的论文。"
                    )])

            formatted_content = self._format_papers(
                recent_papers,
                f"分类 '{category}' 最近 {days} 天内的论文"
            )
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=formatted_content
                )])

        except Exception as e:
            error_msg = f"获取最近论文失败: {str(e)}"
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=error_msg
                )])

    def _format_papers(self, papers: List[Dict[str, Any]], search_context: str) -> str:
        """
        格式化论文列表

        Args:
            papers: 论文列表
            search_context: 搜索上下文描述

        Returns:
            格式化的论文信息字符串
        """
        formatted_content = f"ArXiv论文搜索结果 - {search_context}\n"
        formatted_content += "=" * 60 + "\n\n"

        for i, paper in enumerate(papers, 1):
            title = paper.get("title", "无标题")
            authors = paper.get("authors", [])
            summary = paper.get("summary", "无摘要")
            published = paper.get("published", "未知时间")
            categories = paper.get("categories", [])
            paper_id = paper.get("id", "未知ID")

            formatted_content += f"{i}. {title}\n"
            formatted_content += f"   ID: {paper_id}\n"
            formatted_content += f"   作者: {', '.join(authors[:3])}"
            if len(authors) > 3:
                formatted_content += f" 等 {len(authors)} 位作者"
            formatted_content += f"\n"
            formatted_content += f"   发布时间: {published[:10]}\n"
            formatted_content += f"   分类: {', '.join(categories[:3])}"
            if len(categories) > 3:
                formatted_content += " 等"
            formatted_content += f"\n\n"

            # 截取摘要
            summary_snippet = summary[:200] + "..." if len(summary) > 200 else summary
            formatted_content += f"   摘要: {summary_snippet}\n\n"

            if 'links' in paper and 'pdf' in paper['links']:
                pdf_url = paper['links']['pdf'].get('href', '')
                if pdf_url:
                    formatted_content += f"   PDF链接: {pdf_url}\n\n"

            formatted_content += "-" * 40 + "\n\n"

        return formatted_content

    def _format_paper_details(self, paper: Dict[str, Any]) -> str:
        """
        格式化单个论文的详细信息

        Args:
            paper: 论文信息字典

        Returns:
            格式化的论文详细信息字符串
        """
        title = paper.get("title", "无标题")
        authors = paper.get("authors", [])
        summary = paper.get("summary", "无摘要")
        published = paper.get("published", "未知时间")
        updated = paper.get("updated", "未知时间")
        categories = paper.get("categories", [])
        paper_id = paper.get("id", "未知ID")
        comments = paper.get("comment", "")
        journal_ref = paper.get("journal_ref", "")

        formatted_content = f"ArXiv论文详细信息\n"
        formatted_content += "=" * 30 + "\n\n"

        formatted_content += f"**标题**: {title}\n"
        formatted_content += f"**ID**: {paper_id}\n\n"

        formatted_content += f"**作者**: {', '.join(authors)}\n\n"

        formatted_content += f"**发布时间**: {published}\n"
        formatted_content += f"**更新时间**: {updated}\n\n"

        if journal_ref:
            formatted_content += f"**期刊引用**: {journal_ref}\n\n"

        if comments:
            formatted_content += f"**评论**: {comments}\n\n"

        formatted_content += f"**分类**: {', '.join(categories)}\n\n"

        formatted_content += f"**摘要**:\n{summary}\n\n"

        # 添加链接信息
        if 'links' in paper:
            formatted_content += f"**相关链接**:\n"
            for link_type, link_info in paper['links'].items():
                if isinstance(link_info, dict) and 'href' in link_info:
                    formatted_content += f"  - {link_type}: {link_info['href']}\n"

        return formatted_content

    async def _search_arxiv(self, query: str, max_results: int = 10,
                          sort_by: str = "relevance", sort_order: str = "descending") -> List[Dict]:
        """使用ArXiv API搜索论文"""
        try:
            # 构建查询参数
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': max_results,
                'sortBy': sort_by,
                'sortOrder': sort_order
            }

            encoded_params = urllib.parse.urlencode(params)
            url = f"{self.arxiv_base_url}?{encoded_params}"

            with urllib.request.urlopen(url) as response:
                xml_data = response.read().decode('utf-8')

            # 解析XML响应
            root = ET.fromstring(xml_data)
            papers = []

            # 命名空间
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }

            for entry in root.findall('atom:entry', ns):
                paper = {}

                # 基本信息
                paper['id'] = entry.find('atom:id', ns).text
                paper['title'] = entry.find('atom:title', ns).text.replace('\n', ' ').strip()
                paper['summary'] = entry.find('atom:summary', ns).text.replace('\n', ' ').strip()

                # 作者
                authors = []
                for author in entry.findall('atom:author', ns):
                    name = author.find('atom:name', ns).text
                    authors.append(name)
                paper['authors'] = authors

                # 发布日期
                published = entry.find('atom:published', ns).text
                paper['published'] = published

                # ArXiv链接和分类
                arxiv_url = ''
                primary_category = ''
                categories = []

                for link in entry.findall('atom:link', ns):
                    if link.get('title') == 'pdf':
                        paper['pdf_url'] = link.get('href')
                    elif link.get('type') == 'text/html':
                        arxiv_url = link.get('href')

                category_elem = entry.find('arxiv:primary_category', ns)
                if category_elem is not None:
                    primary_category = category_elem.get('term')

                for cat in entry.findall('arxiv:category', ns):
                    categories.append(cat.get('term'))

                paper['arxiv_url'] = arxiv_url
                paper['primary_category'] = primary_category
                paper['categories'] = categories
                paper['links'] = {'arxiv': {'href': arxiv_url}}

                papers.append(paper)

            return papers

        except Exception as e:
            print(f"ArXiv搜索错误: {e}")
            return []


def register_arxiv_tools(toolkit):
    """
    注册ArXiv相关工具到工具包

    Args:
        toolkit: AgentScope工具包
    """
    arxiv_tool = ArXivTool()

    # 注册基础ArXiv搜索
    toolkit.register_tool_function(
        arxiv_tool.search_arxiv_papers,
        func_description="在ArXiv中搜索学术论文"
    )

    # 注册按分类搜索
    toolkit.register_tool_function(
        arxiv_tool.search_by_category,
        func_description="按ArXiv分类搜索论文"
    )

    # 注册按作者搜索
    toolkit.register_tool_function(
        arxiv_tool.search_by_author,
        func_description="按作者搜索ArXiv论文"
    )

    # 注册获取论文详细信息
    toolkit.register_tool_function(
        arxiv_tool.get_paper_details,
        func_description="获取指定ArXiv论文的详细信息"
    )

    # 注册获取最近论文
    toolkit.register_tool_function(
        arxiv_tool.get_recent_papers,
        func_description="获取指定分类最近提交的论文"
    )

    return arxiv_tool