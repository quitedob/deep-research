# -*- coding: utf-8 -*-
"""
使用 LangGraph 构建多智能体工作流图。
"""

import logging
from langgraph.graph import StateGraph, END
from .state import GraphState
from .agents import supervisor_node, researcher_node, writer_node

logger = logging.getLogger(__name__)


def build_agent_graph():
    """
    构建并编译多智能体工作流图。
    """
    workflow = StateGraph(GraphState)

    # 添加节点
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("writer", writer_node)

    # 定义边的连接关系
    workflow.set_entry_point("supervisor")

    # 条件路由
    def route_action(state):
        next_action = state.get("next_action")
        if next_action == "finish" or not next_action:
            return END
        return next_action

    workflow.add_conditional_edges(
        "supervisor",
        route_action,
        {
            "researcher": "researcher",
            "writer": "writer",
        }
    )

    # 工作者节点完成后返回给主管
    workflow.add_edge("researcher", "supervisor")
    workflow.add_edge("writer", "supervisor")

    # 编译图
    app = workflow.compile()
    return app


# 创建全局图实例
agent_graph = build_agent_graph()
