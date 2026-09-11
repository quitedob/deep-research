#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络搜索工具
基于BigModel MCP的网络搜索功能
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

import os
from backend.core.llm.zhipu_llm import ZhipuLLM
from backend.core.llm.base_llm import APIError


class WebSearchTool:
    """
    网络搜索工具
    用于执行实时网络搜索
    """

    def __init__(self, api_key: str):
        """
        初始化网络搜索工具

        Args:
            api_key: BigModel API密钥 (MCP工具通过环境变量配置)
        """
        self.api_key = api_key or os.getenv("WEB_SEARCH_API_KEY") or os.getenv("BIGMODEL_API_KEY") or os.getenv("ZHIPU_API_KEY")
        self._llm = ZhipuLLM(api_key=self.api_key, timeout=30, max_retries=2)

    async def close(self):
        await self._llm.close()

    async def web_search(self, query: str, max_results: int = 10,
                         search_domain_filter: Optional[str] = None,
                         search_recency_filter: str = "oneMonth") -> ToolResponse:
        """Search the web asynchronously and return the provider's sourced result."""
        response = await self._llm.web_search(
            search_query=query[:70], search_engine=os.getenv("WEB_SEARCH_ENGINE", "search_pro"),
            count=max(1, min(max_results, 50)), search_domain_filter=search_domain_filter,
            search_recency_filter=search_recency_filter,
        )
        sources = response.get("search_result")
        if not isinstance(sources, list):
            raise APIError("Web search returned an invalid response")
        results = [{"title": item.get("title"), "url": item.get("link", ""),
                    "snippet": item.get("content", ""), "website_name": item.get("media", "")}
                   for item in sources]
        return ToolResponse(content=[TextBlock(type="text", text=self._format_search_results(results, query))],
                            metadata={"sources": sources})

    def _format_search_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """
        格式化搜索结果 (兼容旧格式)

        Args:
            results: 搜索结果列表
            query: 搜索查询

        Returns:
            格式化的搜索结果字符串
        """
        if not results:
            return f"未找到关于 '{query}' 的相关结果。"

        content = f"网络搜索结果: '{query}'\n\n"

        for i, result in enumerate(results, 1):
            title = result.get("title", "无标题")
            url = result.get("url", "")
            snippet = result.get("snippet", "无摘要")
            website_name = result.get("website_name", "未知网站")

            content += f"{i}. {title}\n"
            content += f"   网站: {website_name}\n"
            content += f"   链接: {url}\n"
            content += f"   摘要: {snippet}\n\n"

        content += f"\n总共找到 {len(results)} 个相关结果。"
        return content

    def _format_mcp_search_results(self, results: List, query: str) -> str:
        """
        格式化MCP搜索结果

        Args:
            results: MCP搜索结果列表
            query: 搜索查询

        Returns:
            格式化的搜索结果字符串
        """
        if not results:
            return f"未找到关于 '{query}' 的相关结果。"

        content = f"网络搜索结果: '{query}'\n\n"

        for i, result in enumerate(results, 1):
            # MCP结果的字段可能不同，需要适配
            title = getattr(result, 'title', '无标题')
            url = getattr(result, 'url', '')
            snippet = getattr(result, 'snippet', '无摘要')
            website_name = getattr(result, 'website_name', getattr(result, 'siteName', '未知网站'))

            content += f"{i}. {title}\n"
            content += f"   网站: {website_name}\n"
            content += f"   链接: {url}\n"
            content += f"   摘要: {snippet}\n\n"

        content += f"\n总共找到 {len(results)} 个相关结果。"
        return content

    async def news_search(
        self,
        query: str,
        max_results: int = 5
    ) -> ToolResponse:
        """
        搜索新闻

        Args:
            query: 新闻搜索查询
            max_results: 最大结果数量

        Returns:
            新闻搜索结果的ToolResponse
        """
        return await self.web_search(
            query=f"{query} 新闻 最新消息",
            max_results=max_results,
            search_recency_filter="oneWeek"
        )

    async def academic_search(
        self,
        query: str,
        max_results: int = 8
    ) -> ToolResponse:
        """
        学术搜索

        Args:
            query: 学术搜索查询
            max_results: 最大结果数量

        Returns:
            学术搜索结果的ToolResponse
        """
        academic_domains = [
            "scholar.google.com",
            "arxiv.org",
            "researchgate.net",
            "ieeexplore.ieee.org",
            "dl.acm.org",
            "springer.com",
            "sciencedirect.com"
        ]

        content_parts = []

        for domain in academic_domains:
            try:
                results = await self.web_search(
                    query=query,
                    max_results=max(1, max_results // len(academic_domains)),
                    search_domain_filter=domain
                )

                if results.content:
                    content_parts.append(results.content[0]["text"])

                # 添加延时避免请求过于频繁
                await asyncio.sleep(0.5)

            except Exception as e:
                continue

        if content_parts:
            combined_content = f"学术搜索结果: '{query}'\n\n" + "\n\n".join(content_parts)
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=combined_content
                )])
        else:
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=f"未找到关于 '{query}' 的学术搜索结果。"
                )])


# 注册为AgentScope工具函数的装饰器
def register_web_search_tools(toolkit, api_key: str):
    """
    注册网络搜索相关工具到工具包

    Args:
        toolkit: AgentScope工具包
        api_key: BigModel API密钥
    """
    web_tool = WebSearchTool(api_key)

    # 注册基础网络搜索
    toolkit.register_tool_function(
        web_tool.web_search,
        func_description="执行实时网络搜索获取最新信息"
    )

    # 注册新闻搜索
    toolkit.register_tool_function(
        web_tool.news_search,
        func_description="搜索最新新闻和时事信息"
    )

    # 注册学术搜索
    toolkit.register_tool_function(
        web_tool.academic_search,
        func_description="在学术网站和专业数据库中搜索研究资料"
    )

    return web_tool