# -*- coding: utf-8 -*-
"""
深度研究API路由（SSE 进度）并记录使用统计  # 模块说明
"""
from __future__ import annotations
import asyncio  # 异步
import json  # 序列化
import uuid  # 会话ID
import logging  # 日志
from typing import Dict, Any, Optional  # 类型
from fastapi import APIRouter, HTTPException, BackgroundTasks, Header  # FastAPI
from fastapi.responses import StreamingResponse  # SSE
from pydantic import BaseModel  # 模型
from src.graph.builder import agent_graph  # 工作流图
from src.server.routers.auth import verify_token  # Token
from src.server.db import insert_usage_log, get_user_by_username  # DB

logger = logging.getLogger(__name__)  # 日志器
router = APIRouter(prefix="/api", tags=["深度研究模式"])  # 路由器

# 会话内存存储
research_sessions: Dict[str, Dict[str, Any]] = {}


class ResearchRequest(BaseModel):  # 请求模型
    query: str  # 研究主题


class ResearchStatus(BaseModel):  # 启动返回
    session_id: str
    status: str
    message: str


class FinalReport(BaseModel):  # 最终报告
    session_id: str
    query: str
    report: str


async def run_research_in_background(session_id: str, query: str, user_id: Optional[int]):
    """后台运行研究图，持续写入进度和最终报告"""
    try:
        config = {"configurable": {"thread_id": session_id}}
        inputs = {"messages": [{"role": "user", "content": query}]}
        async for event in agent_graph.astream_events(inputs, config, version="v2"):
            kind = event["event"]
            if kind == "on_chain_start":
                research_sessions[session_id]["status"] = "running"
            if kind == "on_chain_stream":
                chunk = event["data"]["chunk"]
                research_sessions[session_id]["progress"].append(chunk)
            if kind == "on_chain_end":
                final_state = event["data"]["output"]
                research_sessions[session_id]["status"] = "completed"
                research_sessions[session_id]["final_report"] = final_state.get("report", "")
                insert_usage_log(user_id, endpoint="/api/research", model=None)
    except Exception as e:
        logger.error(f"后台研究任务失败(session={session_id}): {e}", exc_info=True)
        research_sessions[session_id]["status"] = "failed"
        research_sessions[session_id]["error"] = str(e)


@router.post("/research", response_model=ResearchStatus)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks, authorization: str | None = Header(default=None)):
    """启动深度研究任务并立即返回 session_id"""
    session_id = f"research-session-{uuid.uuid4()}"

    # 解析可选用户
    user_id: Optional[int] = None
    if authorization and authorization.startswith("Bearer "):
        username = verify_token(authorization.split(" ", 1)[1])
        if username:
            user = get_user_by_username(username)
            user_id = user["id"] if user else None

    research_sessions[session_id] = {
        "status": "pending",
        "query": request.query,
        "progress": [],
        "final_report": None,
        "error": None,
        "user_id": user_id,
    }

    background_tasks.add_task(run_research_in_background, session_id, request.query, user_id)

    return ResearchStatus(session_id=session_id, status="started", message="研究任务已启动，请通过流式端点获取进度。")


@router.get("/research/stream/{session_id}")
async def stream_research_progress(session_id: str):
    """SSE 推送研究进度"""
    if session_id not in research_sessions:
        raise HTTPException(status_code=404, detail="研究会话不存在")

    async def event_generator():
        last = 0
        while True:
            session = research_sessions.get(session_id)
            if not session:
                break
            while last < len(session["progress"]):
                chunk = session["progress"][last]
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                last += 1
            if session["status"] in ("completed", "failed"):
                final_event = {"status": session["status"], "error": session.get("error")}
                yield f"data: {json.dumps(final_event, ensure_ascii=False)}\n\n"
                break
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/research/{session_id}", response_model=FinalReport)
async def get_research_result(session_id: str):
    """返回最终研究报告"""
    session = research_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="研究会话不存在")
    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"研究任务尚未完成，当前状态: {session['status']}")
    return FinalReport(session_id=session_id, query=session["query"], report=session.get("final_report") or "")


