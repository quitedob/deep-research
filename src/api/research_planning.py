# -*- coding: utf-8 -*-
"""
Research Planning API Endpoints for Deep Research Platform
Handles research planning, execution, and management API calls
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import asyncio

from ..core.plan.plan_notebook import PlanNotebook
from ..core.plan.planner import ResearchPlanner
from ..core.plan.storage import MemoryPlanStorage
from ..core.database import get_db
from ..core.security import get_current_user
from ..services.user_service import UserService
from ..services.auth_service import AuthService

router = APIRouter(prefix="/api/research-planning", tags=["research-planning"])

# Global instances (in production, these would be properly managed)
_plan_notebook = PlanNotebook()
_research_planner = ResearchPlanner()

# User-specific plan notebooks
_user_plan_notebooks = {}

def get_user_plan_notebook(user_id: str) -> PlanNotebook:
    """Get or create a plan notebook for a specific user"""
    if user_id not in _user_plan_notebooks:
        _user_plan_notebooks[user_id] = PlanNotebook(storage=MemoryPlanStorage())
        _user_plan_notebooks[user_id].set_user_id(user_id)
    return _user_plan_notebooks[user_id]

# Research Plan Management Endpoints

@router.post("/plans")
async def create_research_plan(
    plan_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new research plan"""
    try:
        user_notebook = get_user_plan_notebook(current_user["id"])

        plan = await user_notebook.create_plan(
            title=plan_data.get("title"),
            description=plan_data.get("description"),
            research_query=plan_data.get("research_query"),
            user_id=current_user["id"],
            project_id=plan_data.get("project_id"),
            custom_steps=plan_data.get("custom_steps")
        )

        return {
            "success": True,
            "plan": plan.to_dict(),
            "message": "Research plan created successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create research plan: {str(e)}")

