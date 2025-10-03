# -*- coding: utf-8 -*-
"""
证据链 API：提供研究过程中的证据追踪和可视化
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from pydantic import BaseModel

from ..sqlmodel.models import User
from ..sqlmodel.rag_models import Evidence
from ..service.auth import get_current_user
from src.core.db import get_db_session

router = APIRouter(tags=["evidence"])


class EvidenceResponse(BaseModel):
    """证据响应模型"""
    id: int
    source_type: str
    source_url: Optional[str]
    source_title: Optional[str]
    content: str
    snippet: Optional[str]
    relevance_score: Optional[float]
    confidence_score: Optional[float]
    citation_text: Optional[str]
    used_in_response: bool
    metadata: Optional[Dict[str, Any]]
    created_at: str


class EvidenceTraceResponse(BaseModel):
    """证据链追踪响应"""
    conversation_id: Optional[str]
    research_session_id: Optional[str]
    total_evidence: int
    evidence_by_type: Dict[str, int]
    evidence_list: List[EvidenceResponse]


@router.get("/conversation/{conversation_id}")
async def get_conversation_evidence(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> EvidenceTraceResponse:
    """获取对话的证据链"""
    try:
        # 查询证据总数
        count_stmt = select(func.count(Evidence.id)).where(
            Evidence.conversation_id == conversation_id
        )
        total_result = await db.execute(count_stmt)
        total_evidence = total_result.scalar() or 0
        
        # 查询证据列表
        stmt = (
            select(Evidence)
            .where(Evidence.conversation_id == conversation_id)
            .order_by(desc(Evidence.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(stmt)
        evidence_records = result.scalars().all()
        
        # 统计各类型证据数量
        type_count_stmt = (
            select(Evidence.source_type, func.count(Evidence.id))
            .where(Evidence.conversation_id == conversation_id)
            .group_by(Evidence.source_type)
        )
        type_result = await db.execute(type_count_stmt)
        evidence_by_type = dict(type_result.fetchall())
        
        # 转换为响应格式
        evidence_list = []
        for evidence in evidence_records:
            evidence_response = EvidenceResponse(
                id=evidence.id,
                source_type=evidence.source_type,
                source_url=evidence.source_url,
                source_title=evidence.source_title,
                content=evidence.content,
                snippet=evidence.snippet,
                relevance_score=evidence.relevance_score,
                confidence_score=evidence.confidence_score,
                citation_text=evidence.citation_text,
                used_in_response=evidence.used_in_response,
                metadata=evidence.metadata,
                created_at=evidence.created_at.isoformat()
            )
            evidence_list.append(evidence_response)
        
        return EvidenceTraceResponse(
            conversation_id=conversation_id,
            research_session_id=None,
            total_evidence=total_evidence,
            evidence_by_type=evidence_by_type,
            evidence_list=evidence_list
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取证据链失败: {str(e)}")


@router.get("/research/{research_session_id}")
async def get_research_evidence(
    research_session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> EvidenceTraceResponse:
    """获取研究会话的证据链"""
    try:
        # 查询证据总数
        count_stmt = select(func.count(Evidence.id)).where(
            Evidence.research_session_id == research_session_id
        )
        total_result = await db.execute(count_stmt)
        total_evidence = total_result.scalar() or 0
        
        # 查询证据列表
        stmt = (
            select(Evidence)
            .where(Evidence.research_session_id == research_session_id)
            .order_by(desc(Evidence.relevance_score), desc(Evidence.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(stmt)
        evidence_records = result.scalars().all()
        
        # 统计各类型证据数量
        type_count_stmt = (
            select(Evidence.source_type, func.count(Evidence.id))
            .where(Evidence.research_session_id == research_session_id)
            .group_by(Evidence.source_type)
        )
        type_result = await db.execute(type_count_stmt)
        evidence_by_type = dict(type_result.fetchall())
        
        # 转换为响应格式
        evidence_list = []
        for evidence in evidence_records:
            evidence_response = EvidenceResponse(
                id=evidence.id,
                source_type=evidence.source_type,
                source_url=evidence.source_url,
                source_title=evidence.source_title,
                content=evidence.content,
                snippet=evidence.snippet,
                relevance_score=evidence.relevance_score,
                confidence_score=evidence.confidence_score,
                citation_text=evidence.citation_text,
                used_in_response=evidence.used_in_response,
                metadata=evidence.metadata,
                created_at=evidence.created_at.isoformat()
            )
            evidence_list.append(evidence_response)
        
        return EvidenceTraceResponse(
            conversation_id=None,
            research_session_id=research_session_id,
            total_evidence=total_evidence,
            evidence_by_type=evidence_by_type,
            evidence_list=evidence_list
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取研究证据链失败: {str(e)}")


@router.put("/evidence/{evidence_id}/mark_used")
async def mark_evidence_used(
    evidence_id: int,
    used: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """标记证据是否被使用"""
    try:
        # 查找证据记录
        stmt = select(Evidence).where(Evidence.id == evidence_id)
        result = await db.execute(stmt)
        evidence = result.scalar_one_or_none()
        
        if not evidence:
            raise HTTPException(status_code=404, detail="证据记录不存在")
        
        # 更新使用状态
        evidence.used_in_response = used
        await db.commit()
        
        return {"message": f"证据使用状态已更新为: {used}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新证据状态失败: {str(e)}")


@router.get("/stats")
async def get_evidence_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    days: int = Query(7, ge=1, le=30)
) -> Dict[str, Any]:
    """获取证据统计信息"""
    try:
        from datetime import datetime, timedelta
        
        # 计算时间范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 总证据数量
        total_stmt = select(func.count(Evidence.id)).where(
            Evidence.created_at >= start_date
        )
        total_result = await db.execute(total_stmt)
        total_evidence = total_result.scalar() or 0
        
        # 按类型统计
        type_stmt = (
            select(Evidence.source_type, func.count(Evidence.id))
            .where(Evidence.created_at >= start_date)
            .group_by(Evidence.source_type)
        )
        type_result = await db.execute(type_stmt)
        by_type = dict(type_result.fetchall())
        
        # 使用率统计
        used_stmt = select(func.count(Evidence.id)).where(
            Evidence.created_at >= start_date,
            Evidence.used_in_response == True
        )
        used_result = await db.execute(used_stmt)
        used_evidence = used_result.scalar() or 0
        
        usage_rate = (used_evidence / total_evidence * 100) if total_evidence > 0 else 0
        
        # 平均相关性评分
        avg_score_stmt = select(func.avg(Evidence.relevance_score)).where(
            Evidence.created_at >= start_date,
            Evidence.relevance_score.is_not(None)
        )
        avg_result = await db.execute(avg_score_stmt)
        avg_relevance_score = avg_result.scalar() or 0
        
        return {
            "period_days": days,
            "total_evidence": total_evidence,
            "used_evidence": used_evidence,
            "usage_rate": round(usage_rate, 2),
            "avg_relevance_score": round(float(avg_relevance_score), 3),
            "evidence_by_type": by_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取证据统计失败: {str(e)}")