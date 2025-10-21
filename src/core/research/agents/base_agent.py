# -*- coding: utf-8 -*-
"""
Base Agent for Deep Research Platform
Foundation for all specialized research agents
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass, field

from pydantic import BaseModel, Field


@dataclass
class AgentCapability:
    """Agent capability definition"""
    name: str
    description: str
    enabled: bool = True
    priority: int = 1


@dataclass
class AgentTask:
    """Task assigned to an agent"""
    id: str
    description: str
    task_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AgentStatus(str):
    """Agent status enumeration"""
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"


class BaseResearchAgent(ABC):
    """
    Base class for all specialized research agents
    Provides common functionality for task management, communication, and monitoring
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        capabilities: Optional[List[AgentCapability]] = None,
        max_concurrent_tasks: int = 3,
        timeout: int = 300
    ):
        """
        Initialize base research agent

        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            capabilities: List of agent capabilities
            max_concurrent_tasks: Maximum concurrent tasks
            timeout: Task timeout in seconds
        """
        self.agent_id = agent_id or f"agent_{uuid.uuid4().hex[:8]}"
        self.name = name or f"Agent {self.agent_id}"
        self.capabilities = capabilities or []
        self.max_concurrent_tasks = max_concurrent_tasks
        self.timeout = timeout

        # State management
        self.status = AgentStatus.IDLE
        self.current_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: List[AgentTask] = []
        self.task_queue: List[AgentTask] = []

        # Communication
        self.message_handlers: Dict[str, callable] = {}
        self.event_listeners: Dict[str, List[callable]] = {}

        # Metrics
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.total_processing_time = 0.0
        self.last_activity = datetime.now()

    @abstractmethod
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Process a single task - must be implemented by subclasses

        Args:
            task: Task to process

        Returns:
            Task result
        """
        pass

    @abstractmethod
    def get_agent_type(self) -> str:
        """Get the agent type identifier"""
        pass

    async def assign_task(self, task: AgentTask) -> bool:
        """
        Assign a task to this agent

        Args:
            task: Task to assign

        Returns:
            True if task was accepted, False otherwise
        """
        if len(self.current_tasks) >= self.max_concurrent_tasks:
            self.task_queue.append(task)
            await self._emit_event("task_queued", {"task_id": task.id, "queue_size": len(self.task_queue)})
            return False

        # Check if agent has required capability
        if not self._can_handle_task(task):
            return False

        self.current_tasks[task.id] = task
        task.status = "assigned"
        task.started_at = datetime.now()

        await self._emit_event("task_assigned", {"task_id": task.id, "agent_id": self.agent_id})

        # Start processing asynchronously
        asyncio.create_task(self._process_task_async(task))

        return True

    async def _process_task_async(self, task: AgentTask) -> None:
        """Process task asynchronously with error handling"""
        self.status = AgentStatus.WORKING
        self.last_activity = datetime.now()

        try:
            # Set timeout
            result = await asyncio.wait_for(
                self.process_task(task),
                timeout=self.timeout
            )

            task.result = result
            task.status = "completed"
            task.completed_at = datetime.now()
            self.tasks_completed += 1

            await self._emit_event("task_completed", {
                "task_id": task.id,
                "result": result,
                "processing_time": (task.completed_at - task.started_at).total_seconds()
            })

        except asyncio.TimeoutError:
            task.error = f"Task timed out after {self.timeout} seconds"
            task.status = "failed"
            task.completed_at = datetime.now()
            self.tasks_failed += 1

            await self._emit_event("task_failed", {
                "task_id": task.id,
                "error": task.error
            })

        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            task.completed_at = datetime.now()
            self.tasks_failed += 1

            await self._emit_event("task_failed", {
                "task_id": task.id,
                "error": task.error
            })

        finally:
            # Move task from current to completed
            if task.id in self.current_tasks:
                del self.current_tasks[task.id]
            self.completed_tasks.append(task)

            # Update status
            if not self.current_tasks:
                self.status = AgentStatus.IDLE
                # Process queued tasks
                if self.task_queue:
                    next_task = self.task_queue.pop(0)
                    await self.assign_task(next_task)

            # Update metrics
            if task.started_at and task.completed_at:
                processing_time = (task.completed_at - task.started_at).total_seconds()
                self.total_processing_time += processing_time

    def _can_handle_task(self, task: AgentTask) -> bool:
        """Check if agent can handle the task based on capabilities"""
        if not self.capabilities:
            return True  # No restrictions

        required_capability = task.task_type
        for capability in self.capabilities:
            if capability.name == required_capability and capability.enabled:
                return True

        return False

    async def send_message(self, target_agent_id: str, message: Dict[str, Any]) -> bool:
        """
        Send a message to another agent

        Args:
            target_agent_id: ID of target agent
            message: Message content

        Returns:
            True if message was sent successfully
        """
        # This would be implemented by the orchestrator for inter-agent communication
        await self._emit_event("message_sent", {
            "target_agent_id": target_agent_id,
            "message": message
        })
        return True

    async def receive_message(self, sender_agent_id: str, message: Dict[str, Any]) -> None:
        """
        Receive a message from another agent

        Args:
            sender_agent_id: ID of sender agent
            message: Message content
        """
        message_type = message.get("type", "unknown")

        if message_type in self.message_handlers:
            await self.message_handlers[message_type](sender_agent_id, message)

        await self._emit_event("message_received", {
            "sender_agent_id": sender_agent_id,
            "message": message
        })

    def register_message_handler(self, message_type: str, handler: callable) -> None:
        """Register a handler for specific message types"""
        self.message_handlers[message_type] = handler

    def add_event_listener(self, event_type: str, listener: callable) -> None:
        """Add an event listener"""
        if event_type not in self.event_listeners:
            self.event_listeners[event_type] = []
        self.event_listeners[event_type].append(listener)

    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event to all listeners"""
        if event_type in self.event_listeners:
            for listener in self.event_listeners[event_type]:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(self, event_type, data)
                    else:
                        listener(self, event_type, data)
                except Exception as e:
                    print(f"Error in event listener: {e}")

    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.get_agent_type(),
            "status": self.status,
            "current_tasks": len(self.current_tasks),
            "queued_tasks": len(self.task_queue),
            "completed_tasks": len(self.completed_tasks),
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "success_rate": self.tasks_completed / max(1, self.tasks_completed + self.tasks_failed),
            "average_processing_time": self.total_processing_time / max(1, self.tasks_completed),
            "capabilities": [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "enabled": cap.enabled
                }
                for cap in self.capabilities
            ],
            "last_activity": self.last_activity.isoformat()
        }

    async def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get history of completed tasks"""
        recent_tasks = self.completed_tasks[-limit:] if limit > 0 else self.completed_tasks

        return [
            {
                "task_id": task.id,
                "description": task.description,
                "type": task.task_type,
                "status": task.status,
                "result": task.result,
                "error": task.error,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "processing_time": (
                    (task.completed_at - task.started_at).total_seconds()
                    if task.started_at and task.completed_at else None
                )
            }
            for task in recent_tasks
        ]

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task (if possible)

        Args:
            task_id: ID of task to cancel

        Returns:
            True if task was cancelled
        """
        # Check current tasks
        if task_id in self.current_tasks:
            task = self.current_tasks[task_id]
            task.status = "cancelled"
            task.completed_at = datetime.now()

            del self.current_tasks[task_id]
            self.completed_tasks.append(task)

            await self._emit_event("task_cancelled", {"task_id": task_id})
            return True

        # Check queued tasks
        for i, task in enumerate(self.task_queue):
            if task.id == task_id:
                task.status = "cancelled"
                self.task_queue.pop(i)

                await self._emit_event("task_cancelled", {"task_id": task_id})
                return True

        return False

    async def shutdown(self) -> None:
        """Shutdown the agent gracefully"""
        self.status = AgentStatus.COMPLETED

        # Cancel all current tasks
        for task_id in list(self.current_tasks.keys()):
            await self.cancel_task(task_id)

        # Clear queued tasks
        self.task_queue.clear()

        await self._emit_event("agent_shutdown", {"agent_id": self.agent_id})

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.agent_id}, name={self.name}, status={self.status})"