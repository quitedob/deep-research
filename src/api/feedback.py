# -*- coding: utf-8 -*-
"""
用户反馈 API 端点
提供 AI 响应质量反馈功能
"""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import require_auth
from ..api.errors import create_error_response, ErrorCodes, handle_database_error, handle_not_found_error, APIException
from ..sqlmodel.models import User, MessageFeedback, ConversationMessage
from ..core.db import get_async_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


# ==================== 请求/响应模型 ====================

class FeedbackCreateRequest(BaseModel):
    """创建反馈请求"""
    message_id: str
    rating: int  # 1 = 👍 (赞), -1 = 👎 (踩)
    comment: Optional[str] = None
    feedback_type: Optional[str] = None  # quality, relevance, helpfulness
    context: Optional[dict] = None  # 额外上下文信息

    class Config:
        from_attributes = True


class FeedbackResponse(BaseModel):
    """反馈响应"""
    id: int
    message_id: str
    user_id: str
    rating: int
    comment: Optional[str]
    created_at: datetime
    updated_at: datetime
    feedback_type: Optional[str]
    context: Optional[dict]

    class Config:
        from_attributes = True


class FeedbackStatsResponse(BaseModel):
    """反馈统计响应"""
    total_feedbacks: int
    positive_feedbacks: int
    negative_feedbacks: int
    average_rating: float
    feedback_by_type: dict
    recent_feedbacks: List[FeedbackResponse]


# ==================== 权限检查 ====================

async def require_authenticated_user(current_user: User = Depends(require_auth)) -> User:
    """要求已认证用户"""
    return current_user


# ==================== 反馈管理端点 ====================

