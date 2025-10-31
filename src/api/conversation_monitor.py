# -*- coding: utf-8 -*-
"""
对话监控API
提供实时监控数据查询接口
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.deps import require_auth
from src.sqlmodel.models import User
from src.services.conversation_monitor import get_conversation_monitor
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitor", tags=["conversation_monitor"])


class SessionMetricsResponse(BaseModel):
    """会话指标响应"""
    session_id: str
    user_id: str
    message_count: int
    current_mode: str
    rag_searches: int
    network_searches: int
    mode_switches: int
    total_processing_time: float
    created_at: str
    last_activity: str


class GlobalMetricsResponse(BaseModel):
    """全局指标响应"""
    total_sessions: int
    total_messages: int
    rag_enhanced_sessions: int
    network_searches: int
    rag_searches: int
    mode_switches: int
    memory_summaries: int
    uptime_seconds: float
    active_sessions: int
    start_time: str
    performance: dict


class PerformanceStatsResponse(BaseModel):
    """性能统计响应"""
    stats: dict


@router.get("/sessions/{session_id}", response_model=SessionMetricsResponse)
async def get_session_metrics(
    session_id: str,
    current_user: User = Depends(require_auth)
):
    """获取指定会话的监控指标"""
    try:
        monitor = get_conversation_monitor()
        metrics = await monitor.get_session_metrics(session_id)

        if not metrics:
            raise HTTPException(
                status_code=404,
                detail=f"会话 {session_id} 的监控数据不存在"
            )

        return SessionMetricsResponse(**metrics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[SessionMetricsResponse])
async def get_all_sessions_metrics(
    current_user: User = Depends(require_auth)
):
    """获取所有会话的监控指标"""
    try:
        monitor = get_conversation_monitor()
        all_metrics = await monitor.get_all_sessions_metrics()

        return [SessionMetricsResponse(**m) for m in all_metrics]

    except Exception as e:
        logger.error(f"获取所有会话指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/global", response_model=GlobalMetricsResponse)
async def get_global_metrics(
    current_user: User = Depends(require_auth)
):
    """获取全局监控指标"""
    try:
        monitor = get_conversation_monitor()
        metrics = await monitor.get_global_metrics()

        return GlobalMetricsResponse(**metrics)

    except Exception as e:
        logger.error(f"获取全局指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance", response_model=PerformanceStatsResponse)
async def get_performance_stats(
    current_user: User = Depends(require_auth)
):
    """获取性能统计数据"""
    try:
        monitor = get_conversation_monitor()
        stats = await monitor.get_performance_stats()

        return PerformanceStatsResponse(stats=stats)

    except Exception as e:
        logger.error(f"获取性能统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_old_sessions(
    hours: int = 24,
    current_user: User = Depends(require_auth)
):
    """清理旧会话监控数据"""
    try:
        monitor = get_conversation_monitor()
        cleaned_count = await monitor.cleanup_old_sessions(hours)

        return {
            "success": True,
            "message": f"已清理 {cleaned_count} 个旧会话的监控数据",
            "cleaned_count": cleaned_count
        }

    except Exception as e:
        logger.error(f"清理旧会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_metrics(
    current_user: User = Depends(require_auth)
):
    """重置所有监控指标（需要管理员权限）"""
    try:
        # TODO: 添加管理员权限检查
        monitor = get_conversation_monitor()
        await monitor.reset_metrics()

        return {
            "success": True,
            "message": "监控指标已重置"
        }

    except Exception as e:
        logger.error(f"重置指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def monitor_health_check():
    """监控服务健康检查"""
    try:
        monitor = get_conversation_monitor()
        metrics = await monitor.get_global_metrics()

        return {
            "status": "healthy",
            "active_sessions": metrics["active_sessions"],
            "total_messages": metrics["total_messages"],
            "uptime_seconds": metrics["uptime_seconds"]
        }

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
