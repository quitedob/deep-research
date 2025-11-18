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

# 导入MCP web search prime 工具
web_search_prime = None
try:
    # Try to import the MCP tool function directly
    import sys
    # Check if the MCP tool is available in the current context
    if 'mcp_web_search_prime_webSearchPrime' in dir():
        from mcp_web_search_prime_webSearchPrime import webSearchPrime
        web_search_prime = type('obj', (object,), {'webSearchPrime': webSearchPrime})()
except Exception as e:
    print(f"[INFO] MCP Web Search Prime not available: {e}")
    web_search_prime = None


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
        self.api_key = api_key

    async def web_search(
        self,
        query: str,
        max_results: int = 10,
        search_domain_filter: Optional[str] = None,
        search_recency_filter: str = "oneMonth"
    ) -> ToolResponse:
        """
        执行网络搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数量
            search_domain_filter: 搜索域名过滤
            search_recency_filter: 搜索时间范围过滤

        Returns:
            搜索结果的ToolResponse
        """
        try:
            # 优先使用 ZhipuAI 网络搜索功能
            try:
                import os
                from zhipuai import ZhipuAI
                
                api_key = os.getenv("BIGMODEL_API_KEY", self.api_key)
                if api_key:
                    client = ZhipuAI(api_key=api_key)
                    
                    # 使用 ZhipuAI 的 web_search 工具
                    response = client.chat.completions.create(
                        model="glm-4.5-flash",
                        messages=[
                            {
                                "role": "user", 
                                "content": f"请搜索并详细总结关于以下主题的信息，包括定义、特点、应用和最新发展：{query}"
                            }
                        ],
                        tools=[{
                            "type": "web_search",
                            "web_search": {
                                "enable": True,
                                "search_query": query
                            }
                        }],
                        temperature=0.7
                    )
                    
                    content = response.choices[0].message.content
                    
                    # 格式化返回结果
                    formatted_content = f"网络搜索结果 - '{query}'\n"
                    formatted_content += "=" * 60 + "\n\n"
                    formatted_content += content
                    formatted_content += f"\n\n搜索时间范围: {search_recency_filter}"
                    
                    return ToolResponse(
                        content=[TextBlock(
                            type="text",
                            text=formatted_content
                        )])
            except Exception as e:
                print(f"[INFO] ZhipuAI web search not available: {e}")
            
            # 备用方案：返回建议信息
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=(
                        f"网络搜索暂时不可用。搜索查询: '{query}'\n\n"
                        f"建议使用以下替代方案：\n"
                        f"1. search_arxiv_papers - 搜索学术论文获取权威信息\n"
                        f"2. search_wikipedia - 搜索维基百科获取基础知识\n"
                        f"3. get_wikipedia_content - 获取详细的百科内容"
                    )
                )])

            # 格式化搜索结果
            if results and len(results) > 0:
                formatted_content = self._format_mcp_search_results(results, query)
            else:
                formatted_content = f"未找到关于 '{query}' 的搜索结果。"

            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=formatted_content
                )]
            )

        except Exception as e:
            error_msg = f"网络搜索失败: {str(e)}"
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=error_msg
                )])

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
                    max_results=max_results // len(academic_domains),
                    search_domain_filter=domain
                )

                if results.success:
                    content_parts.append(results.content[0].text)

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