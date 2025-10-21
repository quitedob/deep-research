# -*- coding: utf-8 -*-
"""
PlanNotebook for Deep Research Platform
Based on AgentScope v1.0.0 PlanNotebook with research-specific enhancements
"""

import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from .plan import Plan, SubTask, PlanStatus, SubTaskStatus, PlanCreateRequest, PlanExecutionRequest
from .storage import PlanStorageBase, MemoryPlanStorage
from .planner import ResearchPlanner


class PlanNotebook:
    """
    PlanNotebook manages research plans and provides tool functions for plan management.
    Integrates with ReAct agents for automated research planning and execution.
    """

    def __init__(
        self,
        storage: Optional[PlanStorageBase] = None,
        max_subtasks: Optional[int] = 10,
        plan_to_hint: Optional[Callable] = None
    ):
        """
        Initialize PlanNotebook

        Args:
            storage: Plan storage implementation (defaults to MemoryPlanStorage)
            max_subtasks: Maximum number of subtasks allowed in a plan
            plan_to_hint: Function to generate hint messages from current plan
        """
        self.storage = storage or MemoryPlanStorage()
        self.max_subtasks = max_subtasks
        self.plan_to_hint = plan_to_hint or self._default_plan_to_hint
        self.current_plan: Optional[Plan] = None
        self.plan_change_hooks: List[Callable] = []
        self.planner = ResearchPlanner()

    def list_tools(self) -> List[Dict[str, Any]]:
        """List available plan management tool functions"""
        return [
            {
                "name": "create_plan",
                "description": "Create a new research plan with specified topic and description",
                "parameters": {
                    "title": "string - Title of the research plan",
                    "description": "string - Detailed description of research goals",
                    "research_query": "string - Main research question or topic"
                }
            },
            {
                "name": "revise_current_plan",
                "description": "Revise the current research plan based on new insights",
                "parameters": {
                    "revision_reason": "string - Reason for revising the plan",
                    "new_steps": "array - New steps to add or modify (optional)"
                }
            },
            {
                "name": "finish_plan",
                "description": "Mark the current research plan as completed",
                "parameters": {
                    "summary": "string - Summary of research findings",
                    "final_insights": "array - Key insights from the research"
                }
            },
            {
                "name": "view_current_plan",
                "description": "View the current research plan and its status",
                "parameters": {}
            },
            {
                "name": "view_historical_plans",
                "description": "View previously completed research plans",
                "parameters": {
                    "limit": "integer - Maximum number of plans to show (default: 5)"
                }
            },
            {
                "name": "recover_historical_plan",
                "description": "Recover and continue a previously completed plan",
                "parameters": {
                    "plan_id": "string - ID of the plan to recover"
                }
            },
            {
                "name": "execute_plan_step",
                "description": "Execute the current step in the research plan",
                "parameters": {
                    "action_taken": "string - Action performed for this step",
                    "evidence_collected": "array - Evidence gathered in this step",
                    "insights": "array - Insights from this step"
                }
            },
            {
                "name": "update_subtask_status",
                "description": "Update the status of the current subtask",
                "parameters": {
                    "status": "string - New status (pending/in_progress/completed/failed)",
                    "notes": "string - Notes about the status update (optional)"
                }
            },
            {
                "name": "add_plan_insight",
                "description": "Add a research insight to the current plan",
                "parameters": {
                    "insight": "string - Research insight to add"
                }
            },
            {
                "name": "add_plan_evidence",
                "description": "Add evidence reference to the current plan",
                "parameters": {
                    "evidence_reference": "string - Reference or description of evidence"
                }
            }
        ]

    async def create_plan(
        self,
        title: str,
        description: str,
        research_query: str,
        user_id: str,
        project_id: Optional[str] = None,
        custom_steps: Optional[List[str]] = None
    ) -> Plan:
        """
        Create a new research plan

        Args:
            title: Plan title
            description: Plan description
            research_query: Main research question
            user_id: User creating the plan
            project_id: Associated project ID
            custom_steps: Custom steps if provided

        Returns:
            Created plan
        """
        if self.current_plan and self.current_plan.status == PlanStatus.IN_PROGRESS:
            raise ValueError("Cannot create new plan while current plan is in progress")

        # Generate plan steps
        if custom_steps:
            steps = custom_steps
        else:
            steps = await self.planner.generate_research_steps(research_query, max_steps=self.max_subtasks)

        if len(steps) > self.max_subtasks:
            steps = steps[:self.max_subtasks]

        # Create subtasks
        subtasks = []
        for i, step in enumerate(steps):
            subtask = SubTask(
                id=f"subtask_{uuid.uuid4().hex[:8]}",
                title=f"Step {i+1}: {step}",
                description=f"Execute research step: {step}",
                status=SubTaskStatus.PENDING,
                dependencies=[subtasks[-1].id] if subtasks else []
            )
            subtasks.append(subtask)

        # Create plan
        plan = Plan(
            id=f"plan_{uuid.uuid4().hex[:8]}",
            title=title,
            description=description,
            subtasks=subtasks,
            total_steps=len(subtasks),
            created_by=user_id,
            project_id=project_id,
            working_plan_summary=description,
            status=PlanStatus.CREATED
        )

        # Save plan
        await self.storage.save_plan(plan)
        self.current_plan = plan

        # Notify hooks
        await self._notify_plan_change(plan)

        return plan

    async def revise_current_plan(
        self,
        revision_reason: str,
        new_steps: Optional[List[str]] = None
    ) -> Plan:
        """Revise the current research plan"""
        if not self.current_plan:
            raise ValueError("No current plan to revise")

        if self.current_plan.status in [PlanStatus.COMPLETED, PlanStatus.FAILED]:
            raise ValueError("Cannot revise completed or failed plan")

        # Add revision reason as insight
        self.current_plan.add_insight(f"Plan revision: {revision_reason}")

        # Add new steps if provided
        if new_steps:
            for step in new_steps:
                subtask = SubTask(
                    id=f"subtask_{uuid.uuid4().hex[:8]}",
                    title=f"Additional Step: {step}",
                    description=f"Execute additional research: {step}",
                    status=SubTaskStatus.PENDING,
                    dependencies=[
                        self.current_plan.subtasks[-1].id
                    ] if self.current_plan.subtasks else []
                )
                self.current_plan.subtasks.append(subtask)

            self.current_plan.total_steps = len(self.current_plan.subtasks)

        # Update plan
        self.current_plan.updated_at = datetime.now()
        await self.storage.update_plan(self.current_plan.id, self.current_plan.model_dump())

        # Notify hooks
        await self._notify_plan_change(self.current_plan)

        return self.current_plan

    async def finish_plan(
        self,
        summary: str,
        final_insights: List[str]
    ) -> Plan:
        """Finish the current research plan"""
        if not self.current_plan:
            raise ValueError("No current plan to finish")

        self.current_plan.status = PlanStatus.COMPLETED
        self.current_plan.add_insight(f"Research Summary: {summary}")

        for insight in final_insights:
            self.current_plan.add_insight(f"Final Insight: {insight}")

        # Mark remaining tasks as completed
        for subtask in self.current_plan.subtasks:
            if subtask.status in [SubTaskStatus.PENDING, SubTaskStatus.IN_PROGRESS]:
                subtask.status = SubTaskStatus.COMPLETED
                subtask.end_time = datetime.now()

        self.current_plan.completed_steps = self.current_plan.total_steps
        self.current_plan.progress_percentage = 100.0

        # Save plan
        await self.storage.update_plan(self.current_plan.id, self.current_plan.model_dump())

        # Notify hooks
        await self._notify_plan_change(self.current_plan)

        return self.current_plan

    async def view_current_plan(self) -> Dict[str, Any]:
        """View the current research plan"""
        if not self.current_plan:
            return {"error": "No current plan"}

        current_subtask = self.current_plan.get_current_subtask()

        return {
            "plan_id": self.current_plan.id,
            "title": self.current_plan.title,
            "description": self.current_plan.description,
            "status": self.current_plan.status,
            "progress": f"{self.current_plan.progress_percentage:.1f}%",
            "completed_steps": self.current_plan.completed_steps,
            "total_steps": self.current_plan.total_steps,
            "current_subtask": {
                "id": current_subtask.id,
                "title": current_subtask.title,
                "status": current_subtask.status,
                "working_plan": current_subtask.working_plan
            } if current_subtask else None,
            "insights_count": len(self.current_plan.insights),
            "evidence_count": len(self.current_plan.evidence_collected)
        }

    async def view_historical_plans(self, limit: int = 5) -> List[Dict[str, Any]]:
        """View historical research plans"""
        if not hasattr(self, '_user_id'):
            return []

        plans = await self.storage.get_historical_plans(self._user_id, limit)

        return [
            {
                "plan_id": plan.id,
                "title": plan.title,
                "description": plan.description[:100] + "..." if len(plan.description) > 100 else plan.description,
                "status": plan.status,
                "completed_at": plan.updated_at,
                "total_steps": plan.total_steps,
                "insights_count": len(plan.insights)
            }
            for plan in plans
        ]

    async def recover_historical_plan(self, plan_id: str) -> Plan:
        """Recover a historical plan"""
        plan = await self.storage.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        if plan.status != PlanStatus.COMPLETED:
            raise ValueError(f"Plan {plan_id} is not completed")

        # Create a new plan based on the historical one
        new_plan = Plan(
            id=f"plan_{uuid.uuid4().hex[:8]}",
            title=f"Revised: {plan.title}",
            description=plan.description,
            subtasks=[
                SubTask(
                    id=f"subtask_{uuid.uuid4().hex[:8]}",
                    title=f"Review previous findings: {step.title}",
                    description=f"Review and build upon previous research: {step.description}",
                    status=SubTaskStatus.PENDING
                )
                for step in plan.subtasks
            ],
            total_steps=len(plan.subtasks),
            created_by=plan.created_by,
            project_id=plan.project_id,
            working_plan_summary=f"Revised plan based on previous research: {plan.insights[-1] if plan.insights else 'No previous insights'}",
            status=PlanStatus.CREATED
        )

        # Save new plan
        await self.storage.save_plan(new_plan)
        self.current_plan = new_plan

        # Notify hooks
        await self._notify_plan_change(new_plan)

        return new_plan

    async def execute_plan_step(
        self,
        action_taken: str,
        evidence_collected: List[str],
        insights: List[str]
    ) -> Dict[str, Any]:
        """Execute the current step in the research plan"""
        if not self.current_plan:
            return {"error": "No current plan"}

        current_subtask = self.current_plan.get_current_subtask()
        if not current_subtask:
            return {"error": "No current subtask"}

        # Update subtask with action and evidence
        current_subtask.working_plan = f"Action taken: {action_taken}"

        # Add evidence and insights to plan
        for evidence in evidence_collected:
            self.current_plan.add_evidence(evidence)

        for insight in insights:
            self.current_plan.add_insight(insight)

        # Mark current step as done
        self.current_plan.mark_current_step_done()

        # Save plan
        await self.storage.update_plan(self.current_plan.id, self.current_plan.model_dump())

        # Notify hooks
        await self._notify_plan_change(self.current_plan)

        return {
            "step_completed": True,
            "next_subtask": {
                "id": self.current_plan.get_current_subtask().id,
                "title": self.current_plan.get_current_subtask().title
            } if self.current_plan.get_current_subtask() else None,
            "progress": f"{self.current_plan.progress_percentage:.1f}%"
        }

    async def update_subtask_status(
        self,
        status: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update the status of the current subtask"""
        if not self.current_plan:
            return {"error": "No current plan"}

        current_subtask = self.current_plan.get_current_subtask()
        if not current_subtask:
            return {"error": "No current subtask"}

        # Update status
        try:
            new_status = SubTaskStatus(status)
            current_subtask.status = new_status

            if notes:
                current_subtask.working_plan = f"{current_subtask.working_plan or ''}\nUpdate: {notes}"

            # Save plan
            await self.storage.update_plan(self.current_plan.id, self.current_plan.model_dump())

            return {
                "subtask_id": current_subtask.id,
                "status": new_status,
                "notes": notes
            }
        except ValueError:
            return {"error": f"Invalid status: {status}"}

    async def add_plan_insight(self, insight: str) -> Dict[str, Any]:
        """Add a research insight to the current plan"""
        if not self.current_plan:
            return {"error": "No current plan"}

        self.current_plan.add_insight(insight)
        await self.storage.update_plan(self.current_plan.id, self.current_plan.model_dump())

        return {
            "insight_added": True,
            "total_insights": len(self.current_plan.insights)
        }

    async def add_plan_evidence(self, evidence_reference: str) -> Dict[str, Any]:
        """Add evidence reference to the current plan"""
        if not self.current_plan:
            return {"error": "No current plan"}

        self.current_plan.add_evidence(evidence_reference)
        await self.storage.update_plan(self.current_plan.id, self.current_plan.model_dump())

        return {
            "evidence_added": True,
            "total_evidence": len(self.current_plan.evidence_collected)
        }

    async def get_current_hint(self) -> str:
        """Get the hint message for the current plan"""
        if not self.current_plan:
            return "No current plan. Use create_plan to start a new research project."

        return await self.plan_to_hint(self.current_plan)

    def register_plan_change_hook(self, hook_func: Callable) -> None:
        """Register a hook function that will be called when the plan changes"""
        self.plan_change_hooks.append(hook_func)

    def remove_plan_change_hook(self, hook_func: Callable) -> None:
        """Remove a registered plan change hook function"""
        if hook_func in self.plan_change_hooks:
            self.plan_change_hooks.remove(hook_func)

    async def _notify_plan_change(self, plan: Plan) -> None:
        """Notify all registered hooks about plan changes"""
        for hook in self.plan_change_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(self, plan)
                else:
                    hook(self, plan)
            except Exception as e:
                print(f"Error in plan change hook: {e}")

    async def _default_plan_to_hint(self, plan: Plan) -> str:
        """Default implementation for generating hint messages from plan"""
        current_subtask = plan.get_current_subtask()

        hint = f"""Current Research Plan: {plan.title}
Status: {plan.status}
Progress: {plan.completed_steps}/{plan.total_steps} steps completed ({plan.progress_percentage:.1f}%)
"""

        if current_subtask:
            hint += f"""
Current Step: {current_subtask.title}
Description: {current_subtask.description}
Status: {current_subtask.status}
"""
            if current_subtask.working_plan:
                hint += f"Working Plan: {current_subtask.working_plan}\n"

        if plan.insights:
            hint += f"\nRecent Insights:\n"
            for insight in plan.insights[-3:]:  # Show last 3 insights
                hint += f"- {insight}\n"

        if plan.evidence_collected:
            hint += f"\nEvidence Collected: {len(plan.evidence_collected)} items\n"

        return hint

    def set_user_id(self, user_id: str) -> None:
        """Set the user ID for the notebook (used for historical plans)"""
        self._user_id = user_id