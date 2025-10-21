# -*- coding: utf-8 -*-
"""
Multi-Agent Orchestrator API Endpoints for Deep Research Platform
Handles agent orchestration, task management, and monitoring API calls
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import asyncio
import logging

from ..core.research.multi_agent_orchestrator import MultiAgentOrchestrator, AgentRole, ExecutionStrategy
from ..core.research.agents import ResearchAgent, EvidenceAgent, SynthesisAgent
from ..core.database import get_db
from ..core.security import get_current_user

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])

# Global orchestrator instance
_orchestrator = None
_connected_clients = set()

logger = logging.getLogger(__name__)

async def get_orchestrator():
    """Get or initialize the global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiAgentOrchestrator(
            max_concurrent_agents=3,
            coordination_strategy="adaptive"
        )

        # Register default agents
        research_agent = ResearchAgent()
        evidence_agent = EvidenceAgent()
        synthesis_agent = SynthesisAgent()

        await _orchestrator.register_agent(research_agent)
        await _orchestrator.register_agent(evidence_agent)
        await _orchestrator.register_agent(synthesis_agent)

        await _orchestrator.initialize()

    return _orchestrator

# Orchestrator Management Endpoints

@router.post("/initialize")
async def initialize_orchestrator(
    config: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initialize the multi-agent orchestrator"""
    try:
        orchestrator = await get_orchestrator()

        # Update configuration
        orchestrator.max_concurrent_agents = config.get("max_concurrent_agents", 3)
        orchestrator.coordination_strategy = config.get("strategy", "adaptive")

        return {
            "success": True,
            "status": "initialized",
            "agents": len(orchestrator.agents),
            "message": "Orchestrator initialized successfully"
        }

    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize orchestrator: {str(e)}")

@router.post("/start")
async def start_orchestration(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start the orchestrator"""
    try:
        orchestrator = await get_orchestrator()
        await orchestrator.start()

        # Notify connected clients
        await broadcast_to_clients({
            "type": "orchestrator_status",
            "status": "started",
            "timestamp": datetime.now().isoformat()
        })

        return {
            "success": True,
            "status": "running",
            "message": "Orchestration started successfully"
        }

    except Exception as e:
        logger.error(f"Failed to start orchestration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start orchestration: {str(e)}")

@router.post("/pause")
async def pause_orchestration(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pause the orchestrator"""
    try:
        orchestrator = await get_orchestrator()
        await orchestrator.pause()

        # Notify connected clients
        await broadcast_to_clients({
            "type": "orchestrator_status",
            "status": "paused",
            "timestamp": datetime.now().isoformat()
        })

        return {
            "success": True,
            "status": "paused",
            "message": "Orchestration paused successfully"
        }

    except Exception as e:
        logger.error(f"Failed to pause orchestration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pause orchestration: {str(e)}")

@router.post("/stop")
async def stop_orchestration(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop the orchestrator"""
    try:
        orchestrator = await get_orchestrator()
        await orchestrator.stop()

        # Notify connected clients
        await broadcast_to_clients({
            "type": "orchestrator_status",
            "status": "stopped",
            "timestamp": datetime.now().isoformat()
        })

        return {
            "success": True,
            "status": "stopped",
            "message": "Orchestration stopped successfully"
        }

    except Exception as e:
        logger.error(f"Failed to stop orchestration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop orchestration: {str(e)}")

@router.get("/status")
async def get_orchestrator_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current orchestrator status"""
    try:
        orchestrator = await get_orchestrator()

        # Get agent statuses
        agent_statuses = []
        for agent in orchestrator.agents:
            status = await agent.get_status()
            agent_statuses.append(status)

        # Get task queue status
        task_status = {
            "pending_tasks": len(orchestrator.task_queue),
            "running_tasks": len(orchestrator.running_tasks),
            "completed_tasks": len(orchestrator.completed_tasks)
        }

        # Calculate metrics
        total_completed = sum(status["tasks_completed"] for status in agent_statuses)
        total_failed = sum(status["tasks_failed"] for status in agent_statuses)
        total_tasks = total_completed + total_failed

        metrics = {
            "total_tasks_completed": total_completed,
            "total_tasks_failed": total_failed,
            "overall_success_rate": total_completed / total_tasks if total_tasks > 0 else 1.0,
            "average_processing_time": sum(status["average_processing_time"] for status in agent_statuses) / len(agent_statuses) if agent_statuses else 0.0
        }

        return {
            "success": True,
            "status": orchestrator.status,
            "agents": agent_statuses,
            "task_status": task_status,
            "metrics": metrics,
            "message": "Orchestrator status retrieved successfully"
        }

    except Exception as e:
        logger.error(f"Failed to get orchestrator status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get orchestrator status: {str(e)}")

# Agent Management Endpoints

@router.get("/agents")
async def get_agents(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all registered agents"""
    try:
        orchestrator = await get_orchestrator()

        agent_list = []
        for agent in orchestrator.agents:
            status = await agent.get_status()
            agent_list.append(status)

        return {
            "success": True,
            "agents": agent_list,
            "count": len(agent_list),
            "message": "Agents retrieved successfully"
        }

    except Exception as e:
        logger.error(f"Failed to get agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agents: {str(e)}")

@router.post("/agents")
async def add_agent(
    agent_config: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new agent to the orchestrator"""
    try:
        orchestrator = await get_orchestrator()

        agent_type = agent_config.get("type", "research")
        agent_id = agent_config.get("id")
        agent_name = agent_config.get("name", f"Agent {agent_type}")

        # Create agent based on type
        if agent_type == "research":
            agent = ResearchAgent(agent_id=agent_id, name=agent_name)
        elif agent_type == "evidence":
            agent = EvidenceAgent(agent_id=agent_id, name=agent_name)
        elif agent_type == "synthesis":
            agent = SynthesisAgent(agent_id=agent_id, name=agent_name)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown agent type: {agent_type}")

        await orchestrator.register_agent(agent)

        return {
            "success": True,
            "agent": await agent.get_status(),
            "message": "Agent added successfully"
        }

    except Exception as e:
        logger.error(f"Failed to add agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add agent: {str(e)}")

@router.delete("/agents/{agent_id}")
async def remove_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove an agent from the orchestrator"""
    try:
        orchestrator = await get_orchestrator()

        success = await orchestrator.remove_agent(agent_id)

        if success:
            return {
                "success": True,
                "message": f"Agent {agent_id} removed successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove agent: {str(e)}")

@router.put("/agents/{agent_id}")
async def update_agent_configuration(
    agent_id: str,
    config: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update agent configuration"""
    try:
        orchestrator = await get_orchestrator()

        agent = orchestrator.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # Update agent configuration
        if "max_concurrent_tasks" in config:
            agent.max_concurrent_tasks = config["max_concurrent_tasks"]
        if "timeout" in config:
            agent.timeout = config["timeout"]

        return {
            "success": True,
            "agent": await agent.get_status(),
            "message": f"Agent {agent_id} configuration updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update agent configuration: {str(e)}")

@router.get("/agents/{agent_id}/tasks")
async def get_agent_task_history(
    agent_id: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get task history for a specific agent"""
    try:
        orchestrator = await get_orchestrator()

        agent = orchestrator.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        task_history = await agent.get_task_history(limit)

        return {
            "success": True,
            "agent_id": agent_id,
            "tasks": task_history,
            "count": len(task_history),
            "message": "Agent task history retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent task history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent task history: {str(e)}")

# Task Management Endpoints

@router.post("/tasks")
async def assign_task(
    task_config: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assign a task to an agent"""
    try:
        orchestrator = await get_orchestrator()

        # Create task
        task = {
            "id": f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": task_config.get("description", ""),
            "task_type": task_config.get("task_type", "general"),
            "parameters": task_config.get("parameters", {}),
            "priority": task_config.get("priority", "medium"),
            "created_at": datetime.now().isoformat(),
            "created_by": current_user["id"]
        }

        # Assign task (this would use the orchestrator's task assignment logic)
        # For now, we'll simulate task assignment
        assigned_agent = None
        for agent in orchestrator.agents:
            if len(agent.current_tasks) < agent.max_concurrent_tasks:
                assigned_agent = agent
                break

        if assigned_agent:
            task["assigned_agent"] = assigned_agent.agent_id
            task["assigned_agent_name"] = assigned_agent.name
            task["status"] = "assigned"
            task["assigned_at"] = datetime.now().isoformat()

            # Notify clients
            await broadcast_to_clients({
                "type": "task_assigned",
                "task": task,
                "timestamp": datetime.now().isoformat()
            })

            return {
                "success": True,
                "task": task,
                "message": "Task assigned successfully"
            }
        else:
            # Add to queue
            orchestrator.task_queue.append(task)
            task["status"] = "queued"

            return {
                "success": True,
                "task": task,
                "message": "Task added to queue"
            }

    except Exception as e:
        logger.error(f"Failed to assign task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to assign task: {str(e)}")

@router.get("/tasks")
async def get_tasks(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tasks"""
    try:
        orchestrator = await get_orchestrator()

        # Get running tasks from agents
        running_tasks = []
        for agent in orchestrator.agents:
            for task_id, task in agent.current_tasks.items():
                running_tasks.append({
                    "id": task_id,
                    "description": task.description,
                    "task_type": task.task_type,
                    "status": "running",
                    "assigned_agent": agent.agent_id,
                    "assigned_agent_name": agent.name,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "progress": 50  # Mock progress
                })

        # Get queued tasks
        queued_tasks = [
            {
                **task,
                "status": "pending"
            }
            for task in orchestrator.task_queue
        ]

        all_tasks = running_tasks + queued_tasks

        return {
            "success": True,
            "tasks": all_tasks,
            "running_count": len(running_tasks),
            "pending_count": len(queued_tasks),
            "total_count": len(all_tasks),
            "message": "Tasks retrieved successfully"
        }

    except Exception as e:
        logger.error(f"Failed to get tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")

@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a task"""
    try:
        orchestrator = await get_orchestrator()

        # Try to cancel from agents
        for agent in orchestrator.agents:
            if await agent.cancel_task(task_id):
                await broadcast_to_clients({
                    "type": "task_cancelled",
                    "task_id": task_id,
                    "timestamp": datetime.now().isoformat()
                })

                return {
                    "success": True,
                    "message": f"Task {task_id} cancelled successfully"
                }

        # Try to remove from queue
        for i, task in enumerate(orchestrator.task_queue):
            if task.get("id") == task_id:
                orchestrator.task_queue.pop(i)
                return {
                    "success": True,
                    "message": f"Task {task_id} removed from queue"
                }

        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")

@router.delete("/tasks/{task_id}?force=true")
async def remove_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Force remove a task"""
    try:
        orchestrator = await get_orchestrator()

        # Try to cancel from agents
        cancelled = False
        for agent in orchestrator.agents:
            if await agent.cancel_task(task_id):
                cancelled = True
                break

        # Try to remove from queue
        removed_from_queue = False
        for i, task in enumerate(orchestrator.task_queue):
            if task.get("id") == task_id:
                orchestrator.task_queue.pop(i)
                removed_from_queue = True
                break

        if cancelled or removed_from_queue:
            return {
                "success": True,
                "message": f"Task {task_id} removed successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove task: {str(e)}")

# Monitoring and Logging Endpoints

@router.get("/logs")
async def get_orchestration_logs(
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get orchestration logs"""
    try:
        # Mock logs for now (in production, this would retrieve from a log store)
        logs = [
            {
                "id": f"log_{i}",
                "timestamp": datetime.now().isoformat(),
                "level": "info",
                "source": "orchestrator",
                "message": f"Orchestrator log entry {i}"
            }
            for i in range(min(limit, 20))
        ]

        return {
            "success": True,
            "logs": logs,
            "count": len(logs),
            "message": "Orchestration logs retrieved successfully"
        }

    except Exception as e:
        logger.error(f"Failed to get orchestration logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get orchestration logs: {str(e)}")

# WebSocket Endpoint for Real-time Updates

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time orchestrator updates"""
    await websocket.accept()
    _connected_clients.add(websocket)

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "subscribe":
                    # Handle subscription to specific events
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "events": message.get("events", [])
                    }))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))

    except WebSocketDisconnect:
        _connected_clients.remove(websocket)
        logger.info("WebSocket client disconnected")

async def broadcast_to_clients(message: Dict[str, Any]):
    """Broadcast message to all connected WebSocket clients"""
    if _connected_clients:
        message_str = json.dumps(message)
        disconnected_clients = set()

        for client in _connected_clients:
            try:
                await client.send_text(message_str)
            except:
                disconnected_clients.add(client)

        # Remove disconnected clients
        for client in disconnected_clients:
            _connected_clients.discard(client)