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
from ..service.agent_manager_v2 import get_agent_manager_v2

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
        manager = get_agent_manager_v2()
        agents = manager.list_agents()
        
        return [
            AgentResponse(
                id=agent["status"]["id"],
                name=agent["config"]["name"],
                base_name=agent["config"]["role"],
                description=agent["config"]["system_prompt"][:100] + "...",
                capabilities=agent["config"]["capabilities"]
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
        manager = get_agent_manager_v2()
        agent = manager.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        
        agent_dict = agent.to_dict()
        return AgentResponse(
            id=agent_dict["status"]["id"],
            name=agent_dict["config"]["name"],
            base_name=agent_dict["config"]["role"],
            description=agent_dict["config"]["system_prompt"][:100] + "...",
            capabilities=agent_dict["config"]["capabilities"]
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
        manager = get_agent_manager_v2()
        result = await manager.call_agent(
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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collaborate", response_model=CollaborationResponse)
async def collaborate_agents(
    request: CollaborateAgentsRequest,
    current_user: User = Depends(require_auth)
):
    """多Agent协作完成任务 - 支持顺序、并行、层次化协作"""
    try:
        manager = get_agent_manager_v2()
        result = await manager.collaborate_agents(
            agent_ids=request.agent_ids,
            task=request.task,
            collaboration_type=request.collaboration_type,
            session_id=request.session_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        # 格式化结果以匹配响应模型
        collaboration_result = result.get("result", {})
        formatted_results = []
        
        if collaboration_result.get("type") == "sequential":
            formatted_results = collaboration_result.get("steps", [])
        elif collaboration_result.get("type") == "parallel":
            formatted_results = collaboration_result.get("results", [])
        elif collaboration_result.get("type") == "hierarchical":
            coordinator = collaboration_result.get("coordinator", {})
            workers = collaboration_result.get("workers", [])
            formatted_results = [coordinator] + workers
        
        return CollaborationResponse(
            status="success",
            task=request.task,
            results=formatted_results,
            session_id=request.session_id or result.get("collaboration_id", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in agent collaboration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/history")
async def get_session_history(
    session_id: str,
    current_user: User = Depends(require_auth)
):
    """获取会话历史"""
    try:
        manager = get_agent_manager_v2()
        
        if session_id not in manager.sessions:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
        
        session = manager.sessions[session_id]
        
        return {
            "session_id": session_id,
            "created_at": session["created_at"].isoformat(),
            "last_activity": session.get("last_activity", session["created_at"]).isoformat(),
            "agents_used": list(session["agents_used"]),
            "messages": session["messages"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
