# -*- coding: utf-8 -*-
"""
Plan Models for Deep Research Platform
Based on AgentScope v1.0.0 plan management system
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PlanStatus(str, Enum):
    """Plan execution status"""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"
    SUSPENDED = "suspended"


class SubTaskStatus(str, Enum):
    """Subtask execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class SubTask(BaseModel):
    """SubTask model for research plan decomposition"""

    id: str = Field(description="Unique identifier for subtask")
    title: str = Field(description="Title of the subtask")
    description: str = Field(description="Detailed description of the subtask")
    status: SubTaskStatus = Field(default=SubTaskStatus.PENDING, description="Current status")
    working_plan: Optional[str] = Field(default=None, description="Detailed working plan for this subtask")
    knowledge_gaps: Optional[str] = Field(default=None, description="Identified knowledge gaps")
    evidence_requirements: List[str] = Field(default_factory=list, description="Required evidence for this subtask")
    assigned_agent: Optional[str] = Field(default=None, description="Agent assigned to this subtask")
    start_time: Optional[datetime] = Field(default=None, description="When subtask started")
    end_time: Optional[datetime] = Field(default=None, description="When subtask completed")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies on other subtasks")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        from_attributes = True


class Plan(BaseModel):
    """Research Plan model"""

    id: str = Field(description="Unique identifier for the plan")
    title: str = Field(description="Title of the research plan")
    description: str = Field(description="Overall description of the research goal")
    status: PlanStatus = Field(default=PlanStatus.CREATED, description="Current plan status")
    subtasks: List[SubTask] = Field(default_factory=list, description="List of subtasks")
    current_subtask_index: int = Field(default=0, description="Index of current active subtask")
    created_at: datetime = Field(default_factory=datetime.now, description="Plan creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
    created_by: str = Field(description="User who created the plan")
    project_id: Optional[str] = Field(default=None, description="Associated research project")
    total_steps: int = Field(description="Total number of steps in the plan")
    completed_steps: int = Field(default=0, description="Number of completed steps")
    progress_percentage: float = Field(default=0.0, description="Progress percentage")
    working_plan_summary: Optional[str] = Field(default=None, description="Summary of the working plan")
    evidence_collected: List[str] = Field(default_factory=list, description="Collected evidence references")
    insights: List[str] = Field(default_factory=list, description="Research insights generated")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional plan metadata")

    class Config:
        from_attributes = True

    def mark_current_step_done(self) -> None:
        """Mark current step as done and move to next"""
        if self.current_subtask_index < len(self.subtasks):
            current_task = self.subtasks[self.current_subtask_index]
            current_task.status = SubTaskStatus.COMPLETED
            current_task.end_time = datetime.now()

            self.completed_steps += 1
            self.progress_percentage = (self.completed_steps / self.total_steps) * 100

            if self.current_subtask_index < len(self.subtasks) - 1:
                self.current_subtask_index += 1
                self.subtasks[self.current_subtask_index].status = SubTaskStatus.IN_PROGRESS
                self.subtasks[self.current_subtask_index].start_time = datetime.now()
            else:
                self.status = PlanStatus.COMPLETED

        self.updated_at = datetime.now()

    def get_current_subtask(self) -> Optional[SubTask]:
        """Get current active subtask"""
        if self.current_subtask_index < len(self.subtasks):
            return self.subtasks[self.current_subtask_index]
        return None

    def add_insight(self, insight: str) -> None:
        """Add research insight to the plan"""
        self.insights.append(insight)
        self.updated_at = datetime.now()

    def add_evidence(self, evidence_ref: str) -> None:
        """Add evidence reference to the plan"""
        self.evidence_collected.append(evidence_ref)
        self.updated_at = datetime.now()


class PlanCreateRequest(BaseModel):
    """Request model for creating a new plan"""

    title: str = Field(description="Title of the research plan")
    description: str = Field(description="Overall description of the research goal")
    research_query: str = Field(description="Main research question or topic")
    user_id: str = Field(description="User creating the plan")
    project_id: Optional[str] = Field(default=None, description="Associated project ID")
    custom_steps: Optional[List[str]] = Field(default=None, description="Custom steps if provided")


class PlanUpdateRequest(BaseModel):
    """Request model for updating a plan"""

    title: Optional[str] = Field(default=None, description="Updated title")
    description: Optional[str] = Field(default=None, description="Updated description")
    status: Optional[PlanStatus] = Field(default=None, description="Updated status")
    subtask_updates: Optional[List[Dict[str, Any]]] = Field(default=None, description="Subtask updates")
    working_plan_summary: Optional[str] = Field(default=None, description="Updated working plan summary")


class SubTaskCreateRequest(BaseModel):
    """Request model for creating a subtask"""

    title: str = Field(description="Title of the subtask")
    description: str = Field(description="Detailed description")
    working_plan: Optional[str] = Field(default=None, description="Working plan details")
    evidence_requirements: List[str] = Field(default_factory=list, description="Required evidence")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies")


class PlanExecutionRequest(BaseModel):
    """Request model for executing a plan step"""

    plan_id: str = Field(description="Plan identifier")
    step_action: str = Field(description="Action to take for current step")
    evidence_collected: List[str] = Field(default_factory=list, description="Evidence collected in this step")
    insights_generated: List[str] = Field(default_factory=list, description="Insights from this step")
    next_step_recommendation: Optional[str] = Field(default=None, description="Recommendation for next step")


class PlanResponse(BaseModel):
    """Response model for plan operations"""

    plan: Plan
    next_actions: List[str] = Field(default_factory=list, description="Recommended next actions")
    progress_summary: str = Field(description="Summary of current progress")
    estimated_completion_time: Optional[str] = Field(default=None, description="Estimated completion time")