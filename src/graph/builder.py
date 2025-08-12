# -*- coding: utf-8 -*-
"""
AgentWork 工作流图构建器
构建多代理工作流的图结构
"""

import logging
from typing import Literal

try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    # 提供基础实现
    class StateGraph:
        def __init__(self, state_class):
            self.state_class = state_class
            self.nodes = {}
            self.edges = []
        
        def add_node(self, name, func):
            self.nodes[name] = func
        
        def add_edge(self, from_node, to_node):
            self.edges.append((from_node, to_node))
        
        def compile(self, **kwargs):
            return MockGraph(self)
    
    class MockGraph:
        def __init__(self, builder):
            self.builder = builder
        
        async def astream(self, input, config=None, stream_mode="values"):
            # 简单的模拟实现
            yield input
            
        def get_graph(self, xray=False):
            return MockGraphView()
    
    class MockGraphView:
        def draw_mermaid(self):
            return "graph TD\n    A[Start] --> B[End]"
    
    START = "START"
    END = "END"

from .types import State, StepType
from .nodes import (
    coordinator_node,
    planner_node,
    researcher_node,
    reporter_node,
    background_investigation_node,
    triage_node,
    simple_chat_node,
)

logger = logging.getLogger(__name__)


def continue_to_running_research_team(state: State) -> Literal["planner", "researcher", "reporter", "simple_chat"]:
    """决定下一个要执行的节点"""
    try:
        # 如果是简单聊天请求，直接路由到聊天节点
        if hasattr(state, 'chat_mode') and state.chat_mode:
            return "simple_chat"
        
        current_plan = getattr(state, 'current_plan', None)
        if not current_plan:
            return "planner"
        
        # 如果计划是字符串类型，说明还在规划阶段
        if isinstance(current_plan, str):
            return "planner"
        
        # 检查是否所有步骤都已完成
        if hasattr(current_plan, 'steps') and current_plan.steps:
            if all(step.execution_res for step in current_plan.steps):
                return "reporter"
            
            # 找到第一个未完成的步骤
            incomplete_step = None
            for step in current_plan.steps:
                if not step.execution_res:
                    incomplete_step = step
                    break
            
            if incomplete_step:
                if hasattr(incomplete_step, 'step_type'):
                    if incomplete_step.step_type == StepType.RESEARCH:
                        return "researcher"
                    elif incomplete_step.step_type == StepType.PROCESSING:
                        return "researcher"  # 暂时都用researcher处理
                
        return "reporter"
        
    except Exception as e:
        logger.error(f"路由决策错误: {e}")
        return "reporter"


def _build_base_graph():
    """构建基础状态图，包含所有节点和边"""
    if not LANGGRAPH_AVAILABLE:
        logger.warning("LangGraph不可用，使用模拟实现")
    
    builder = StateGraph(State)
    
    # 添加节点
    builder.add_node("coordinator", coordinator_node)
    builder.add_node("triage", triage_node) 
    builder.add_node("simple_chat", simple_chat_node)
    builder.add_node("background_investigator", background_investigation_node)
    builder.add_node("planner", planner_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("reporter", reporter_node)
    
    # 添加边
    builder.add_edge(START, "coordinator")
    builder.add_edge("coordinator", "triage")
    
    # 条件路由
    if LANGGRAPH_AVAILABLE:
        builder.add_conditional_edges(
            "triage",
            lambda state: "simple_chat" if getattr(state, 'chat_mode', False) else "background_investigator",
            ["simple_chat", "background_investigator"]
        )
        
        builder.add_conditional_edges(
            "researcher",
            continue_to_running_research_team,
            ["planner", "researcher", "reporter"]
        )
    else:
        # 简化的边连接
        builder.add_edge("triage", "background_investigator")
        builder.add_edge("researcher", "reporter")
    
    builder.add_edge("simple_chat", END)
    builder.add_edge("background_investigator", "planner") 
    builder.add_edge("planner", "researcher")
    builder.add_edge("reporter", END)
    
    return builder


def build_graph_with_memory():
    """构建带有内存的代理工作流图"""
    if not LANGGRAPH_AVAILABLE:
        logger.warning("LangGraph不可用，构建无内存版本")
        return build_graph()
    
    try:
        # 使用持久内存保存对话历史
        memory = MemorySaver()
        
        # 构建状态图
        builder = _build_base_graph()
        return builder.compile(checkpointer=memory)
    except Exception as e:
        logger.error(f"构建带内存图失败: {e}")
        return build_graph()


def build_graph():
    """构建代理工作流图（无内存）"""
    try:
        # 构建状态图
        builder = _build_base_graph()
        return builder.compile()
    except Exception as e:
        logger.error(f"构建图失败: {e}")
        # 返回一个最小可用的图
        return MockGraph(builder) if not LANGGRAPH_AVAILABLE else None


def get_graph_info() -> dict:
    """获取图的信息"""
    try:
        graph = build_graph()
        if hasattr(graph, 'get_graph'):
            graph_view = graph.get_graph(xray=True)
            return {
                "nodes": len(graph_view.nodes) if hasattr(graph_view, 'nodes') else 0,
                "edges": len(graph_view.edges) if hasattr(graph_view, 'edges') else 0,
                "mermaid": graph_view.draw_mermaid() if hasattr(graph_view, 'draw_mermaid') else "graph TD\n    A[Start] --> B[End]"
            }
        else:
            return {
                "nodes": 7,  # 预定义节点数
                "edges": 8,  # 预定义边数
                "mermaid": "graph TD\n    A[Start] --> B[Coordinator] --> C[Triage] --> D[Chat/Research]"
            }
    except Exception as e:
        logger.error(f"获取图信息失败: {e}")
        return {
            "nodes": 0,
            "edges": 0,
            "mermaid": "graph TD\n    A[Error] --> B[Failed to build graph]",
            "error": str(e)
        }


# 创建全局图实例
try:
    graph = build_graph()
    graph_with_memory = build_graph_with_memory()
except Exception as e:
    logger.error(f"创建全局图实例失败: {e}")
    graph = None
    graph_with_memory = None
