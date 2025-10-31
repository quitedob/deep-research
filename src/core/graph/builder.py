# -*- coding: utf-8 -*-
"""
使用 LangGraph 和 AgentScope v1.0 构建多智能体工作流图。
"""

import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import State
from .nodes import (
    background_investigation_node,
    coordinator_node,
    planner_node,
    reporter_node,
    research_team_node,
    researcher_node,
    coder_node,
    human_feedback_node,
)

logger = logging.getLogger(__name__)


def continue_to_running_research_team(state: State):
    """决定是否继续运行研究团队"""
    current_plan = state.get("current_plan")
    if not current_plan or not current_plan.steps:
        return "planner"
    if all(step.execution_res for step in current_plan.steps):
        return "planner"
    # Find first incomplete step
    incomplete_step = None
    for step in current_plan.steps:
        if not step.execution_res:
            incomplete_step = step
            break
    if not incomplete_step:
        return "planner"
    if incomplete_step.step_type == "research":
        return "researcher"
    if incomplete_step.step_type == "processing":
        return "coder"
    return "planner"


def _build_base_graph():
    """构建并返回基础状态图"""
    builder = StateGraph(State)
    builder.add_edge("START", "coordinator")
    builder.add_node("coordinator", coordinator_node)
    builder.add_node("background_investigator", background_investigation_node)
    builder.add_node("planner", planner_node)
    builder.add_node("reporter", reporter_node)
    builder.add_node("research_team", research_team_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("coder", coder_node)
    builder.add_node("human_feedback", human_feedback_node)

    builder.add_edge("background_investigator", "planner")
    builder.add_conditional_edges(
        "research_team",
        continue_to_running_research_team,
        ["planner", "researcher", "coder"],
    )
    builder.add_edge("reporter", "END")
    return builder


def build_graph_with_memory():
    """构建并返回带有记忆的工作流图"""
    memory = MemorySaver()
    builder = _build_base_graph()
    return builder.compile(checkpointer=memory)


def build_graph():
    """构建并返回不带记忆的工作流图"""
    builder = _build_base_graph()
    return builder.compile()


# 创建全局图实例（带记忆）
agent_graph = build_graph_with_memory()
