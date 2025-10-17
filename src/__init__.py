# -*- coding: utf-8 -*-
"""
AgentWork - AI智能研究助手
基于LangGraph的多代理工作流系统
"""

# 轻量化 __init__，避免导入不存在的旧模块
# 保持旧接口名向后兼容：agent_graph / build_agent_graph
from .graph.builder import (
    agent_graph,
    build_agent_graph,
)

__version__ = "2.0.0"
__all__ = [
    "agent_graph",
    "build_agent_graph",
    "__version__",
]
