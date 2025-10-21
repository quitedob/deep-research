# -*- coding: utf-8 -*-
"""
Research Module for Deep Research Platform
Advanced research orchestration with multi-agent coordination
"""

from .agents import (
    BaseResearchAgent,
    ResearchAgent,
    EvidenceAgent,
    SynthesisAgent,
    AgentCapability,
    AgentTask,
    AgentStatus
)
from .multi_agent_orchestrator import MultiAgentOrchestrator, AgentRole, ExecutionStrategy
from .evidence_chain import (
    EvidenceChainManager,
    EvidenceItem,
    EvidenceChain,
    EvidenceType,
    EvidenceQuality,
    EvidenceStatus,
    EvidenceRelation
)

__all__ = [
    # Agents
    "BaseResearchAgent",
    "ResearchAgent",
    "EvidenceAgent",
    "SynthesisAgent",
    "AgentCapability",
    "AgentTask",
    "AgentStatus",

    # Orchestration
    "MultiAgentOrchestrator",
    "AgentRole",
    "ExecutionStrategy",

    # Evidence Management
    "EvidenceChainManager",
    "EvidenceItem",
    "EvidenceChain",
    "EvidenceType",
    "EvidenceQuality",
    "EvidenceStatus",
    "EvidenceRelation"
]