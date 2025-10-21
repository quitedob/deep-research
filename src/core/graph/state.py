# -*- coding: utf-8 -*-
"""
定义多智能体工作流的共享状态。
"""

from typing import List, Optional, TypedDict, Dict, Any


class GraphState(TypedDict):
    """
    定义图的共享状态。每个键都是一个通道，节点可以从中读取或向其写入。
    """
    # 输入
    original_query: str

    # 计划
    research_plan: Optional[List[Dict[str, Any]]]

    # 智能体产出
    retrieved_documents: Optional[List[Dict[str, Any]]]
    analysis_results: Optional[Dict[str, Any]]
    draft_report: Optional[str]

    # 工作流控制
    next_action: str
    error_log: List[str]
    iteration_count: int

    # 人在环路 (HITL)
    human_review_required: bool
    feedback_request: Optional[str]
    user_feedback: Optional[str]
