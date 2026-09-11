#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度研究API接口
提供AgentScope深度研究功能的REST API
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
import json
import logging
import os

logger = logging.getLogger(__name__)

from backend.services.evidence import citation_evidence
from backend.services.agentscope_research_service import AgentScopeResearchService
from backend.middleware.auth import get_current_user
from backend.core.security.quota import enforce_request_quota
from backend.schemas.research import (
    ResearchRequest,
    ResearchResponse,
    ResearchStatusResponse,
    ResearchListResponse,
    ResearchExportResponse
)


# 创建路由器
router = APIRouter(prefix="/api/research", tags=["deep-research"])

# 创建服务实例
research_service = AgentScopeResearchService()

TERMINAL_STATUSES = {"completed", "failed", "error", "interrupted", "not_found"}
STREAM_TIMEOUT_SECONDS = max(1, int(os.getenv("RESEARCH_STREAM_TIMEOUT_SECONDS", "3600")))


def scoped_user_id(requested_user_id: Optional[str], current_user: Dict[str, Any]) -> str:
    user_id = current_user["user_id"]
    if requested_user_id is not None and requested_user_id != user_id:
        raise HTTPException(status_code=403, detail="无权访问其他用户的数据")
    return user_id


async def require_session_access(session_id: str, current_user: Dict[str, Any]):
    if not await research_service.validate_session_access(session_id, current_user["user_id"]):
        raise HTTPException(status_code=403, detail="无权访问此研究会话")


