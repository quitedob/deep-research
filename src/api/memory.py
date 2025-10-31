# -*- coding: utf-8 -*-
"""
记忆管理API
提供对话摘要查询和长期记忆管理功能
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import require_auth
from src.core.db import get_db_session
from src.sqlmodel.models import User
from src.services.memory_summarizer import get_memory_summarizer
from src.services.conversation_service import ConversationService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


class MemorySummaryResponse(BaseModel):
    """记忆摘要响应"""
    session_id: str
    user_id: str
    summary_text: str
    topics: List[str]
    key_points: List[str]
    user_preferences: dict
    message_count: int
    created_at: str
    metadata: dict


class GenerateSummaryRequest(BaseModel):
    """生成摘要请求"""
    session_id: str


@router.post("/summary/generate", response_model=MemorySummaryResponse)
async def generate_memory_summary(
    request: GenerateSummaryRequest,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """
    为指定会话生成记忆摘要
    """
    try:
        # 获取对话消息
        conversation_service = ConversationService(db)
        messages_result = await conversation_service.get_conversation_messages(
            user_id=str(current_user.id),
            session_id=request.session_id,
            limit=100
        )

        if not messages_result.get("success"):
            raise HTTPException(
                status_code=404,
                detail="会话不存在或无权限访问"
            )

        messages = messages_result.get("messages", [])

        if len(messages) < 5:
            raise HTTPException(
                status_code=400,
                detail="消息数量不足，至少需要5条消息才能生成摘要"
            )

        # 生成摘要
        summarizer = get_memory_summarizer()
        result = await summarizer.generate_summary(
            session_id=request.session_id,
            messages=messages,
            user_id=str(current_user.id)
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "生成摘要失败")
            )

        summary = result["summary"]

        return MemorySummaryResponse(**summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成记忆摘要失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{session_id}", response_model=MemorySummaryResponse)
async def get_memory_summary(
    session_id: str,
    current_user: User = Depends(require_auth)
):
    """
    获取指定会话的记忆摘要
    """
    try:
        summarizer = get_memory_summarizer()
        summary = await summarizer.get_summary(session_id)

        if not summary:
            raise HTTPException(
                status_code=404,
                detail=f"会话 {session_id} 的摘要不存在"
            )

        # 验证权限
        if summary.get("user_id") != str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail="无权限访问此摘要"
            )

        return MemorySummaryResponse(**summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取记忆摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summaries", response_model=List[MemorySummaryResponse])
async def get_all_memory_summaries(
    current_user: User = Depends(require_auth)
):
    """
    获取当前用户的所有记忆摘要
    """
    try:
        summarizer = get_memory_summarizer()
        summaries = await summarizer.get_all_summaries(str(current_user.id))

        return [MemorySummaryResponse(**s) for s in summaries]

    except Exception as e:
        logger.error(f"获取所有记忆摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/summary/{session_id}")
async def delete_memory_summary(
    session_id: str,
    current_user: User = Depends(require_auth)
):
    """
    删除指定会话的记忆摘要
    """
    try:
        summarizer = get_memory_summarizer()

        # 验证权限
        summary = await summarizer.get_summary(session_id)
        if summary and summary.get("user_id") != str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail="无权限删除此摘要"
            )

        success = await summarizer.delete_summary(session_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"会话 {session_id} 的摘要不存在"
            )

        return {
            "success": True,
            "message": "摘要已删除"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除记忆摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_memory_stats(
    current_user: User = Depends(require_auth)
):
    """
    获取用户的记忆统计信息
    """
    try:
        summarizer = get_memory_summarizer()
        summaries = await summarizer.get_all_summaries(str(current_user.id))

        # 统计信息
        total_summaries = len(summaries)
        total_messages = sum(s.get("message_count", 0) for s in summaries)

        # 提取所有主题
        all_topics = []
        for s in summaries:
            all_topics.extend(s.get("topics", []))

        # 主题频率统计
        from collections import Counter
        topic_frequency = Counter(all_topics)
        top_topics = [
            {"topic": topic, "count": count}
            for topic, count in topic_frequency.most_common(10)
        ]

        return {
            "total_summaries": total_summaries,
            "total_messages_summarized": total_messages,
            "top_topics": top_topics,
            "avg_messages_per_summary": total_messages / total_summaries if total_summaries > 0 else 0
        }

    except Exception as e:
        logger.error(f"获取记忆统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
