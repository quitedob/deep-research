#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgentScope研究工具模块
包含所有研究相关的工具实现
"""

from .web_search_tool import WebSearchTool, register_web_search_tools
from .wikipedia_tool import WikipediaTool, register_wikipedia_tools
from .arxiv_tool import ArXivTool, register_arxiv_tools
from .image_analysis_tool import ImageAnalysisTool, register_image_analysis_tools
from .synthesis_tool import SynthesisTool, register_synthesis_tools

__all__ = [
    "WebSearchTool",
    "register_web_search_tools",
    "WikipediaTool",
    "register_wikipedia_tools",
    "ArXivTool",
    "register_arxiv_tools",
    "ImageAnalysisTool",
    "register_image_analysis_tools",
    "SynthesisTool",
    "register_synthesis_tools"
]