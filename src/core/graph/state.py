# -*- coding: utf-8 -*-
"""
定义多智能体工作流的共享状态 - 基于 AgentScope v1.0
"""

from dataclasses import field
from langgraph.graph import MessagesState
from typing import List, Optional
from src.prompts.planner_model import Plan
from src.rag import Resource


class State(MessagesState):
    """State for the agent system, extends MessagesState with additional fields."""

    # Runtime Variables
    locale: str = "en-US"
    research_topic: str = ""
    clarified_research_topic: str = ""  # Complete/final clarified topic with all clarification rounds
    observations: list[str] = []
    resources: list[Resource] = []
    plan_iterations: int = 0
    current_plan: Plan | str = None
    final_report: str = ""
    auto_accepted_plan: bool = False
    enable_background_investigation: bool = True
    background_investigation_results: str = None

    # Clarification state tracking (disabled by default)
    enable_clarification: bool = False  # Enable/disable clarification feature (default: False)
    clarification_rounds: int = 0
    clarification_history: list[str] = field(default_factory=list)
    is_clarification_complete: bool = False
    max_clarification_rounds: int = 3  # Default: 3 rounds (only used when enable_clarification=True)

    # Workflow control
    goto: str = "planner"  # Default next node
