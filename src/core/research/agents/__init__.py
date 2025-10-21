# -*- coding: utf-8 -*-
"""
Research Agents Package for Deep Research Platform
Specialized agents for research, evidence collection, and synthesis
"""

from .base_agent import BaseResearchAgent, AgentCapability, AgentTask, AgentStatus
from .research_agent import ResearchAgent
from .evidence_agent import EvidenceAgent
from .synthesis_agent import SynthesisAgent

__all__ = [
    "BaseResearchAgent",
    "AgentCapability",
    "AgentTask",
    "AgentStatus",
    "ResearchAgent",
    "EvidenceAgent",
    "SynthesisAgent"
]