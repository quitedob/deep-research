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
from ..api.errors import create_error_response, ErrorCodes, handle_database_error, handle_not_found_error, APIException
from ..sqlmodel.models import User
from ..services.agentscope_service import get_agentscope_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


# Request/Response Models
class CallAgentRequest(BaseModel):
    agent_id: str
    prompt: str
    session_id: Optional[str] = None
    context: Optional[dict] = None


class CollaborateAgentsRequest(BaseModel):
    task: str
    agent_ids: List[str]
    collaboration_type: str = "sequential"  # sequential, parallel, hierarchical
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
        service = get_agentscope_service()
        agents = await service.list_agents()
        
        return [
            AgentResponse(
                id=agent["config"]["name"],
                name=agent["config"]["name"],
                base_name=agent["config"]["role"],
                description=agent["config"]["system_prompt"][:100] + "...",
                capabilities=agent["config"]["capabilities"]
            )
            for agent in agents
        ]
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        return handle_database_error(e)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent_info(
    agent_id: str,
    current_user: User = Depends(require_auth)
):
    """获取Agent详细信息"""
    try:
        service = get_agentscope_service()
        agent_status = await service.get_agent_status(agent_id)
        
        if not agent_status:
            return handle_not_found_error(f"Agent '{agent_id}'")
        
        return AgentResponse(
            id=agent_status["name"],
            name=agent_status["name"],
            base_name=agent_status["role"],
            description="AgentScope v1.0 智能体",
            capabilities=agent_status["capabilities"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent info: {e}")
        return handle_database_error(e)


@router.post("/call", response_model=AgentCallResponse)
async def call_agent(
    request: CallAgentRequest,
    current_user: User = Depends(require_auth)
):
    """调用指定的Agent"""
    try:
        service = get_agentscope_service()
        result = await service.call_agent(
            agent_id=request.agent_id,
            message=request.prompt,
            session_id=request.session_id,
            context=request.context
        )
        
        return AgentCallResponse(
            status="success" if result.get("success") else "error",
            result=result.get("response"),
            error=result.get("error"),
            agent_id=result.get("agent_id"),
            agent_name=result.get("agent_name")
        )
    except Exception as e:
        logger.error(f"Error calling agent: {e}")
        return handle_database_error(e)


@router.post("/collaborate", response_model=CollaborationResponse)
async def collaborate_agents(
    request: CollaborateAgentsRequest,
    current_user: User = Depends(require_auth)
):
    """多Agent协作完成任务 - 支持顺序、并行、层次化协作"""
    try:
        service = get_agentscope_service()
        result = await service.collaborate_agents(
            task=request.task,
            agent_ids=request.agent_ids,
            collaboration_type=request.collaboration_type,
            session_id=request.session_id
        )
        
        if not result.get("success"):
            raise APIException(
                code=ErrorCodes.BUSINESS_LOGIC_ERROR,
                message=result.get("error"),
                status_code=400
            )
        
        return CollaborationResponse(
            status="success",
            task=request.task,
            results=result.get("results", []),
            session_id=result.get("session_id", request.session_id)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in agent collaboration: {e}")
        return handle_database_error(e)


@router.get("/sessions/{session_id}/history")
async def get_session_history(
    session_id: str,
    current_user: User = Depends(require_auth)
):
    """获取会话历史"""
    try:
        # TODO: 实现会话历史查询
        return {
            "session_id": session_id,
            "message": "Session history feature coming soon with AgentScope v1.0"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session history: {e}")
        return handle_database_error(e)
