#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
常用工具集合
提供搜索、文档处理、代码分析等常用工具
"""
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
import logging

from .toolkit import Toolkit, ToolCategory, ToolResponse, ToolResponseType

logger = logging.getLogger(__name__)

# 创建常用工具集
common_toolkit = Toolkit(name="common", description="Common tools for agents")


@common_toolkit.tool(
    name="web_search",
    description="Search the web for information using DuckDuckGo",
    category=ToolCategory.SEARCH,
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 5
            }
        },
        "required": ["query"]
    }
)
async def web_search(query: str, max_results: int = 5) -> ToolResponse:
    """网络搜索工具"""
    try:
        from duckduckgo_search import AsyncDDGS
        
        async with AsyncDDGS() as ddgs:
            results = []
            async for result in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", "")
                })
            
            return ToolResponse(
                success=True,
                data=results,
                response_type=ToolResponseType.JSON,
                metadata={"query": query, "count": len(results)}
            )
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return ToolResponse(
            success=False,
            data=None,
            response_type=ToolResponseType.ERROR,
            error=str(e)
        )


@common_toolkit.tool(
    name="arxiv_search",
    description="Search academic papers on arXiv",
    category=ToolCategory.SEARCH,
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 5
            }
        },
        "required": ["query"]
    }
)
async def arxiv_search(query: str, max_results: int = 5) -> ToolResponse:
    """arXiv学术搜索"""
    try:
        import arxiv
        
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = []
        for paper in search.results():
            results.append({
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "summary": paper.summary,
                "published": paper.published.isoformat(),
                "pdf_url": paper.pdf_url,
                "entry_id": paper.entry_id
            })
        
        return ToolResponse(
            success=True,
            data=results,
            response_type=ToolResponseType.JSON,
            metadata={"query": query, "count": len(results)}
        )
    except Exception as e:
        logger.error(f"arXiv search error: {e}")
        return ToolResponse(
            success=False,
            data=None,
            response_type=ToolResponseType.ERROR,
            error=str(e)
        )


@common_toolkit.tool(
    name="wikipedia_search",
    description="Search Wikipedia for information",
    category=ToolCategory.SEARCH,
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"
            },
            "sentences": {
                "type": "integer",
                "description": "Number of sentences to return",
                "default": 3
            }
        },
        "required": ["query"]
    }
)
async def wikipedia_search(query: str, sentences: int = 3) -> ToolResponse:
    """Wikipedia搜索"""
    try:
        import wikipedia
        
        # 设置语言为中文
        wikipedia.set_lang("zh")
        
        try:
            summary = wikipedia.summary(query, sentences=sentences)
            page = wikipedia.page(query)
            
            return ToolResponse(
                success=True,
                data={
                    "summary": summary,
                    "url": page.url,
                    "title": page.title
                },
                response_type=ToolResponseType.JSON,
                metadata={"query": query}
            )
        except wikipedia.DisambiguationError as e:
            # 如果有歧义，返回选项
            return ToolResponse(
                success=True,
                data={
                    "disambiguation": True,
                    "options": e.options[:5]
                },
                response_type=ToolResponseType.JSON,
                metadata={"query": query}
            )
    except Exception as e:
        logger.error(f"Wikipedia search error: {e}")
        return ToolResponse(
            success=False,
            data=None,
            response_type=ToolResponseType.ERROR,
            error=str(e)
        )


@common_toolkit.tool(
    name="extract_text_from_url",
    description="Extract main text content from a URL",
    category=ToolCategory.WEB,
    parameters={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to extract text from"
            }
        },
        "required": ["url"]
    }
)
async def extract_text_from_url(url: str) -> ToolResponse:
    """从URL提取文本"""
    try:
        import trafilatura
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                html = await response.text()
        
        text = trafilatura.extract(html)
        
        if text:
            return ToolResponse(
                success=True,
                data=text,
                response_type=ToolResponseType.TEXT,
                metadata={"url": url, "length": len(text)}
            )
        else:
            return ToolResponse(
                success=False,
                data=None,
                response_type=ToolResponseType.ERROR,
                error="Failed to extract text from URL"
            )
    except Exception as e:
        logger.error(f"URL extraction error: {e}")
        return ToolResponse(
            success=False,
            data=None,
            response_type=ToolResponseType.ERROR,
            error=str(e)
        )


@common_toolkit.tool(
    name="calculate",
    description="Perform mathematical calculations",
    category=ToolCategory.UTILITY,
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate"
            }
        },
        "required": ["expression"]
    }
)
def calculate(expression: str) -> ToolResponse:
    """计算器工具"""
    try:
        # 安全的数学表达式求值
        import ast
        import operator
        
        # 支持的操作符
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }
        
        def eval_expr(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                return operators[type(node.op)](
                    eval_expr(node.left),
                    eval_expr(node.right)
                )
            elif isinstance(node, ast.UnaryOp):
                return operators[type(node.op)](eval_expr(node.operand))
            else:
                raise ValueError(f"Unsupported operation: {type(node)}")
        
        tree = ast.parse(expression, mode='eval')
        result = eval_expr(tree.body)
        
        return ToolResponse(
            success=True,
            data=result,
            response_type=ToolResponseType.TEXT,
            metadata={"expression": expression}
        )
    except Exception as e:
        logger.error(f"Calculation error: {e}")
        return ToolResponse(
            success=False,
            data=None,
            response_type=ToolResponseType.ERROR,
            error=str(e)
        )


def get_common_toolkit() -> Toolkit:
    """获取常用工具集"""
    return common_toolkit
