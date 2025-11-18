#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
维基百科搜索工具
基于test_wiki_api.py的维基百科内容获取功能
"""

import asyncio
from typing import Any, Dict, List, Optional
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

# 维基百科工具的替代实现 (当原有工具不可用时)
import urllib.request
import urllib.parse
import json


class WikipediaTool:
    """
    维基百科搜索工具
    用于获取维基百科页面的详细内容
    """

    def __init__(self):
        """
        初始化维基百科工具
        """
        # 使用简单的Wikipedia API实现
        self.api_base = "https://zh.wikipedia.org/api/rest_v1"

    async def search_wikipedia(
        self,
        query: str,
        lang: str = "zh",
        max_results: int = 5
    ) -> ToolResponse:
        """
        搜索维基百科页面

        Args:
            query: 搜索查询
            lang: 语言代码 (zh, en等)
            max_results: 最大结果数量

        Returns:
            搜索结果的ToolResponse
        """
        try:
            # 使用Wikipedia API搜索
            search_url = f"https://{lang}.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": max_results,
                "utf8": 1
            }

            encoded_params = urllib.parse.urlencode(params)
            url = f"{search_url}?{encoded_params}"

            # 添加 User-Agent 请求头避免 403 错误
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (DeepResearch/1.0; +https://github.com/deep-research)',
                    'Accept': 'application/json'
                }
            )

            # 添加超时和重试机制
            import time
            max_retries = 3
            retry_delay = 2

            for attempt in range(max_retries):
                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        data = json.loads(response.read().decode('utf-8'))
                    break
                except urllib.error.HTTPError as e:
                    if e.code == 403 and attempt < max_retries - 1:
                        print(f"[WARN] Wikipedia 403 error, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        raise

            search_results = data.get("query", {}).get("search", [])

            if not search_results:
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"未找到关于 '{query}' 的维基百科页面。"
                    )])

            # 格式化搜索结果
            formatted_content = f"维基百科搜索结果: '{query}'\n\n"

            for i, page in enumerate(search_results[:max_results], 1):
                title = page.get("title", "无标题")
                page_id = page.get("pageid", "未知ID")
                snippet = page.get("snippet", "无摘要").replace('<span class="searchmatch">', '').replace('</span>', '')

                formatted_content += f"{i}. {title}\n"
                formatted_content += f"   页面ID: {page_id}\n"
                formatted_content += f"   摘要: {snippet}\n\n"

            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=formatted_content
                )])

        except Exception as e:
            error_msg = f"维基百科搜索失败: {str(e)}"
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=error_msg
                )])

    async def get_wikipedia_content(
        self,
        page_title: str,
        lang: str = "zh",
        sections: Optional[List[str]] = None
    ) -> ToolResponse:
        """
        获取维基百科页面的完整内容

        Args:
            page_title: 页面标题
            lang: 语言代码
            sections: 指定获取的章节，None表示获取全部

        Returns:
            页面内容的ToolResponse
        """
        try:
            # 获取页面内容
            page_content = await self.get_page_content(
                page_title=page_title,
                lang=lang
            )

            if not page_content:
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"未找到页面 '{page_title}' 的内容。"
                    )])

            # 获取页面详细信息
            page_details = await self.get_page_details(
                page_title=page_title,
                lang=lang
            )

            # 格式化内容
            formatted_content = f"维基百科页面内容: {page_title}\n"
            formatted_content += "=" * 50 + "\n\n"

            if page_details:
                # 添加基本信息
                formatted_content += "**基本信息**\n"
                formatted_content += f"标题: {page_details.get('title', page_title)}\n"
                formatted_content += f"最后修改: {page_details.get('lastmodified', '未知')}\n"
                formatted_content += f"页面大小: {page_details.get('length', 0)} 字节\n"

                if 'categories' in page_details:
                    categories = page_details['categories'][:5]  # 只显示前5个分类
                    formatted_content += f"分类: {', '.join(categories)}\n"

                formatted_content += f"链接: {page_details.get('fullurl', '')}\n\n"

            # 添加页面内容
            formatted_content += "**页面内容**\n\n"
            
            # 检查内容长度并适当截断 - 增加长度限制以提供更多信息
            if len(page_content) > 5000:
                formatted_content += page_content[:5000]
                formatted_content += f"\n\n⚠️ [内容已截断，完整内容共 {len(page_content)} 字符。"
                formatted_content += f"已获取足够信息，建议继续下一步研究。"
                formatted_content += f"页面链接: {page_details.get('fullurl', '') if page_details else ''}]"
            else:
                formatted_content += page_content
                if len(page_content) > 1000:
                    formatted_content += "\n\n✓ 已获取完整内容，建议继续下一步研究（如搜索学术论文）。"

            # 如果指定了章节，尝试提取相关章节内容
            if sections:
                section_content = self._extract_sections(page_content, sections)
                if section_content:
                    formatted_content += "\n\n**指定章节内容**\n\n"
                    formatted_content += section_content

            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=formatted_content
                )])

        except Exception as e:
            error_msg = f"获取维基百科内容失败: {str(e)}"
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=error_msg
                )])

    def _extract_sections(self, content: str, sections: List[str]) -> str:
        """
        从内容中提取指定章节

        Args:
            content: 页面内容
            sections: 要提取的章节列表

        Returns:
            提取的章节内容
        """
        lines = content.split('\n')
        extracted_content = []
        current_section = None
        section_lines = []

        for line in lines:
            # 检测章节标题
            if line.startswith('=') and line.endswith('='):
                # 保存上一章节的内容
                if current_section and current_section in sections and section_lines:
                    extracted_content.extend(section_lines)

                # 提取新章节名
                section_name = line.strip('= ').strip()
                current_section = section_name
                section_lines = []

                if current_section in sections:
                    section_lines.append(line)  # 保留章节标题
            else:
                # 累积当前章节的内容
                if current_section and current_section in sections:
                    section_lines.append(line)

        # 处理最后一章节
        if current_section and current_section in sections and section_lines:
            extracted_content.extend(section_lines)

        return '\n'.join(extracted_content)

    async def get_wikipedia_summary(
        self,
        page_title: str,
        lang: str = "zh"
    ) -> ToolResponse:
        """
        获取维基百科页面摘要

        Args:
            page_title: 页面标题
            lang: 语言代码

        Returns:
            页面摘要的ToolResponse
        """
        try:
            # 获取页面摘要
            summary = await self.get_page_summary(
                page_title=page_title,
                lang=lang
            )

            if not summary:
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"未找到页面 '{page_title}' 的摘要。"
                    )])

            formatted_content = f"维基百科摘要: {page_title}\n"
            formatted_content += "=" * 30 + "\n\n"
            formatted_content += summary

            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=formatted_content
                )])

        except Exception as e:
            error_msg = f"获取维基百科摘要失败: {str(e)}"
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=error_msg
                )])

    async def search_related_pages(
        self,
        page_title: str,
        lang: str = "zh",
        max_related: int = 5
    ) -> ToolResponse:
        """
        搜索相关页面

        Args:
            page_title: 基础页面标题
            lang: 语言代码
            max_related: 最大相关页面数量

        Returns:
            相关页面的ToolResponse
        """
        try:
            # 获取页面详细信息以提取链接
            page_details = await self.get_page_details(
                page_title=page_title,
                lang=lang
            )

            if not page_details or 'links' not in page_details:
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"无法获取页面 '{page_title}' 的相关信息。"
                    )])

            links = page_details['links'][:max_related]

            formatted_content = f"与 '{page_title}' 相关的页面:\n\n"

            for i, link in enumerate(links, 1):
                formatted_content += f"{i}. {link}\n"

            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=formatted_content
                )])

        except Exception as e:
            error_msg = f"搜索相关页面失败: {str(e)}"
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=error_msg
                )])

    async def get_page_content(self, page_title: str, lang: str = "zh") -> Optional[str]:
        """获取页面内容的辅助方法 - 获取完整文本内容"""
        try:
            # 使用Wikipedia API获取完整页面文本
            search_url = f"https://{lang}.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "prop": "extracts",
                "titles": page_title,
                "format": "json",
                "explaintext": 1,  # 获取纯文本
                "exsectionformat": "plain",
                "utf8": 1
            }

            encoded_params = urllib.parse.urlencode(params)
            url = f"{search_url}?{encoded_params}"

            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (DeepResearch/1.0; +https://github.com/deep-research)',
                    'Accept': 'application/json'
                }
            )

            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            pages = data.get("query", {}).get("pages", {})
            page_id = next(iter(pages.keys()))
            page_data = pages.get(page_id, {})
            
            if page_id == "-1":  # 页面不存在
                return None
                
            extract = page_data.get('extract', '')
            
            # 如果内容太短，添加提示
            if extract and len(extract) < 500:
                extract += "\n\n⚠️ 注意: 该页面内容较短。建议搜索其他相关页面获取更多信息。"
            
            return extract
        except Exception as e:
            print(f"获取Wikipedia内容失败: {str(e)}")
            return None

    async def get_page_details(self, page_title: str, lang: str = "zh") -> Optional[Dict]:
        """获取页面详细信息的辅助方法"""
        try:
            # 使用Wikipedia API获取页面详细信息
            search_url = f"https://{lang}.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "prop": "info|links|categories",
                "titles": page_title,
                "format": "json",
                "pllimit": 10,
                "cllimit": 10,
                "utf8": 1,
                "inprop": "url|lastmodified|length"
            }

            encoded_params = urllib.parse.urlencode(params)
            url = f"{search_url}?{encoded_params}"

            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (DeepResearch/1.0; +https://github.com/deep-research)',
                    'Accept': 'application/json'
                }
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

            pages = data.get("query", {}).get("pages", {})
            page_id = next(iter(pages.keys()))
            page_data = pages.get(page_id, {})

            if page_id == "-1":  # 页面不存在
                return None

            # 提取链接和分类
            links = [link.get("title", "") for link in page_data.get("links", []) if link.get("title")]
            categories = [cat.get("title", "").replace("Category:", "") for cat in page_data.get("categories", []) if cat.get("title")]

            return {
                "title": page_data.get("title", page_title),
                "lastmodified": page_data.get("touched", ""),
                "length": page_data.get("length", 0),
                "fullurl": page_data.get("fullurl", ""),
                "links": links,
                "categories": categories
            }
        except:
            return None

    async def get_page_summary(self, page_title: str, lang: str = "zh") -> Optional[str]:
        """获取页面摘要的辅助方法"""
        content = await self.get_page_content(page_title, lang)
        return content[:500] + "..." if content and len(content) > 500 else content


def register_wikipedia_tools(toolkit):
    """
    注册维基百科相关工具到工具包

    Args:
        toolkit: AgentScope工具包
    """
    wiki_tool = WikipediaTool()

    # 注册维基百科搜索
    toolkit.register_tool_function(
        wiki_tool.search_wikipedia,
        func_description="在维基百科中搜索相关页面和文章"
    )

    # 注册获取维基百科内容
    toolkit.register_tool_function(
        wiki_tool.get_wikipedia_content,
        func_description="获取指定维基百科页面的完整内容"
    )

    # 注册获取维基百科摘要
    toolkit.register_tool_function(
        wiki_tool.get_wikipedia_summary,
        func_description="获取指定维基百科页面的简要摘要"
    )

    # 注册搜索相关页面
    toolkit.register_tool_function(
        wiki_tool.search_related_pages,
        func_description="搜索与指定页面相关的其他维基百科页面"
    )

    return wiki_tool