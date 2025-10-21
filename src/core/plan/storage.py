# -*- coding: utf-8 -*-
"""
Plan Storage for Deep Research Platform
Handles persistence and retrieval of research plans
"""

import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from .plan import Plan, PlanStatus


class PlanStorageBase(ABC):
    """Base class for plan storage implementations"""

    @abstractmethod
    async def save_plan(self, plan: Plan) -> str:
        """Save a plan and return its ID"""
        pass

    @abstractmethod
    async def get_plan(self, plan_id: str) -> Optional[Plan]:
        """Retrieve a plan by ID"""
        pass

    @abstractmethod
    async def get_plans_by_user(self, user_id: str) -> List[Plan]:
        """Get all plans for a user"""
        pass

    @abstractmethod
    async def get_plans_by_project(self, project_id: str) -> List[Plan]:
        """Get all plans for a project"""
        pass

    @abstractmethod
    async def update_plan(self, plan_id: str, plan_data: Dict[str, Any]) -> bool:
        """Update a plan"""
        pass

    @abstractmethod
    async def delete_plan(self, plan_id: str) -> bool:
        """Delete a plan"""
        pass

    @abstractmethod
    async def get_historical_plans(self, user_id: str, limit: int = 10) -> List[Plan]:
        """Get historical plans for a user"""
        pass