@router.get("/plans/current")
async def get_current_plan(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current active research plan"""
    try:
        user_notebook = get_user_plan_notebook(current_user["id"])
        current_plan = user_notebook.current_plan

        if not current_plan:
            return {
                "success": False,
                "plan": None,
                "message": "No current plan found"
            }

        return {
            "success": True,
            "plan": current_plan.to_dict(),
            "message": "Current plan retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current plan: {str(e)}")

@router.put("/plans/{plan_id}")
async def update_plan(
    plan_id: str,
    plan_update: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a research plan"""
    try:
        user_notebook = get_user_plan_notebook(current_user["id"])

        # Load the plan to check ownership
        plan = await user_notebook.storage.get_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        if plan.created_by != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Update plan
        updated_plan_data = plan.to_dict()
        updated_plan_data.update(plan_update)
        updated_plan_data["updated_at"] = datetime.now()

        success = await user_notebook.storage.update_plan(plan_id, updated_plan_data)

        if success:
            updated_plan = await user_notebook.storage.get_plan(plan_id)
            return {
                "success": True,
                "plan": updated_plan.to_dict(),
                "message": "Plan updated successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update plan")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update plan: {str(e)}")

@router.post("/plans/{plan_id}/revise")
async def revise_plan(
    plan_id: str,
    revision_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revise a research plan"""
    try:
        user_notebook = get_user_plan_notebook(current_user["id"])

        # Load the plan to check ownership
        plan = await user_notebook.storage.get_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        if plan.created_by != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Set as current plan and revise
        user_notebook.current_plan = plan
        revised_plan = await user_notebook.revise_current_plan(
            revision_reason=revision_data.get("revision_reason", ""),
            new_steps=revision_data.get("new_steps")
        )

        return {
            "success": True,
            "plan": revised_plan.to_dict(),
            "message": "Plan revised successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revise plan: {str(e)}")

@router.post("/plans/{plan_id}/finish")
async def finish_plan(
    plan_id: str,
    completion_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Finish a research plan"""
    try:
        user_notebook = get_user_plan_notebook(current_user["id"])

        # Load the plan to check ownership
        plan = await user_notebook.storage.get_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        if plan.created_by != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Set as current plan and finish
        user_notebook.current_plan = plan
        finished_plan = await user_notebook.finish_plan(
            summary=completion_data.get("summary", ""),
            final_insights=completion_data.get("final_insights", [])
        )

        return {
            "success": True,
            "plan": finished_plan.to_dict(),
            "message": "Plan finished successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to finish plan: {str(e)}")

@router.post("/plans/{plan_id}/execute-step")
async def execute_plan_step(
    plan_id: str,
    step_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a step in the research plan"""
    try:
        user_notebook = get_user_plan_notebook(current_user["id"])

        # Load the plan to check ownership
        plan = await user_notebook.storage.get_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        if plan.created_by != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Set as current plan and execute step
        user_notebook.current_plan = plan
        result = await user_notebook.execute_plan_step(
            action_taken=step_data.get("action_taken", ""),
            evidence_collected=step_data.get("evidence_collected", []),
            insights=step_data.get("insights", [])
        )

        return {
            "success": True,
            "result": result,
            "message": "Step executed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute step: {str(e)}")

@router.put("/plans/{plan_id}/subtasks/{subtask_id}")
async def update_subtask_status(
    plan_id: str,
    subtask_id: str,
    status_update: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the status of a subtask"""
    try:
        user_notebook = get_user_plan_notebook(current_user["id"])

        # Load the plan to check ownership
        plan = await user_notebook.storage.get_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        if plan.created_by != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Set as current plan and update subtask
        user_notebook.current_plan = plan
        result = await user_notebook.update_subtask_status(
            status=status_update.get("status", "pending"),
            notes=status_update.get("notes")
        )

        return {
            "success": True,
            "subtask": result,
            "message": "Subtask status updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update subtask status: {str(e)}")

@router.post("/plans/{plan_id}/insights")
async def add_plan_insight(
    plan_id: str,
    insight_data: Dict[str, str],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add an insight to a research plan"""
    try:
        user_notebook = get_user_plan_notebook(current_user["id"])

        # Load the plan to check ownership
        plan = await user_notebook.storage.get_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        if plan.created_by != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Set as current plan and add insight
        user_notebook.current_plan = plan
        result = await user_notebook.add_plan_insight(insight_data.get("insight", ""))

        return {
            "success": True,
            "insight": result,
            "message": "Insight added successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add insight: {str(e)}")

@router.post("/plans/{plan_id}/evidence")
async def add_plan_evidence(
    plan_id: str,
    evidence_data: Dict[str, str],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add evidence reference to a research plan"""
    try:
        user_notebook = get_user_plan_notebook(current_user["id"])

        # Load the plan to check ownership
        plan = await user_notebook.storage.get_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        if plan.created_by != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Set as current plan and add evidence
        user_notebook.current_plan = plan
        result = await user_notebook.add_plan_evidence(evidence_data.get("evidence", ""))

        return {
            "success": True,
            "evidence": result,
            "message": "Evidence reference added successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add evidence reference: {str(e)}")

@router.get("/plans/history")
async def get_historical_plans(
    limit: int = 5,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get historical research plans"""
    try:
        user_notebook = get_user_plan_notebook(current_user["id"])
        plans = await user_notebook.view_historical_plans(limit)

        return {
            "success": True,
            "plans": plans,
            "count": len(plans),
            "message": "Historical plans retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get historical plans: {str(e)}")

@router.post("/plans/{plan_id}/recover")
async def recover_historical_plan(
    plan_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Recover a historical plan"""
    try:
        user_notebook = get_user_plan_notebook(current_user["id"])
        recovered_plan = await user_notebook.recover_historical_plan(plan_id)

        return {
            "success": True,
            "plan": recovered_plan.to_dict(),
            "message": "Plan recovered successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recover plan: {str(e)}")

@router.get("/plans/{plan_id}")
async def get_plan_details(
    plan_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific plan"""
    try:
        user_notebook = get_user_plan_notebook(current_user["id"])
        plan = await user_notebook.storage.get_plan(plan_id)

        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        if plan.created_by != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        return {
            "success": True,
            "plan": plan.to_dict(),
            "message": "Plan details retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plan details: {str(e)}")

@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a research plan"""
    try:
        user_notebook = get_user_plan_notebook(current_user["id"])

        # Load the plan to check ownership
        plan = await user_notebook.storage.get_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        if plan.created_by != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        success = await user_notebook.storage.delete_plan(plan_id)

        # Clear current plan if it was the deleted one
        if user_notebook.current_plan and user_notebook.current_plan.id == plan_id:
            user_notebook.current_plan = None

        return {
            "success": success,
            "message": "Plan deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete plan: {str(e)}")

# Research Planning Utilities

@router.post("/generate-steps")
async def generate_research_steps(
    planning_request: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate research steps for a given query"""
    try:
        steps = await _research_planner.generate_research_steps(
            research_query=planning_request.get("research_query", ""),
            max_steps=planning_request.get("max_steps", 5),
            domain=planning_request.get("domain")
        )

        return {
            "success": True,
            "steps": steps,
            "message": "Research steps generated successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate research steps: {str(e)}")

@router.post("/generate-working-plan")
async def generate_working_plan(
    plan_request: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a detailed working plan for a research step"""
    try:
        working_plan = await _research_planner.generate_working_plan(
            step_description=plan_request.get("step_description", ""),
            context=plan_request.get("context", {})
        )

        return {
            "success": True,
            "working_plan": working_plan,
            "message": "Working plan generated successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate working plan: {str(e)}")

@router.post("/evaluate-progress")
async def evaluate_research_progress(
    evaluation_request: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Evaluate research progress and provide recommendations"""
    try:
        user_notebook = get_user_plan_notebook(current_user["id"])

        plan_id = evaluation_request.get("plan_id")
        if not plan_id:
            raise HTTPException(status_code=400, detail="Plan ID is required")

        plan = await user_notebook.storage.get_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        if plan.created_by != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        evaluation = await _research_planner.evaluate_research_progress(
            plan=plan,
            current_step=evaluation_request.get("current_step", 0),
            findings=evaluation_request.get("findings", []),
            evidence_count=evaluation_request.get("evidence_count", 0)
        )

        return {
            "success": True,
            "evaluation": evaluation,
            "message": "Research progress evaluated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate research progress: {str(e)}")