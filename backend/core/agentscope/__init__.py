#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgentScope深度研究模块
提供基于AgentScope的智能研究功能
"""

from .llm_adapter import AgentScopeLLMAdapter, DualLLMManager, create_llm_manager
from .research_agent import DeepResearchAgent
from .memory.research_memory import ResearchSessionMemory, ResearchMemoryManager
from .tools import (
    WebSearchTool,
    WikipediaTool,
    ArXivTool,
    ImageAnalysisTool,
    SynthesisTool
)
from .config import (
    AgentScopeConfig,
    ConfigManager,
    get_config,
    reload_config,
    LLMConfig,
    MultimodalLLMConfig,
    ResearchConfig
)

__version__ = "1.0.0"

__all__ = [
    # LLM适配器
    "AgentScopeLLMAdapter",
    "DualLLMManager",
    "create_llm_manager",

    # 研究代理
    "DeepResearchAgent",

    # 记忆管理
    "ResearchSessionMemory",
    "ResearchMemoryManager",

    # 工具
    "WebSearchTool",
    "WikipediaTool",
    "ArXivTool",
    "ImageAnalysisTool",
    "SynthesisTool",

    # 配置
    "AgentScopeConfig",
    "ConfigManager",
    "get_config",
    "reload_config",
    "LLMConfig",
    "MultimodalLLMConfig",
    "ResearchConfig"
]