class FilePlanStorage(PlanStorageBase):
    """File-based plan storage implementation"""

    def __init__(self, storage_dir: str = "plans_storage"):
        self.storage_dir = storage_dir
        self.plans_dir = os.path.join(storage_dir, "plans")
        self.user_index_dir = os.path.join(storage_dir, "users")
        self.project_index_dir = os.path.join(storage_dir, "projects")

        # Create directories if they don't exist
        os.makedirs(self.plans_dir, exist_ok=True)
        os.makedirs(self.user_index_dir, exist_ok=True)
        os.makedirs(self.project_index_dir, exist_ok=True)

    async def save_plan(self, plan: Plan) -> str:
        """Save a plan to file storage"""
        # Save plan data
        plan_file = os.path.join(self.plans_dir, f"{plan.id}.json")
        plan_data = plan.model_dump()

        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan_data, f, ensure_ascii=False, indent=2, default=str)

        # Update user index
        await self._update_user_index(plan.created_by, plan.id)

        # Update project index if applicable
        if plan.project_id:
            await self._update_project_index(plan.project_id, plan.id)

        return plan.id

    async def get_plan(self, plan_id: str) -> Optional[Plan]:
        """Retrieve a plan from file storage"""
        plan_file = os.path.join(self.plans_dir, f"{plan_id}.json")

        if not os.path.exists(plan_file):
            return None

        try:
            with open(plan_file, 'r', encoding='utf-8') as f:
                plan_data = json.load(f)
            return Plan(**plan_data)
        except Exception as e:
            print(f"Error loading plan {plan_id}: {e}")
            return None

    async def get_plans_by_user(self, user_id: str) -> List[Plan]:
        """Get all plans for a user"""
        user_index_file = os.path.join(self.user_index_dir, f"{user_id}.json")

        if not os.path.exists(user_index_file):
            return []

        try:
            with open(user_index_file, 'r', encoding='utf-8') as f:
                plan_ids = json.load(f)

            plans = []
            for plan_id in plan_ids:
                plan = await self.get_plan(plan_id)
                if plan:
                    plans.append(plan)

            # Sort by creation date, newest first
            plans.sort(key=lambda p: p.created_at, reverse=True)
            return plans
        except Exception as e:
            print(f"Error loading user plans for {user_id}: {e}")
            return []

    async def get_plans_by_project(self, project_id: str) -> List[Plan]:
        """Get all plans for a project"""
        project_index_file = os.path.join(self.project_index_dir, f"{project_id}.json")

        if not os.path.exists(project_index_file):
            return []

        try:
            with open(project_index_file, 'r', encoding='utf-8') as f:
                plan_ids = json.load(f)

            plans = []
            for plan_id in plan_ids:
                plan = await self.get_plan(plan_id)
                if plan:
                    plans.append(plan)

            # Sort by creation date, newest first
            plans.sort(key=lambda p: p.created_at, reverse=True)
            return plans
        except Exception as e:
            print(f"Error loading project plans for {project_id}: {e}")
            return []

    async def update_plan(self, plan_id: str, plan_data: Dict[str, Any]) -> bool:
        """Update a plan in file storage"""
        plan = await self.get_plan(plan_id)
        if not plan:
            return False

        # Update plan with new data
        for key, value in plan_data.items():
            if hasattr(plan, key):
                setattr(plan, key, value)

        plan.updated_at = datetime.now()

        # Save updated plan
        plan_file = os.path.join(self.plans_dir, f"{plan_id}.json")
        updated_data = plan.model_dump()

        try:
            with open(plan_file, 'w', encoding='utf-8') as f:
                json.dump(updated_data, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error updating plan {plan_id}: {e}")
            return False

    async def delete_plan(self, plan_id: str) -> bool:
        """Delete a plan from file storage"""
        plan = await self.get_plan(plan_id)
        if not plan:
            return False

        # Delete plan file
        plan_file = os.path.join(self.plans_dir, f"{plan_id}.json")
        try:
            os.remove(plan_file)

            # Remove from user index
            await self._remove_from_user_index(plan.created_by, plan_id)

            # Remove from project index if applicable
            if plan.project_id:
                await self._remove_from_project_index(plan.project_id, plan_id)

            return True
        except Exception as e:
            print(f"Error deleting plan {plan_id}: {e}")
            return False

    async def get_historical_plans(self, user_id: str, limit: int = 10) -> List[Plan]:
        """Get historical plans for a user"""
        all_plans = await self.get_plans_by_user(user_id)

        # Filter completed plans and sort by completion time
        completed_plans = [
            plan for plan in all_plans
            if plan.status == PlanStatus.COMPLETED
        ]

        completed_plans.sort(
            key=lambda p: p.updated_at,
            reverse=True
        )

        return completed_plans[:limit]

    async def _update_user_index(self, user_id: str, plan_id: str) -> None:
        """Update user index with new plan"""
        user_index_file = os.path.join(self.user_index_dir, f"{user_id}.json")

        plan_ids = []
        if os.path.exists(user_index_file):
            try:
                with open(user_index_file, 'r', encoding='utf-8') as f:
                    plan_ids = json.load(f)
            except:
                plan_ids = []

        if plan_id not in plan_ids:
            plan_ids.append(plan_id)

            with open(user_index_file, 'w', encoding='utf-8') as f:
                json.dump(plan_ids, f, indent=2)

    async def _update_project_index(self, project_id: str, plan_id: str) -> None:
        """Update project index with new plan"""
        project_index_file = os.path.join(self.project_index_dir, f"{project_id}.json")

        plan_ids = []
        if os.path.exists(project_index_file):
            try:
                with open(project_index_file, 'r', encoding='utf-8') as f:
                    plan_ids = json.load(f)
            except:
                plan_ids = []

        if plan_id not in plan_ids:
            plan_ids.append(plan_id)

            with open(project_index_file, 'w', encoding='utf-8') as f:
                json.dump(plan_ids, f, indent=2)

    async def _remove_from_user_index(self, user_id: str, plan_id: str) -> None:
        """Remove plan from user index"""
        user_index_file = os.path.join(self.user_index_dir, f"{user_id}.json")

        if os.path.exists(user_index_file):
            try:
                with open(user_index_file, 'r', encoding='utf-8') as f:
                    plan_ids = json.load(f)

                if plan_id in plan_ids:
                    plan_ids.remove(plan_id)

                    with open(user_index_file, 'w', encoding='utf-8') as f:
                        json.dump(plan_ids, f, indent=2)
            except Exception as e:
                print(f"Error removing plan from user index: {e}")

    async def _remove_from_project_index(self, project_id: str, plan_id: str) -> None:
        """Remove plan from project index"""
        project_index_file = os.path.join(self.project_index_dir, f"{project_id}.json")

        if os.path.exists(project_index_file):
            try:
                with open(project_index_file, 'r', encoding='utf-8') as f:
                    plan_ids = json.load(f)

                if plan_id in plan_ids:
                    plan_ids.remove(plan_id)

                    with open(project_index_file, 'w', encoding='utf-8') as f:
                        json.dump(plan_ids, f, indent=2)
            except Exception as e:
                print(f"Error removing plan from project index: {e}")


class MemoryPlanStorage(PlanStorageBase):
    """In-memory plan storage for development and testing"""

    def __init__(self):
        self._plans: Dict[str, Plan] = {}
        self._user_plans: Dict[str, List[str]] = {}
        self._project_plans: Dict[str, List[str]] = {}

    async def save_plan(self, plan: Plan) -> str:
        """Save a plan to memory"""
        self._plans[plan.id] = plan

        # Update user index
        if plan.created_by not in self._user_plans:
            self._user_plans[plan.created_by] = []
        if plan.id not in self._user_plans[plan.created_by]:
            self._user_plans[plan.created_by].append(plan.id)

        # Update project index if applicable
        if plan.project_id:
            if plan.project_id not in self._project_plans:
                self._project_plans[plan.project_id] = []
            if plan.id not in self._project_plans[plan.project_id]:
                self._project_plans[plan.project_id].append(plan.id)

        return plan.id

    async def get_plan(self, plan_id: str) -> Optional[Plan]:
        """Retrieve a plan from memory"""
        return self._plans.get(plan_id)

    async def get_plans_by_user(self, user_id: str) -> List[Plan]:
        """Get all plans for a user from memory"""
        plan_ids = self._user_plans.get(user_id, [])
        plans = []

        for plan_id in plan_ids:
            plan = self._plans.get(plan_id)
            if plan:
                plans.append(plan)

        plans.sort(key=lambda p: p.created_at, reverse=True)
        return plans

    async def get_plans_by_project(self, project_id: str) -> List[Plan]:
        """Get all plans for a project from memory"""
        plan_ids = self._project_plans.get(project_id, [])
        plans = []

        for plan_id in plan_ids:
            plan = self._plans.get(plan_id)
            if plan:
                plans.append(plan)

        plans.sort(key=lambda p: p.created_at, reverse=True)
        return plans

    async def update_plan(self, plan_id: str, plan_data: Dict[str, Any]) -> bool:
        """Update a plan in memory"""
        plan = self._plans.get(plan_id)
        if not plan:
            return False

        for key, value in plan_data.items():
            if hasattr(plan, key):
                setattr(plan, key, value)

        plan.updated_at = datetime.now()
        return True

    async def delete_plan(self, plan_id: str) -> bool:
        """Delete a plan from memory"""
        plan = self._plans.get(plan_id)
        if not plan:
            return False

        # Remove from main storage
        del self._plans[plan_id]

        # Remove from user index
        user_plans = self._user_plans.get(plan.created_by, [])
        if plan_id in user_plans:
            user_plans.remove(plan_id)
            self._user_plans[plan.created_by] = user_plans

        # Remove from project index if applicable
        if plan.project_id:
            project_plans = self._project_plans.get(plan.project_id, [])
            if plan_id in project_plans:
                project_plans.remove(plan_id)
                self._project_plans[plan.project_id] = project_plans

        return True

    async def get_historical_plans(self, user_id: str, limit: int = 10) -> List[Plan]:
        """Get historical plans for a user from memory"""
        all_plans = await self.get_plans_by_user(user_id)

        completed_plans = [
            plan for plan in all_plans
            if plan.status == PlanStatus.COMPLETED
        ]

        completed_plans.sort(key=lambda p: p.updated_at, reverse=True)
        return completed_plans[:limit]