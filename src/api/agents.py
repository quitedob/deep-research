# -*- coding: utf-8 -*-
"""
Agent管理API端点
提供Agent注册、调用和协作接口
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..api.deps import require_auth
from ..sqlmodel.models import User
from ..service.agent_manager import get_agent_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])


# Request/Response Models
class CallAgentRequest(BaseModel):
    agent_id: str
    prompt: str
    session_id: Optional[str] = None
    context: Optional[dict] = None


class CollaborateAgentsRequest(BaseModel):
    task: str
    agent_ids: List[str]
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    base_name: str
    description: str
    capabilities: List[str]


class AgentCallResponse(BaseModel):
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None


class CollaborationResponse(BaseModel):
    status: str
    task: str
    results: List[dict]
    session_id: str


@router.get("/list", response_model=List[AgentResponse])
async def list_agents(
    current_user: User = Depends(require_auth)
):
    """列出所有可用的Agents"""
    try:
        manager = get_agent_manager()
        agents = manager.list_agents()
        
        return [
            AgentResponse(
                id=agent["id"],
                name=agent["name"],
                base_name=agent["base_name"],
                description=agent["description"],
                capabilities=agent["capabilities"]
            )
            for agent in agents
        ]
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent_info(
    agent_id: str,
    current_user: User = Depends(require_auth)
):
    """获取Agent详细信息"""
    try:
        manager = get_agent_manager()
        agent = manager.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        
        return AgentResponse(
            id=agent.id,
            name=agent.name,
            base_name=agent.base_name,
            description=agent.description,
            capabilities=agent.capabilities
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/call", response_model=AgentCallResponse)
async def call_agent(
    request: CallAgentRequest,
    current_user: User = Depends(require_auth)
):
    """调用指定的Agent"""
    try:
        manager = get_agent_manager()
        result = await manager.call_agent(
            agent_id=request.agent_id,
            prompt=request.prompt,
            session_id=request.session_id,
            context=request.context
        )
        
        return AgentCallResponse(
            status=result.get("status"),
            result=result.get("result"),
            error=result.get("error"),
            agent_id=result.get("agent_id"),
            agent_name=result.get("agent_name")
        )
    except Exception as e:
        logger.error(f"Error calling agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collaborate", response_model=CollaborationResponse)
async def collaborate_agents(
    request: CollaborateAgentsRequest,
    current_user: User = Depends(require_auth)
):
    """多Agent协作完成任务"""
    try:
        manager = get_agent_manager()
        result = await manager.collaborate_agents(
            task=request.task,
            agent_ids=request.agent_ids,
            session_id=request.session_id
        )
        
        return CollaborationResponse(
            status=result.get("status"),
            task=result.get("task"),
            results=result.get("results", []),
            session_id=result.get("session_id")
        )
    except Exception as e:
        logger.error(f"Error in agent collaboration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{agent_id}/history")
async def get_agent_session_history(
    agent_id: str,
    session_id: str = "default_session",
    current_user: User = Depends(require_auth)
):
    """获取Agent会话历史"""
    try:
        manager = get_agent_manager()
        history = manager.get_agent_session_history(agent_id, session_id)
        
        return {
            "agent_id": agent_id,
            "session_id": session_id,
            "history": history
        }
    except Exception as e:
        logger.error(f"Error getting session history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
