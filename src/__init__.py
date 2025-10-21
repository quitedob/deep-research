# -*- coding: utf-8 -*-
"""
AgentWork - AI智能研究助手
基于LangGraph的多代理工作流系统
"""

# 轻量化 __init__，避免导入不存在的旧模块
# 保持旧接口名向后兼容：agent_graph / build_agent_graph
# 注意：graph 模块已移动到 core 目录，这里提供向后兼容的导入
# from .core.graph.builder import (
#     agent_graph,
#     build_agent_graph,
# )

__version__ = "2.0.0"
__all__ = [
    # "agent_graph",  # 暂时注释，需要时从 core.graph.builder 导入
    # "build_agent_graph",  # 暂时注释，需要时从 core.graph.builder 导入
    "__version__",
]