@router.post("/start", response_model=ResearchResponse, dependencies=[Depends(enforce_request_quota)])
async def start_research(
    request: ResearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    启动深度研究
    """
    try:
        # 从认证的用户信息中获取用户ID
        user_id = current_user["user_id"]

        # 处理 LLM 配置
        llm_provider = None
        if request.llm_config:
            llm_provider = request.llm_config.get("provider", "deepseek")

        # 处理多模态 LLM 配置（如果需要）
        multimodal_llm_instance = None
        if request.include_images and request.multimodal_llm_config:
            from backend.core.llm.factory import LLMFactory
            try:
                multimodal_llm_instance = LLMFactory.create_llm(
                    provider=request.multimodal_llm_config.get("provider", "deepseek"),
                    model=request.multimodal_llm_config.get("model_name", "deepseek-flash")
                )
            except Exception as e:
                print(f"警告: 创建多模态LLM失败: {e}")

        # 启动研究
        result = await research_service.start_research(
            query=request.query,
            user_id=user_id,
            research_type=request.research_type,
            sources=request.sources,
            include_images=request.include_images,
            llm_provider=llm_provider,
            multimodal_llm_instance=multimodal_llm_instance,
            session_id=request.session_id
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "启动研究失败"))

        return ResearchResponse(**result)

    except HTTPException:
        raise
    except Exception:
        logger.exception("Research request failed")
        raise HTTPException(status_code=500, detail="启动研究时出错，请重试")


@router.get("/status/{session_id}", response_model=ResearchStatusResponse)
async def get_research_status(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取研究状态（需要认证并验证会话访问权限）
    """
    try:
        # 如果提供了用户信息，验证访问权限
        if current_user:
            user_id = current_user["user_id"]
            has_access = await research_service.validate_session_access(session_id, user_id)
            if not has_access:
                raise HTTPException(status_code=403, detail="无权访问此研究会话")

        # 获取状态
        status = await research_service.get_research_status(session_id)

        return ResearchStatusResponse(
            success=True,
            session_id=session_id,
            status_data=status,
            message="获取状态成功"
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Research request failed")
        raise HTTPException(status_code=500, detail="获取研究状态时出错，请重试")


@router.post("/interrupt/{session_id}")
async def interrupt_research(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    中断研究会话
    """
    try:
        # 从认证的用户信息中获取用户ID
        user_id = current_user["user_id"]

        # 验证访问权限
        has_access = await research_service.validate_session_access(session_id, user_id)
        if not has_access:
            raise HTTPException(status_code=403, detail="无权访问此研究会话")

        # 中断研究
        result = await research_service.interrupt_research(session_id)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "中断研究失败"))

        return result

    except HTTPException:
        raise
    except Exception:
        logger.exception("Research request failed")
        raise HTTPException(status_code=500, detail="中断研究时出错，请重试")


@router.post("/resume/{session_id}")
async def resume_research(
    session_id: str,
    state_data: Optional[Dict[str, Any]] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    恢复被中断的研究
    """
    try:
        # 从认证的用户信息中获取用户ID
        user_id = current_user["user_id"]

        # 验证访问权限
        has_access = await research_service.validate_session_access(session_id, user_id)
        if not has_access:
            raise HTTPException(status_code=403, detail="无权访问此研究会话")

        # 恢复研究
        result = await research_service.resume_research(session_id, state_data)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "恢复研究失败"))

        return result

    except HTTPException:
        raise
    except Exception:
        logger.exception("Research request failed")
        raise HTTPException(status_code=500, detail="恢复研究时出错，请重试")


@router.get("/sessions", response_model=ResearchListResponse)
async def get_user_sessions(
    status: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    user_id: Optional[str] = Query(None, description="用户ID（可选，用于过滤特定用户的会话）"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取研究会话列表（仅当前用户）
    如果提供了user_id参数，则只返回该用户的会话
    """
    try:
        user_id = scoped_user_id(user_id, current_user)

        # 获取会话列表
        sessions = await research_service.get_user_sessions(
            user_id=user_id,
            status=status,
            limit=limit
        )

        return ResearchListResponse(
            success=True,
            sessions=sessions,
            total=len(sessions),
            message="获取会话列表成功"
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Research request failed")
        raise HTTPException(status_code=500, detail="获取会话列表时出错，请重试")


@router.get("/export/{session_id}", response_model=ResearchExportResponse)
async def export_session_data(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    导出会话数据（需要认证并验证会话访问权限）
    """
    try:
        # 如果提供了用户信息，验证访问权限
        if current_user:
            user_id = current_user["user_id"]
            has_access = await research_service.validate_session_access(session_id, user_id)
            if not has_access:
                raise HTTPException(status_code=403, detail="无权访问此研究会话")

        # 导出数据
        data = await research_service.export_session_data(session_id)

        if not data:
            raise HTTPException(status_code=404, detail="会话数据不存在")

        # 构建响应（直接返回字典，让 FastAPI 处理）
        return {
            "success": True,
            "session_id": session_id,
            "data": data,
            "exported_at": data.get("exported_at", datetime.utcnow().isoformat()),
            "message": "导出数据成功"
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Research request failed")
        raise HTTPException(status_code=500, detail="导出会话数据时出错，请重试")


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    删除研究会话
    """
    try:
        # 从认证的用户信息中获取用户ID
        user_id = current_user["user_id"]

        # 验证访问权限
        has_access = await research_service.validate_session_access(session_id, user_id)
        if not has_access:
            raise HTTPException(status_code=403, detail="无权访问此研究会话")

        # 删除会话
        result = await research_service.delete_session(session_id)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "删除会话失败"))

        return result

    except HTTPException:
        raise
    except Exception:
        logger.exception("Research request failed")
        raise HTTPException(status_code=500, detail="删除会话时出错，请重试")


@router.get("/search")
async def search_research_content(
    query: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: Optional[str] = Query(None, description="用户ID（可选，用于过滤特定用户的内容）"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    搜索研究内容（仅当前用户）
    如果提供了user_id参数，则只搜索该用户的内容
    """
    try:
        user_id = scoped_user_id(user_id, current_user)

        # 搜索内容
        results = await research_service.search_research_content(
            query=query,
            user_id=user_id,
            limit=limit
        )

        return {
            "success": True,
            "query": query,
            "results": results,
            "total": len(results),
            "message": "搜索完成"
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Research request failed")
        raise HTTPException(status_code=500, detail="搜索研究内容时出错，请重试")


@router.get("/statistics")
async def get_research_statistics(
    user_id: Optional[str] = Query(None, description="用户ID（可选，用于获取特定用户的统计）"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取研究统计信息（仅当前用户）
    如果提供了user_id参数，则返回该用户的统计；仅返回当前用户统计
    """
    try:
        user_id = scoped_user_id(user_id, current_user)
        stats = await research_service.get_research_statistics(user_id=user_id)

        return {
            "success": True,
            "statistics": stats,
            "scope": "user",
            "message": "获取统计信息成功"
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Research request failed")
        raise HTTPException(status_code=500, detail="获取研究统计时出错，请重试")


@router.post("/cleanup")
async def cleanup_inactive_sessions(
    inactive_hours: int = Query(default=24, ge=1, le=168),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    清理非活跃会话（仅管理员）
    """
    try:
        # 只有管理员可以执行清理操作
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="权限不足：仅管理员可执行此操作")

        # 执行清理
        result = await research_service.cleanup_inactive_sessions(inactive_hours)

        return result

    except HTTPException:
        raise
    except Exception:
        logger.exception("Research request failed")
        raise HTTPException(status_code=500, detail="清理非活跃会话时出错，请重试")


async def research_events(session_id: str):
    """Yield bounded progress and exactly one terminal event."""
    yield {"type": "connected", "session_id": session_id}
    try:
        async with asyncio.timeout(STREAM_TIMEOUT_SECONDS):
            previous_status = None
            while True:
                status_data = await research_service.get_research_status(session_id)
                status = status_data.get("status")
                if status != previous_status:
                    yield {"type": "status_update", "status": status, "data": status_data}
                    previous_status = status
                if status == "completed":
                    export = await research_service.export_session_data(session_id)
                    if not export:
                        yield {"type": "error", "status": "error", "error": "报告数据不可用"}
                        return
                    report = await research_service.format_final_report(session_id, export)
                    citations = export.get("citations", [])
                    yield {
                        "type": "completed", "status": "completed",
                        "data": {
                            "report_text": research_service.generate_full_report_text(report),
                            "session_id": session_id,
                            "chat_session_id": export.get("session_info", {}).get("chat_session_id"),
                            "metadata": {
                                "type": "research", "session_id": session_id,
                                "evidence": citation_evidence(citations), "citations": citations,
                            },
                        },
                    }
                    return
                if status in TERMINAL_STATUSES:
                    message = "研究已中断，可稍后恢复" if status == "interrupted" else "研究未能完成，请重试"
                    yield {"type": "error", "status": status, "error": message}
                    return
                yield {"type": "heartbeat"}
                await asyncio.sleep(3)
    except TimeoutError:
        yield {"type": "error", "status": "timeout", "error": "进度连接已超时，请重新连接"}
    except Exception:
        logger.exception("Research stream failed")
        yield {"type": "error", "status": "error", "error": "读取研究进度失败，请重试"}


@router.get("/stream/{session_id}")
async def stream_research_progress(
    session_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    await require_session_access(session_id, current_user)

    async def event_generator():
        async for event in research_events(session_id):
            if await request.is_disconnected():
                return
            yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"

    return StreamingResponse(
        event_generator(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.websocket("/ws/progress/{session_id}")
async def websocket_research_progress(websocket: WebSocket, session_id: str):
    # Browsers authenticate in the first frame so tokens never enter URLs/logs.
    await websocket.accept()
    try:
        authorization = websocket.headers.get("authorization")
        if not authorization:
            first_message = await asyncio.wait_for(websocket.receive_json(), timeout=10)
            token = first_message.get("token") if isinstance(first_message, dict) else None
            if not isinstance(token, str) or not token:
                await websocket.close(code=1008)
                return
            authorization = f"Bearer {token}"
        current_user = await get_current_user(authorization)
        await require_session_access(session_id, current_user)
        async for event in research_events(session_id):
            await websocket.send_json(event)
        await websocket.close(code=1000)
    except WebSocketDisconnect:
        return
    except (HTTPException, TimeoutError, ValueError):
        await websocket.close(code=1008)
    except Exception:
        logger.exception("Research WebSocket failed")
        await websocket.close(code=1011)
