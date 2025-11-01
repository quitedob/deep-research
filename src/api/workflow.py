#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangGraph工作流API端点
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging

from src.services.langgraph_workflow import (
    get_langgraph_workflow,
    create_research_workflow,
    ResearchWorkflowConfig
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


class WorkflowRequest(BaseModel):
    """工作流请求"""
    query: str = Field(..., description="研究查询")
    max_iterations: Optional[int] = Field(3, description="最大迭代次数")
    min_research_sources: Optional[int] = Field(3, description="最小研究来源数")
    quality_threshold: Optional[float] = Field(0.7, description="质量阈值")
    enable_parallel_research: Optional[bool] = Field(True, description="启用并行研究")
    enable_supervisor_feedback: Optional[bool] = Field(True, description="启用监督反馈")


class WorkflowResponse(BaseModel):
    """工作流响应"""
    success: bool
    final_content: Optional[str] = None
    research_results: Optional[List[Dict[str, Any]]] = None
    iterations: Optional[int] = None
    execution_history: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


@router.post("/research", response_model=WorkflowResponse)
async def run_research_workflow(request: WorkflowRequest):
    """
    运行研究工作流
    
    执行完整的研究工作流：researcher → writer → supervisor
    """
    try:
        # 创建工作流配置
        config = ResearchWorkflowConfig(
            max_iterations=request.max_iterations,
            min_research_sources=request.min_research_sources,
            quality_threshold=request.quality_threshold,
            enable_parallel_research=request.enable_parallel_research,
            enable_supervisor_feedback=request.enable_supervisor_feedback
        )
        
        # 创建工作流实例
        workflow = create_research_workflow(config)
        
        # 运行工作流
        result = await workflow.run(request.query)
        
        if result["success"]:
            return WorkflowResponse(
                success=True,
                final_content=result["final_content"],
                research_results=result["research_results"],
                iterations=result["iterations"],
                execution_history=result["execution_history"]
            )
        else:
            return WorkflowResponse(
                success=False,
                error=result.get("error", "Unknown error")
            )
            
    except Exception as e:
        logger.error(f"Research workflow failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """获取工作流状态"""
    try:
        workflow = get_langgraph_workflow(workflow_id)
        summary = workflow.get_execution_summary()
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{workflow_id}")
async def get_workflow_history(workflow_id: str):
    """获取工作流执行历史"""
    try:
        workflow = get_langgraph_workflow(workflow_id)
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "execution_history": workflow.execution_history,
            "state": workflow.get_state_dict()
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflow history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
