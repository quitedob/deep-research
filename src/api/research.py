# -*- coding: utf-8 -*-
"""
研究功能API端点
"""

from typing import Optional
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services.session_service import store
from src.schemas.research import ResearchReq, ResearchResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/research", response_model=ResearchResponse)
async def start_research(req: ResearchReq):
    """
    多智能体研究端点：使用LangGraph工作流进行深度研究。
    """
    try:
        session_id = await store.ensure_session(req.session_id)

        # 导入多智能体工作流
        from src.graph.builder import agent_graph

        # 初始化工作流状态
        initial_state = {
            "original_query": req.query,
            "iteration_count": 0,
            "error_log": [],
            "retrieved_documents": [],
            "analysis_results": {},
            "draft_report": None,
            "next_action": "supervisor",
            "human_review_required": False,
            "feedback_request": None,
            "user_feedback": None
        }

        # 运行多智能体工作流
        logger.info(f"Starting research workflow for query: {req.query}")

        # 使用astream进行异步流式处理
        final_state = None
        async for state in agent_graph.astream(initial_state):
            final_state = state
            logger.info(f"Workflow step completed. Next action: {state.get('next_action', 'unknown')}")

            # 如果工作流完成，退出循环
            if state.get("next_action") == "finish":
                break

        # 获取最终报告
        if final_state and final_state.get("draft_report"):
            report_content = final_state["draft_report"]
            logger.info(f"Research completed successfully. Report length: {len(report_content)}")

            # 保存研究报告到会话存储
            await store.set_research_report(session_id, req.query, report_content)

            return ResearchResponse(
                session_id=session_id,
                status="completed",
                documents_found=len(final_state.get("retrieved_documents", [])),
                iterations=final_state.get("iteration_count", 0)
            )
        else:
            # 如果没有生成报告，创建一个错误报告
            error_report = f"# 研究失败\n\n查询: {req.query}\n\n错误: 工作流未能生成有效报告。请检查系统配置和日志。"
            await store.set_research_report(session_id, req.query, error_report)

            return ResearchResponse(
                session_id=session_id,
                status="failed",
                error="工作流未能生成有效报告"
            )

    except Exception as e:
        logger.error(f"Research workflow error: {e}")
        import traceback
        traceback.print_exc()

        # 即使出错也要创建会话和基础报告
        try:
            session_id = await store.ensure_session(req.session_id)
            error_report = f"# 研究错误\n\n查询: {req.query}\n\n系统错误: {str(e)}\n\n请稍后重试或联系管理员。"
            await store.set_research_report(session_id, req.query, error_report)

            return ResearchResponse(
                session_id=session_id,
                status="error",
                error=str(e)
            )
        except Exception as inner_e:
            raise HTTPException(status_code=500, detail=f"研究失败: {str(e)}")

@router.get("/research/{session_id}")
async def get_research_report(session_id: str):
    """获取研究报告"""
    try:
        doc = await store.get_research_report(session_id)
        if not doc:
            raise HTTPException(status_code=404, detail="report not ready")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取研究报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/research/stream/{session_id}")
async def research_stream(session_id: str):
    """
    最小可用研究流式端点：发送若干进度事件，最后发送 completed 状态。
    前端收到 completed 后会调用 /api/research/{session_id} 拉取最终报告。
    """
    try:
        from fastapi.responses import StreamingResponse
        import asyncio

        async def _gen():
            try:
                yield "data: {\"phase\":\"planning\",\"message\":\"生成研究计划...\"}\n\n".encode("utf-8")
                await asyncio.sleep(0.05)
                yield "data: {\"phase\":\"collecting\",\"message\":\"检索与收集资料...\"}\n\n".encode("utf-8")
                await asyncio.sleep(0.05)
                yield "data: {\"phase\":\"synthesizing\",\"message\":\"撰写报告...\"}\n\n".encode("utf-8")
                await asyncio.sleep(0.05)
                yield "data: {\"status\":\"completed\"}\n\n".encode("utf-8")
            except Exception as e:
                yield f"data: {{\"status\":\"failed\",\"error\":{str(e)!r}}}\n\n".encode("utf-8")

        return StreamingResponse(_gen(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"研究流式端点失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))