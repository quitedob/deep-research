# -*- coding: utf-8 -*-
"""
AgentWork - AI智能研究助手
基于LangGraph的多代理工作流系统
"""

# 轻量化 __init__，避免导入不存在的旧模块
from .graph.builder import agent_graph, build_agent_graph  # 导出当前工作流图

__version__ = "2.0.0"
__all__ = ["agent_graph", "build_agent_graph", "__version__"]