@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackCreateRequest,
    current_user: User = Depends(require_authenticated_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    提交对AI回复的反馈

    - **message_id**: 消息ID
    - **rating**: 评分（1=赞，-1=踩）
    - **comment**: 可选评论
    - **feedback_type**: 反馈类型
    """
    try:
        # 验证评分值
        if request.rating not in [1, -1]:
            raise APIException(
                code=ErrorCodes.VALIDATION_ERROR,
                message="评分必须是1（赞）或-1（踩）",
                status_code=400
            )

        # 验证消息是否存在且属于用户
        message_result = await session.execute(
            select(ConversationMessage)
            .join(ConversationSession, ConversationMessage.session_id == ConversationSession.id)
            .where(
                and_(
                    ConversationMessage.id == request.message_id,
                    ConversationSession.user_id == current_user.id
                )
            )
        )
        message = message_result.scalar_one_or_none()

        if not message:
            raise APIException(
                code=ErrorCodes.NOT_FOUND,
                message="消息不存在或无权限访问",
                status_code=404
            )

        # 检查是否已经提交过反馈
        existing_feedback_result = await session.execute(
            select(MessageFeedback)
            .where(
                and_(
                    MessageFeedback.message_id == request.message_id,
                    MessageFeedback.user_id == current_user.id
                )
            )
        )
        existing_feedback = existing_feedback_result.scalar_one_or_none()

        if existing_feedback:
            # 更新现有反馈
            existing_feedback.rating = request.rating
            existing_feedback.comment = request.comment
            existing_feedback.feedback_type = request.feedback_type
            existing_feedback.context = request.context
            existing_feedback.updated_at = datetime.utcnow()

            await session.commit()
            await session.refresh(existing_feedback)

            logger.info(f"用户 {current_user.id} 更新了消息 {request.message_id} 的反馈")

            return FeedbackResponse.from_orm(existing_feedback)

        # 创建新反馈
        feedback = MessageFeedback(
            message_id=request.message_id,
            user_id=current_user.id,
            rating=request.rating,
            comment=request.comment,
            feedback_type=request.feedback_type,
            context=request.context
        )

        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)

        logger.info(f"用户 {current_user.id} 提交了对消息 {request.message_id} 的反馈: {request.rating}")

        return FeedbackResponse.from_orm(feedback)

    except APIException:
        raise
    except Exception as e:
        logger.error(f"提交反馈失败: {e}")
        await session.rollback()
        return handle_database_error(e)


@router.get("/message/{message_id}")
async def get_message_feedback(
    message_id: str,
    current_user: User = Depends(require_authenticated_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取指定消息的反馈"""
    try:
        # 验证消息访问权限
        message_result = await session.execute(
            select(ConversationMessage)
            .join(ConversationSession, ConversationMessage.session_id == ConversationSession.id)
            .where(
                and_(
                    ConversationMessage.id == message_id,
                    ConversationSession.user_id == current_user.id
                )
            )
        )
        message = message_result.scalar_one_or_none()

        if not message:
            raise APIException(
                code=ErrorCodes.NOT_FOUND,
                message="消息不存在或无权限访问",
                status_code=404
            )

        # 获取反馈
        feedback_result = await session.execute(
            select(MessageFeedback)
            .where(MessageFeedback.message_id == message_id)
            .order_by(MessageFeedback.created_at.desc())
        )
        feedbacks = feedback_result.scalars().all()

        return {
            "message_id": message_id,
            "total_feedbacks": len(feedbacks),
            "positive_feedbacks": sum(1 for f in feedbacks if f.rating == 1),
            "negative_feedbacks": sum(1 for f in feedbacks if f.rating == -1),
            "feedbacks": [FeedbackResponse.from_orm(f) for f in feedbacks]
        }

    except APIException:
        raise
    except Exception as e:
        logger.error(f"获取消息反馈失败: {e}")
        return handle_database_error(e)


@router.get("/user/stats", response_model=FeedbackStatsResponse)
async def get_user_feedback_stats(
    current_user: User = Depends(require_authenticated_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取用户的反馈统计"""
    try:
        # 总反馈数
        total_result = await session.execute(
            select(func.count(MessageFeedback.id))
            .where(MessageFeedback.user_id == current_user.id)
        )
        total_feedbacks = total_result.scalar()

        # 正面和负面反馈数
        positive_result = await session.execute(
            select(func.count(MessageFeedback.id))
            .where(
                and_(
                    MessageFeedback.user_id == current_user.id,
                    MessageFeedback.rating == 1
                )
            )
        )
        positive_feedbacks = positive_result.scalar()

        negative_result = await session.execute(
            select(func.count(MessageFeedback.id))
            .where(
                and_(
                    MessageFeedback.user_id == current_user.id,
                    MessageFeedback.rating == -1
                )
            )
        )
        negative_feedbacks = negative_result.scalar()

        # 计算平均评分
        average_rating = 0.0
        if total_feedbacks > 0:
            rating_result = await session.execute(
                select(func.avg(MessageFeedback.rating))
                .where(MessageFeedback.user_id == current_user.id)
            )
            average_rating = float(rating_result.scalar() or 0.0)

        # 按类型统计
        type_stats_result = await session.execute(
            select(
                MessageFeedback.feedback_type,
                func.count(MessageFeedback.id).label('count'),
                func.avg(MessageFeedback.rating).label('avg_rating')
            )
            .where(
                and_(
                    MessageFeedback.user_id == current_user.id,
                    MessageFeedback.feedback_type.isnot(None)
                )
            )
            .group_by(MessageFeedback.feedback_type)
        )
        type_stats = {
            row.feedback_type: {
                "count": row.count,
                "average_rating": float(row.avg_rating or 0.0)
            }
            for row in type_stats_result.fetchall()
        }

        # 最近反馈
        recent_result = await session.execute(
            select(MessageFeedback)
            .where(MessageFeedback.user_id == current_user.id)
            .order_by(MessageFeedback.created_at.desc())
            .limit(10)
        )
        recent_feedbacks = [FeedbackResponse.from_orm(f) for f in recent_result.scalars().all()]

        return FeedbackStatsResponse(
            total_feedbacks=total_feedbacks,
            positive_feedbacks=positive_feedbacks,
            negative_feedbacks=negative_feedbacks,
            average_rating=average_rating,
            feedback_by_type=type_stats,
            recent_feedbacks=recent_feedbacks
        )

    except Exception as e:
        logger.error(f"获取用户反馈统计失败: {e}")
        return handle_database_error(e)


@router.get("/global/stats")
async def get_global_feedback_stats(
    current_user: User = Depends(require_authenticated_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取全局反馈统计（管理员权限）"""
    if current_user.role != "admin":
        raise APIException(
            code=ErrorCodes.FORBIDDEN,
            message="需要管理员权限",
            status_code=403
        )

    try:
        # 总反馈数
        total_result = await session.execute(
            select(func.count(MessageFeedback.id))
        )
        total_feedbacks = total_result.scalar()

        # 正面和负面反馈数
        positive_result = await session.execute(
            select(func.count(MessageFeedback.id))
            .where(MessageFeedback.rating == 1)
        )
        positive_feedbacks = positive_result.scalar()

        negative_result = await session.execute(
            select(func.count(MessageFeedback.id))
            .where(MessageFeedback.rating == -1)
        )
        negative_feedbacks = negative_result.scalar()

        # 计算平均评分
        average_rating = 0.0
        if total_feedbacks > 0:
            rating_result = await session.execute(
                select(func.avg(MessageFeedback.rating))
            )
            average_rating = float(rating_result.scalar() or 0.0)

        # 按日期统计（最近7天）
        from datetime import timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        daily_stats_result = await session.execute(
            select(
                func.date(MessageFeedback.created_at).label('date'),
                func.count(MessageFeedback.id).label('total'),
                func.count(MessageFeedback.id).filter(MessageFeedback.rating == 1).label('positive'),
                func.count(MessageFeedback.id).filter(MessageFeedback.rating == -1).label('negative')
            )
            .where(MessageFeedback.created_at >= seven_days_ago)
            .group_by(func.date(MessageFeedback.created_at))
            .order_by(func.date(MessageFeedback.created_at))
        )
        daily_stats = [
            {
                "date": str(row.date),
                "total": row.total,
                "positive": row.positive,
                "negative": row.negative,
                "rating": (row.positive - row.negative) / max(row.total, 1)
            }
            for row in daily_stats_result.fetchall()
        ]

        return {
            "summary": {
                "total_feedbacks": total_feedbacks,
                "positive_feedbacks": positive_feedbacks,
                "negative_feedbacks": negative_feedbacks,
                "average_rating": average_rating,
                "positive_rate": positive_feedbacks / max(total_feedbacks, 1) * 100,
                "period_days": 7
            },
            "daily_stats": daily_stats
        }

    except Exception as e:
        logger.error(f"获取全局反馈统计失败: {e}")
        return handle_database_error(e)


@router.delete("/message/{message_id}")
async def delete_feedback(
    message_id: str,
    current_user: User = Depends(require_authenticated_user),
    session: AsyncSession = Depends(get_async_session)
):
    """删除对消息的反馈"""
    try:
        # 验证消息访问权限
        message_result = await session.execute(
            select(ConversationMessage)
            .join(ConversationSession, ConversationMessage.session_id == ConversationSession.id)
            .where(
                and_(
                    ConversationMessage.id == message_id,
                    ConversationSession.user_id == current_user.id
                )
            )
        )
        message = message_result.scalar_one_or_none()

        if not message:
            raise APIException(
                code=ErrorCodes.NOT_FOUND,
                message="消息不存在或无权限访问",
                status_code=404
            )

        # 删除反馈
        delete_result = await session.execute(
            MessageFeedback.__table__.delete()
            .where(
                and_(
                    MessageFeedback.message_id == message_id,
                    MessageFeedback.user_id == current_user.id
                )
            )
        )
        deleted_count = delete_result.rowcount

        await session.commit()

        if deleted_count == 0:
            return {"message": "没有找到要删除的反馈"}

        logger.info(f"用户 {current_user.id} 删除了对消息 {message_id} 的反馈")

        return {"message": "反馈已删除"}

    except APIException:
        raise
    except Exception as e:
        logger.error(f"删除反馈失败: {e}")
        await session.rollback()
        return handle_database_error(e)