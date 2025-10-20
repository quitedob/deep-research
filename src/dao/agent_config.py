# -*- coding: utf-8 -*-
"""
AgentConfigurationDAO: Agent LLM configuration data access operations.
Provides high-level methods for managing agent configurations with database persistence.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.sqlmodel.models import AgentConfiguration, User
from .base import BaseRepository


class AgentConfigurationDAO(BaseRepository[AgentConfiguration]):
    """Data access object for agent configuration operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AgentConfiguration)

    async def get_by_agent_id(self, agent_id: str) -> Optional[AgentConfiguration]:
        """Get configuration by agent ID."""
        return await self.find_one({"agent_id": agent_id})

    async def get_all_active_configs(self) -> List[AgentConfiguration]:
        """Get all active agent configurations."""
        return await self.find_many(
            filters={"is_active": True},
            order_by="agent_id"
        )

    async def get_all_configs(self) -> List[AgentConfiguration]:
        """Get all agent configurations (including inactive)."""
        return await self.find_all(order_by="agent_id")

    async def create_or_update_config(
        self,
        agent_id: str,
        agent_name: str,
        llm_provider: str,
        model_name: str,
        description: Optional[str] = None,
        is_active: bool = True,
        updated_by: Optional[str] = None
    ) -> AgentConfiguration:
        """Create or update an agent configuration."""
        # Check if configuration exists
        existing_config = await self.get_by_agent_id(agent_id)

        if existing_config:
            # Update existing configuration
            update_data = {
                "agent_name": agent_name,
                "llm_provider": llm_provider,
                "model_name": model_name,
                "description": description,
                "is_active": is_active,
                "updated_by": updated_by
            }
            return await self.update(str(existing_config.id), update_data)
        else:
            # Create new configuration
            return await self.create(
                agent_id=agent_id,
                agent_name=agent_name,
                llm_provider=llm_provider,
                model_name=model_name,
                description=description,
                is_active=is_active,
                updated_by=updated_by
            )

    async def update_config(
        self,
        agent_id: str,
        llm_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        updated_by: Optional[str] = None
    ) -> Optional[AgentConfiguration]:
        """Update specific fields of an agent configuration."""
        config = await self.get_by_agent_id(agent_id)
        if not config:
            return None

        update_data = {}
        if llm_provider is not None:
            update_data["llm_provider"] = llm_provider
        if model_name is not None:
            update_data["model_name"] = model_name
        if description is not None:
            update_data["description"] = description
        if is_active is not None:
            update_data["is_active"] = is_active
        if updated_by is not None:
            update_data["updated_by"] = updated_by

        return await self.update(str(config.id), update_data)

    async def deactivate_config(self, agent_id: str, updated_by: Optional[str] = None) -> bool:
        """Deactivate an agent configuration."""
        config = await self.update_config(
            agent_id=agent_id,
            is_active=False,
            updated_by=updated_by
        )
        return config is not None

    async def activate_config(self, agent_id: str, updated_by: Optional[str] = None) -> bool:
        """Activate an agent configuration."""
        config = await self.update_config(
            agent_id=agent_id,
            is_active=True,
            updated_by=updated_by
        )
        return config is not None

    async def delete_config(self, agent_id: str) -> bool:
        """Delete an agent configuration."""
        config = await self.get_by_agent_id(agent_id)
        if not config:
            return False

        return await self.delete(str(config.id))

    async def get_configs_by_provider(self, llm_provider: str) -> List[AgentConfiguration]:
        """Get all configurations for a specific LLM provider."""
        return await self.find_many(
            filters={"llm_provider": llm_provider, "is_active": True},
            order_by="agent_id"
        )

    async def get_config_with_user(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration with user information about who updated it."""
        config = await self.get_by_agent_id(agent_id)
        if not config:
            return None

        user_info = None
        if config.updated_by:
            user_query = select(User).where(User.id == config.updated_by)
            user_result = await self.session.execute(user_query)
            user = user_result.scalar_one_or_none()
            if user:
                user_info = {
                    "id": str(user.id),
                    "username": user.username
                }

        return {
            "id": str(config.id),
            "agent_id": config.agent_id,
            "agent_name": config.agent_name,
            "llm_provider": config.llm_provider,
            "model_name": config.model_name,
            "description": config.description,
            "is_active": config.is_active,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
            "updated_by": user_info
        }

    async def get_all_configs_with_users(self) -> List[Dict[str, Any]]:
        """Get all configurations with user information."""
        configs = await self.get_all_configs()
        result = []

        for config in configs:
            user_info = None
            if config.updated_by:
                user_query = select(User).where(User.id == config.updated_by)
                user_result = await self.session.execute(user_query)
                user = user_result.scalar_one_or_none()
                if user:
                    user_info = {
                        "id": str(user.id),
                        "username": user.username
                    }

            result.append({
                "id": str(config.id),
                "agent_id": config.agent_id,
                "agent_name": config.agent_name,
                "llm_provider": config.llm_provider,
                "model_name": config.model_name,
                "description": config.description,
                "is_active": config.is_active,
                "created_at": config.created_at,
                "updated_at": config.updated_at,
                "updated_by": user_info
            })

        return result

    async def batch_update_configs(
        self,
        updates: List[Dict[str, Any]],
        updated_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Batch update multiple configurations."""
        results = []

        for update in updates:
            agent_id = update.get("agent_id")
            if not agent_id:
                results.append({
                    "agent_id": agent_id,
                    "success": False,
                    "error": "Missing agent_id"
                })
                continue

            try:
                config = await self.update_config(
                    agent_id=agent_id,
                    llm_provider=update.get("llm_provider"),
                    model_name=update.get("model_name"),
                    description=update.get("description"),
                    is_active=update.get("is_active"),
                    updated_by=updated_by
                )

                if config:
                    results.append({
                        "agent_id": agent_id,
                        "success": True,
                        "config": {
                            "id": str(config.id),
                            "agent_id": config.agent_id,
                            "agent_name": config.agent_name,
                            "llm_provider": config.llm_provider,
                            "model_name": config.model_name,
                            "description": config.description,
                            "is_active": config.is_active
                        }
                    })
                else:
                    results.append({
                        "agent_id": agent_id,
                        "success": False,
                        "error": "Configuration not found"
                    })
            except Exception as e:
                results.append({
                    "agent_id": agent_id,
                    "success": False,
                    "error": str(e)
                })

        return results

    async def initialize_default_configs(self) -> int:
        """Initialize default agent configurations from predefined defaults."""
        default_configs = {
            "research_coordinator": {
                "agent_name": "研究协调员",
                "llm_provider": "doubao",
                "model_name": "doubao-seed-1-6-flash-250615",
                "description": "协调整个研究流程"
            },
            "web_searcher": {
                "agent_name": "网络搜索专家",
                "llm_provider": "doubao",
                "model_name": "doubao-seed-1-6-flash-250615",
                "description": "执行联网搜索任务"
            },
            "data_analyst": {
                "agent_name": "数据分析师",
                "llm_provider": "deepseek",
                "model_name": "deepseek-chat",
                "description": "分析和处理数据"
            },
            "report_writer": {
                "agent_name": "报告撰写员",
                "llm_provider": "kimi",
                "model_name": "moonshot-v1-8k",
                "description": "撰写研究报告"
            },
            "code_expert": {
                "agent_name": "代码专家",
                "llm_provider": "deepseek",
                "model_name": "deepseek-chat",
                "description": "处理代码相关任务"
            },
            "vision_analyst": {
                "agent_name": "视觉分析师",
                "llm_provider": "doubao",
                "model_name": "doubao-1-5-vision-pro-250328",
                "description": "处理图像和视觉任务"
            }
        }

        created_count = 0
        for agent_id, config_data in default_configs.items():
            existing = await self.get_by_agent_id(agent_id)
            if not existing:
                await self.create(agent_id=agent_id, **config_data)
                created_count += 1

        return created_count