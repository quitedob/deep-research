# -*- coding: utf-8 -*-
"""
Multi-Agent Research Orchestrator for Deep Research Platform
Coordinates multiple specialized agents for collaborative research
"""

import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from ..plan.plan_notebook import PlanNotebook
from ..plan.plan import Plan, SubTask, SubTaskStatus
from .research_agent import ResearchAgent, EvidenceAgent, SynthesisAgent
from .evidence_chain import EvidenceChain


class AgentRole(str, Enum):
    """Agent roles in research orchestration"""
    RESEARCHER = "researcher"
    EVIDENCE_COLLECTOR = "evidence_collector"
    SYNTHESIZER = "synthesizer"
    COORDINATOR = "coordinator"


class OrchestratorStatus(str, Enum):
    """Orchestrator status"""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentTask:
    """Task assigned to an agent"""
    id: str
    agent_id: str
    role: AgentRole
    subtask_id: str
    description: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class MultiAgentOrchestrator:
    """
    Orchestrates multiple specialized agents for collaborative research
    """

    def __init__(
        self,
        max_concurrent_agents: int = 3,
        coordination_strategy: str = "sequential"
    ):
        """
        Initialize the multi-agent orchestrator

        Args:
            max_concurrent_agents: Maximum number of agents running concurrently
            coordination_strategy: Strategy for agent coordination ("sequential", "parallel", "adaptive")
        """
        self.max_concurrent_agents = max_concurrent_agents
        self.coordination_strategy = coordination_strategy
        self.status = OrchestratorStatus.IDLE

        # Agent registry
        self.agents: Dict[str, ResearchAgent] = {}
        self.agent_tasks: Dict[str, AgentTask] = {}

        # Research components
        self.plan_notebook: Optional[PlanNotebook] = None
        self.evidence_chain: Optional[EvidenceChain] = None
        self.current_plan: Optional[Plan] = None

        # Orchestration state
        self.execution_history: List[Dict[str, Any]] = []
        self.active_tasks: List[str] = []
        self.completed_tasks: List[str] = []

        # Event hooks
        self.status_change_hooks: List[Callable] = []
        self.task_completion_hooks: List[Callable] = []

    def register_agent(
        self,
        agent_id: str,
        agent: ResearchAgent,
        role: AgentRole
    ) -> None:
        """Register an agent with the orchestrator"""
        self.agents[agent_id] = agent
        # Agent role is stored in the agent itself
        agent.role = role

    async def start_research(
        self,
        research_query: str,
        user_id: str,
        project_id: Optional[str] = None,
        plan_notebook: Optional[PlanNotebook] = None
    ) -> Dict[str, Any]:
        """
        Start a multi-agent research project

        Args:
            research_query: Main research question
            user_id: User requesting the research
            project_id: Associated project ID
            plan_notebook: Plan notebook instance

        Returns:
            Research initiation response
        """
        try:
            self.status = OrchestratorStatus.PLANNING
            await self._notify_status_change()

            # Use provided plan notebook or create default
            self.plan_notebook = plan_notebook or PlanNotebook()
            self.plan_notebook.set_user_id(user_id)

            # Create research plan
            plan = await self.plan_notebook.create_plan(
                title=f"Multi-Agent Research: {research_query}",
                description=f"Collaborative research on: {research_query}",
                research_query=research_query,
                user_id=user_id,
                project_id=project_id
            )

            self.current_plan = plan
            self.evidence_chain = EvidenceChain(plan.id)

            # Start orchestration
            orchestration_result = await self._execute_orchestration()

            self.status = OrchestratorStatus.COMPLETED
            await self._notify_status_change()

            return orchestration_result

        except Exception as e:
            self.status = OrchestratorStatus.FAILED
            await self._notify_status_change()
            return {
                "success": False,
                "error": str(e),
                "orchestration_id": self._get_orchestration_id()
            }

    async def _execute_orchestration(self) -> Dict[str, Any]:
        """Execute the multi-agent orchestration"""
        self.status = OrchestratorStatus.EXECUTING
        await self._notify_status_change()

        orchestration_id = self._get_orchestration_id()
        results = []

        try:
            # Execute based on coordination strategy
            if self.coordination_strategy == "sequential":
                results = await self._execute_sequential()
            elif self.coordination_strategy == "parallel":
                results = await self._execute_parallel()
            elif self.coordination_strategy == "adaptive":
                results = await self._execute_adaptive()
            else:
                results = await self._execute_sequential()

            # Synthesize results
            synthesis_result = await self._synthesize_results(results)

            return {
                "success": True,
                "orchestration_id": orchestration_id,
                "plan_id": self.current_plan.id,
                "results": results,
                "synthesis": synthesis_result,
                "evidence_count": len(self.evidence_chain.evidence_items) if self.evidence_chain else 0,
                "execution_time": self._calculate_execution_time()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "orchestration_id": orchestration_id,
                "partial_results": results
            }

    async def _execute_sequential(self) -> List[Dict[str, Any]]:
        """Execute research tasks sequentially"""
        results = []

        for subtask in self.current_plan.subtasks:
            if subtask.status in [SubTaskStatus.COMPLETED, SubTaskStatus.FAILED]:
                continue

            # Assign task to appropriate agent
            task = await self._assign_task_to_agent(subtask)
            if not task:
                continue

            # Execute task
            result = await self._execute_agent_task(task)
            results.append(result)

            # Update plan with results
            await self._update_plan_with_task_result(task, result)

            # Check if plan is complete
            if self._is_plan_complete():
                break

        return results

    async def _execute_parallel(self) -> List[Dict[str, Any]]:
        """Execute research tasks in parallel where possible"""
        results = []

        # Group tasks by dependencies
        task_groups = self._group_tasks_by_dependencies()

        for group in task_groups:
            # Execute tasks in current group in parallel
            group_results = await asyncio.gather(
                *[self._execute_task_in_group(task) for task in group],
                return_exceptions=True
            )

            for result in group_results:
                if isinstance(result, Exception):
                    results.append({
                        "success": False,
                        "error": str(result)
                    })
                else:
                    results.append(result)
                    await self._update_plan_with_task_result(result["task"], result)

        return results

    async def _execute_adaptive(self) -> List[Dict[str, Any]]:
        """Execute research tasks with adaptive strategy"""
        # Start with sequential execution for initial tasks
        initial_tasks = self.current_plan.subtasks[:2]
        results = []

        for subtask in initial_tasks:
            if subtask.status in [SubTaskStatus.COMPLETED, SubTaskStatus.FAILED]:
                continue

            task = await self._assign_task_to_agent(subtask)
            if task:
                result = await self._execute_agent_task(task)
                results.append(result)
                await self._update_plan_with_task_result(task, result)

        # Evaluate progress and decide on remaining strategy
        progress = self._calculate_progress()
        if progress > 50:
            # Good progress, switch to parallel for remaining tasks
            remaining_tasks = [t for t in self.current_plan.subtasks if t.status == SubTaskStatus.PENDING]
            if remaining_tasks:
                parallel_results = await self._execute_remaining_tasks_parallel(remaining_tasks)
                results.extend(parallel_results)
        else:
            # Slow progress, continue with sequential
            remaining_tasks = [t for t in self.current_plan.subtasks if t.status == SubTaskStatus.PENDING]
            for subtask in remaining_tasks:
                task = await self._assign_task_to_agent(subtask)
                if task:
                    result = await self._execute_agent_task(task)
                    results.append(result)
                    await self._update_plan_with_task_result(task, result)

        return results

    async def _assign_task_to_agent(self, subtask: SubTask) -> Optional[AgentTask]:
        """Assign a subtask to an appropriate agent"""
        # Find best agent for the task
        best_agent = self._find_best_agent(subtask)
        if not best_agent:
            return None

        # Create task
        task = AgentTask(
            id=f"task_{uuid.uuid4().hex[:8]}",
            agent_id=best_agent["id"],
            role=best_agent["role"],
            subtask_id=subtask.id,
            description=subtask.description,
            status="pending"
        )

        self.agent_tasks[task.id] = task
        self.active_tasks.append(task.id)

        return task

    def _find_best_agent(self, subtask: SubTask) -> Optional[Dict[str, Any]]:
        """Find the best agent for a given subtask"""
        available_agents = [
            {"id": agent_id, "agent": agent, "role": getattr(agent, 'role', AgentRole.RESEARCHER)}
            for agent_id, agent in self.agents.items()
        ]

        if not available_agents:
            return None

        # Score agents based on task requirements
        scored_agents = []
        for agent_info in available_agents:
            score = self._score_agent_for_task(agent_info, subtask)
            scored_agents.append({"score": score, **agent_info})

        # Return highest scoring agent
        scored_agents.sort(key=lambda x: x["score"], reverse=True)
        return scored_agents[0] if scored_agents else None

    def _score_agent_for_task(self, agent_info: Dict[str, Any], subtask: SubTask) -> float:
        """Score an agent for a specific task"""
        agent = agent_info["agent"]
        role = agent_info["role"]

        # Base score
        score = 0.5

        # Role-based scoring
        if "evidence" in subtask.description.lower() or "collect" in subtask.description.lower():
            if role == AgentRole.EVIDENCE_COLLECTOR:
                score += 2.0
            elif role == AgentRole.RESEARCHER:
                score += 1.0

        if "analyze" in subtask.description.lower() or "research" in subtask.description.lower():
            if role == AgentRole.RESEARCHER:
                score += 2.0
            elif role == AgentRole.EVIDENCE_COLLECTOR:
                score += 1.0

        if "synthesize" in subtask.description.lower() or "summarize" in subtask.description.lower():
            if role == AgentRole.SYNTHESIZER:
                score += 2.0
            elif role == AgentRole.RESEARCHER:
                score += 1.0

        # Agent capability scoring
        if hasattr(agent, 'get_capabilities'):
            capabilities = agent.get_capabilities()
            if "evidence_collection" in capabilities:
                score += 0.5
            if "analysis" in capabilities:
                score += 0.5
            if "synthesis" in capabilities:
                score += 0.5

        return score

    async def _execute_agent_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a task assigned to an agent"""
        task.status = "executing"
        task.start_time = datetime.now()

        try:
            agent = self.agents[task.agent_id]
            subtask = self.current_plan.get_subtask_by_id(task.subtask_id)

            if not subtask:
                raise ValueError(f"Subtask {task.subtask_id} not found")

            # Execute the task
            result = await agent.execute_task(
                task_description=task.description,
                subtask=subtask,
                context={
                    "plan_id": self.current_plan.id,
                    "evidence_chain": self.evidence_chain,
                    "previous_findings": self._get_previous_findings()
                }
            )

            task.status = "completed"
            task.end_time = datetime.now()
            task.result = result

            # Move task from active to completed
            if task.id in self.active_tasks:
                self.active_tasks.remove(task.id)
            self.completed_tasks.append(task.id)

            # Notify task completion
            await self._notify_task_completion(task, result)

            return {
                "success": True,
                "task": task,
                "result": result,
                "execution_time": (task.end_time - task.start_time).total_seconds()
            }

        except Exception as e:
            task.status = "failed"
            task.end_time = datetime.now()
            task.result = {"error": str(e)}

            if task.id in self.active_tasks:
                self.active_tasks.remove(task.id)
            self.completed_tasks.append(task.id)

            return {
                "success": False,
                "task": task,
                "error": str(e),
                "execution_time": (task.end_time - task.start_time).total_seconds()
            }

    async def _update_plan_with_task_result(self, task: AgentTask, result: Dict[str, Any]) -> None:
        """Update the research plan with task results"""
        if not result.get("success"):
            return

        subtask = self.current_plan.get_subtask_by_id(task.subtask_id)
        if not subtask:
            return

        # Update subtask with findings
        if "findings" in result:
            for finding in result["findings"]:
                self.current_plan.add_insight(f"Agent {task.role}: {finding}")

        if "evidence" in result:
            for evidence in result["evidence"]:
                self.current_plan.add_evidence(evidence)
                if self.evidence_chain:
                    await self.evidence_chain.add_evidence(evidence, task.role)

        # Mark subtask as completed
        subtask.status = SubTaskStatus.COMPLETED
        subtask.end_time = datetime.now()

        # Update plan
        await self.plan_notebook.storage.update_plan(
            self.current_plan.id,
            self.current_plan.model_dump()
        )

    def _group_tasks_by_dependencies(self) -> List[List[SubTask]]:
        """Group tasks by their dependencies"""
        ungrouped = [t for t in self.current_plan.subtasks if t.status == SubTaskStatus.PENDING]
        groups = []

        while ungrouped:
            # Find tasks with no pending dependencies
            current_group = []
            remaining_tasks = []

            for task in ungrouped:
                if all(dep not in [t.id for t in ungrouped] for dep in task.dependencies):
                    current_group.append(task)
                else:
                    remaining_tasks.append(task)

            groups.append(current_group)
            ungrouped = remaining_tasks

        return groups

    async def _execute_remaining_tasks_parallel(self, remaining_tasks: List[SubTask]) -> List[Dict[str, Any]]:
        """Execute remaining tasks in parallel"""
        task_results = []

        # Create tasks for parallel execution
        tasks = []
        for subtask in remaining_tasks:
            task = await self._assign_task_to_agent(subtask)
            if task:
                tasks.append(task)

        # Execute tasks in parallel
        if tasks:
            results = await asyncio.gather(
                *[self._execute_agent_task(task) for task in tasks],
                return_exceptions=True
            )

            for result in results:
                if isinstance(result, Exception):
                    task_results.append({
                        "success": False,
                        "error": str(result)
                    })
                else:
                    task_results.append(result)

        return task_results

    async def _synthesize_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesize results from all agents"""
        self.status = OrchestratorStatus.SYNTHESIZING
        await self._notify_status_change()

        successful_results = [r for r in results if r.get("success")]

        if not successful_results:
            return {"error": "No successful results to synthesize"}

        # Use synthesis agent if available
        synthesis_agent = None
        for agent in self.agents.values():
            if hasattr(agent, 'role') and agent.role == AgentRole.SYNTHESIZER:
                synthesis_agent = agent
                break

        if synthesis_agent:
            try:
                synthesis = await synthesis_agent.synthesize_results(
                    results=successful_results,
                    plan=self.current_plan,
                    evidence_chain=self.evidence_chain
                )
                return {"synthesis": synthesis, "method": "agent_synthesis"}
            except Exception as e:
                return {"error": f"Agent synthesis failed: {e}"}

        # Fallback to basic synthesis
        return self._basic_synthesis(successful_results)

    def _basic_synthesis(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Basic synthesis method when no synthesis agent is available"""
        all_insights = []
        all_evidence = []

        for result in results:
            if "result" in result and "findings" in result["result"]:
                all_insights.extend(result["result"]["findings"])
            if "result" in result and "evidence" in result["result"]:
                all_evidence.extend(result["result"]["evidence"])

        return {
            "summary": f"Completed {len(results)} research tasks with {len(all_insights)} insights and {len(all_evidence)} evidence items",
            "insights": all_insights,
            "evidence_count": len(all_evidence),
            "method": "basic_synthesis"
        }

    def _is_plan_complete(self) -> bool:
        """Check if the research plan is complete"""
        if not self.current_plan:
            return True

        completed_subtasks = sum(
            1 for subtask in self.current_plan.subtasks
            if subtask.status == SubTaskStatus.COMPLETED
        )

        return completed_subtasks >= len(self.current_plan.subtasks)

    def _calculate_progress(self) -> float:
        """Calculate overall research progress"""
        if not self.current_plan:
            return 0.0

        return self.current_plan.progress_percentage

    def _calculate_execution_time(self) -> float:
        """Calculate total execution time"""
        if not self.execution_history:
            return 0.0

        start_time = min(entry["timestamp"] for entry in self.execution_history)
        end_time = max(entry["timestamp"] for entry in self.execution_history)

        return (end_time - start_time).total_seconds()

    def _get_previous_findings(self) -> List[str]:
        """Get findings from previous tasks"""
        return self.current_plan.insights if self.current_plan else []

    def _get_orchestration_id(self) -> str:
        """Generate orchestration ID"""
        return f"orch_{uuid.uuid4().hex[:8]}"

    def register_status_change_hook(self, hook: Callable) -> None:
        """Register a status change hook"""
        self.status_change_hooks.append(hook)

    def register_task_completion_hook(self, hook: Callable) -> None:
        """Register a task completion hook"""
        self.task_completion_hooks.append(hook)

    async def _notify_status_change(self) -> None:
        """Notify all status change hooks"""
        for hook in self.status_change_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(self, self.status)
                else:
                    hook(self, self.status)
            except Exception as e:
                print(f"Error in status change hook: {e}")

    async def _notify_task_completion(self, task: AgentTask, result: Dict[str, Any]) -> None:
        """Notify all task completion hooks"""
        for hook in self.task_completion_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(self, task, result)
                else:
                    hook(self, task, result)
            except Exception as e:
                print(f"Error in task completion hook: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status"""
        return {
            "status": self.status,
            "current_plan_id": self.current_plan.id if self.current_plan else None,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "registered_agents": len(self.agents),
            "progress_percentage": self._calculate_progress(),
            "evidence_count": len(self.evidence_chain.evidence_items) if self.evidence_chain else 0
        }