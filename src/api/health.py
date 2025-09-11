# -*- coding: utf-8 -*-
"""
健康检查和监控API
提供系统健康状态、性能指标和诊断信息
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..sqlmodel.models import User
from ..service.auth import get_current_user
from ..middleware.monitoring import get_health_status, get_metrics
from pkg.db import get_db_session
from src.config.logging import get_performance_monitor

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """
    基础健康检查
    返回系统整体健康状态
    """
    return await get_health_status()

@router.get("/detailed")
async def detailed_health_check(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    详细健康检查（需要管理员权限）
    返回系统各组件的详细状态
    """
    if current_user.role != "admin":
        return {"error": "需要管理员权限"}

    # 获取基础健康状态
    health_data = await get_health_status()

    # 添加数据库统计信息
    try:
        # 文档数量统计
        from sqlalchemy import func, select
        from ..sqlmodel.rag_models import Document, Chunk, Embedding, Evidence

        doc_count = await db.execute(select(func.count(Document.id)))
        chunk_count = await db.execute(select(func.count(Chunk.id)))
        embedding_count = await db.execute(select(func.count(Embedding.id)))
        evidence_count = await db.execute(select(func.count(Evidence.id)))

        health_data["database_stats"] = {
            "documents": doc_count.scalar(),
            "chunks": chunk_count.scalar(),
            "embeddings": embedding_count.scalar(),
            "evidence_records": evidence_count.scalar()
        }

    except Exception as e:
        health_data["database_stats"] = {"error": str(e)}

    # 添加队列统计
    try:
        from ..tasks.queue import get_task_queue
        queue = await get_task_queue()
        queue_stats = await queue.get_queue_stats()
        health_data["queue_stats"] = queue_stats
    except Exception as e:
        health_data["queue_stats"] = {"error": str(e)}

    # 添加模型路由统计
    try:
        from ..llms.router import get_router
        router = get_router()
        routing_stats = await router.get_routing_stats()
        health_data["routing_stats"] = routing_stats
    except Exception as e:
        health_data["routing_stats"] = {"error": str(e)}

    return health_data

@router.get("/metrics")
async def get_prometheus_metrics(current_user: User = Depends(get_current_user)):
    """
    Prometheus格式的监控指标（需要管理员权限）
    """
    if current_user.role != "admin":
        return {"error": "需要管理员权限"}

    return await get_metrics()

@router.get("/performance")
async def get_performance_stats(current_user: User = Depends(get_current_user)):
    """
    性能统计信息（需要管理员权限）
    """
    if current_user.role != "admin":
        return {"error": "需要管理员权限"}

    monitor = get_performance_monitor()
    return monitor.get_stats()

@router.get("/database")
async def get_database_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    数据库统计信息（需要管理员权限）
    """
    if current_user.role != "admin":
        return {"error": "需要管理员权限"}

    try:
        from sqlalchemy import func, select
        from ..sqlmodel.rag_models import Document, DocumentProcessingJob, Evidence

        # 基础统计
        stats = {}

        # 文档处理任务统计
        job_stats = await db.execute(
            select(
                func.count(DocumentProcessingJob.id),
                func.sum(DocumentProcessingJob.progress),
                DocumentProcessingJob.status
            )
            .group_by(DocumentProcessingJob.status)
        )
        stats["processing_jobs"] = dict(job_stats.fetchall())

        # 文档统计
        doc_count = await db.execute(select(func.count(Document.id)))
        stats["total_documents"] = doc_count.scalar()

        # 用户文档统计
        user_docs = await db.execute(
            select(Document.user_id, func.count(Document.id))
            .group_by(Document.user_id)
        )
        stats["documents_by_user"] = dict(user_docs.fetchall())

        # 证据统计
        evidence_stats = await db.execute(
            select(Evidence.source_type, func.count(Evidence.id))
            .group_by(Evidence.source_type)
        )
        stats["evidence_by_type"] = dict(evidence_stats.fetchall())

        # 最近活动
        recent_jobs = await db.execute(
            select(DocumentProcessingJob)
            .order_by(DocumentProcessingJob.created_at.desc())
            .limit(10)
        )
        stats["recent_jobs"] = [
            {
                "id": job.id,
                "filename": job.filename,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "user_id": job.user_id
            }
            for job in recent_jobs.scalars()
        ]

        return stats

    except Exception as e:
        return {"error": f"获取数据库统计失败: {str(e)}"}

@router.get("/system")
async def get_system_info(current_user: User = Depends(get_current_user)):
    """
    系统信息（需要管理员权限）
    """
    if current_user.role != "admin":
        return {"error": "需要管理员权限"}

    import psutil
    import platform
    from datetime import datetime

    try:
        # 系统信息
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": psutil.disk_usage('/')._asdict(),
            "uptime": datetime.now().timestamp() - psutil.boot_time()
        }

        # 进程信息
        process = psutil.Process()
        system_info["process"] = {
            "pid": process.pid,
            "cpu_percent": process.cpu_percent(),
            "memory_info": process.memory_info()._asdict(),
            "num_threads": process.num_threads(),
            "create_time": process.create_time()
        }

        return system_info

    except Exception as e:
        return {"error": f"获取系统信息失败: {str(e)}"}