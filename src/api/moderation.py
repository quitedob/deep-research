# -*- coding: utf-8 -*-
"""
内容审核管理 API 端点
提供内容举报、审核和管理功能
"""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import require_auth, require_admin
from ..api.errors import create_error_response, ErrorCodes, handle_database_error, handle_not_found_error, APIException
from ..sqlmodel.models import User, ModerationQueue, ConversationMessage, ConversationSession
from ..core.db import get_async_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/moderation", tags=["moderation"])


# ==================== 请求/响应模型 ====================

class ContentReportRequest(BaseModel):
    """内容举报请求"""
    message_id: str
    report_reason: str  # spam, harassment, violence, inappropriate_content, misinformation, other
    report_description: Optional[str] = None
    context_data: Optional[dict] = None

    class Config:
        from_attributes = True


class ModerationQueueResponse(BaseModel):
    """审核队列响应"""
    id: int
    message_id: str
    reporter_user_id: str
    reported_user_id: Optional[str]
    report_reason: str
    report_description: Optional[str]
    status: str
    priority: str
    reviewer_admin_id: Optional[str]
    review_notes: Optional[str]
    action_taken: Optional[str]
    created_at: datetime
    reviewed_at: Optional[datetime]
    resolved_at: Optional[datetime]
    context_data: Optional[dict]

    # 关联数据
    message_content: Optional[str] = None
    reporter_username: Optional[str] = None
    reported_username: Optional[str] = None
    reviewer_admin_username: Optional[str] = None
    session_title: Optional[str] = None

    class Config:
        from_attributes = True


class ModerationActionRequest(BaseModel):
    """审核操作请求"""
    action: str  # warning, message_deleted, user_suspended, user_banned, dismiss
    review_notes: Optional[str] = None
    priority_change: Optional[str] = None  # low, medium, high, urgent

    class Config:
        from_attributes = True


class ModerationStatsResponse(BaseModel):
    """审核统计响应"""
    total_reports: int
    pending_reports: int
    reviewing_reports: int
    resolved_reports: int
    dismissed_reports: int
    reports_by_reason: dict
    reports_by_priority: dict
    recent_reports: List[ModerationQueueResponse]


# ==================== 权限检查 ====================

async def require_authenticated_user(current_user: User = Depends(require_auth)) -> User:
    """要求已认证用户"""
    return current_user


async def require_admin_user(current_user: User = Depends(require_admin)) -> User:
    """要求管理员权限"""
    return current_user


# ==================== 内容举报端点 ====================

@router.post("/report", response_model=ModerationQueueResponse)
async def report_content(
    request: ContentReportRequest,
    current_user: User = Depends(require_authenticated_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    举报内容

    - **message_id**: 被举报的消息ID
    - **report_reason**: 举报原因类型
    - **report_description**: 详细描述（可选）
    """
    try:
        # 验证举报原因
        valid_reasons = ['spam', 'harassment', 'violence', 'inappropriate_content', 'misinformation', 'other']
        if request.report_reason not in valid_reasons:
            raise APIException(
                code=ErrorCodes.VALIDATION_ERROR,
                message=f"无效的举报原因。有效选项: {', '.join(valid_reasons)}",
                status_code=400
            )

        # 验证消息是否存在且用户有权限访问
        message_result = await session.execute(
            select(ConversationMessage)
            .join(ConversationSession, ConversationMessage.session_id == ConversationSession.id)
            .where(
                ConversationMessage.id == request.message_id
            )
        )
        message = message_result.scalar_one_or_none()

        if not message:
            raise APIException(
                code=ErrorCodes.NOT_FOUND,
                message="消息不存在",
                status_code=404
            )

        # 检查是否已经举报过
        existing_report_result = await session.execute(
            select(ModerationQueue)
            .where(
                and_(
                    ModerationQueue.message_id == request.message_id,
                    ModerationQueue.reporter_user_id == current_user.id,
                    ModerationQueue.status.in_(['pending', 'reviewing'])
                )
            )
        )
        existing_report = existing_report_result.scalar_one_or_none()

        if existing_report:
            raise APIException(
                code=ErrorCodes.CONFLICT,
                message="您已经举报过此内容，该举报正在处理中",
                status_code=409
            )

        # 获取被举报用户ID
        reported_user_id = None
        if message.role != 'system':
            # 通过会话获取消息发送者
            session_result = await session.execute(
                select(ConversationSession).where(ConversationSession.id == message.session_id)
            )
            conversation_session = session_result.scalar_one_or_none()
            if conversation_session:
                reported_user_id = conversation_session.user_id

        # 确定优先级
        priority = 'medium'
        if request.report_reason in ['violence', 'harassment']:
            priority = 'high'
        elif request.report_reason == 'spam':
            priority = 'low'

        # 创建举报记录
        report = ModerationQueue(
            message_id=request.message_id,
            reporter_user_id=current_user.id,
            reported_user_id=reported_user_id,
            report_reason=request.report_reason,
            report_description=request.report_description,
            priority=priority,
            context_data=request.context_data or {
                "message_content": message.content[:500],  # 保存前500字符作为上下文
                "message_role": message.role,
                "report_timestamp": datetime.utcnow().isoformat()
            }
        )

        session.add(report)
        await session.commit()
        await session.refresh(report)

        # 构建响应数据
        response_data = await _build_moderation_response(session, report)

        logger.info(f"用户 {current_user.id} 举报了消息 {request.message_id}，原因: {request.report_reason}")

        return response_data

    except APIException:
        raise
    except Exception as e:
        logger.error(f"内容举报失败: {e}")
        await session.rollback()
        return handle_database_error(e)


@router.get("/my-reports", response_model=List[ModerationQueueResponse])
async def get_my_reports(
    status: Optional[str] = Query(None, description="按状态筛选"),
    limit: int = Query(20, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(require_authenticated_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取我的举报记录"""
    try:
        query = select(ModerationQueue).where(ModerationQueue.reporter_user_id == current_user.id)

        if status:
            valid_statuses = ['pending', 'reviewing', 'resolved', 'dismissed']
            if status not in valid_statuses:
                raise APIException(
                    code=ErrorCodes.VALIDATION_ERROR,
                    message=f"无效的状态。有效选项: {', '.join(valid_statuses)}",
                    status_code=400
                )
            query = query.where(ModerationQueue.status == status)

        query = query.order_by(ModerationQueue.created_at.desc()).limit(limit).offset(offset)

        result = await session.execute(query)
        reports = result.scalars().all()

        # 构建响应数据
        response_data = []
        for report in reports:
            response_data.append(await _build_moderation_response(session, report))

        return response_data

    except APIException:
        raise
    except Exception as e:
        logger.error(f"获取举报记录失败: {e}")
        return handle_database_error(e)


# ==================== 管理员审核端点 ====================

@router.get("/admin/queue", response_model=List[ModerationQueueResponse])
async def get_moderation_queue(
    status: Optional[str] = Query(None, description="按状态筛选"),
    priority: Optional[str] = Query(None, description="按优先级筛选"),
    reason: Optional[str] = Query(None, description="按举报原因筛选"),
    limit: int = Query(50, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取审核队列（管理员权限）"""
    try:
        query = select(ModerationQueue)

        if status:
            valid_statuses = ['pending', 'reviewing', 'resolved', 'dismissed']
            if status not in valid_statuses:
                raise APIException(
                    code=ErrorCodes.VALIDATION_ERROR,
                    message=f"无效的状态。有效选项: {', '.join(valid_statuses)}",
                    status_code=400
                )
            query = query.where(ModerationQueue.status == status)

        if priority:
            valid_priorities = ['low', 'medium', 'high', 'urgent']
            if priority not in valid_priorities:
                raise APIException(
                    code=ErrorCodes.VALIDATION_ERROR,
                    message=f"无效的优先级。有效选项: {', '.join(valid_priorities)}",
                    status_code=400
                )
            query = query.where(ModerationQueue.priority == priority)

        if reason:
            valid_reasons = ['spam', 'harassment', 'violence', 'inappropriate_content', 'misinformation', 'other']
            if reason not in valid_reasons:
                raise APIException(
                    code=ErrorCodes.VALIDATION_ERROR,
                    message=f"无效的举报原因。有效选项: {', '.join(valid_reasons)}",
                    status_code=400
                )
            query = query.where(ModerationQueue.report_reason == reason)

        query = query.order_by(
            ModerationQueue.priority.desc(),
            ModerationQueue.created_at.desc()
        ).limit(limit).offset(offset)

        result = await session.execute(query)
        reports = result.scalars().all()

        # 构建响应数据
        response_data = []
        for report in reports:
            response_data.append(await _build_moderation_response(session, report))

        return response_data

    except APIException:
        raise
    except Exception as e:
        logger.error(f"获取审核队列失败: {e}")
        return handle_database_error(e)


@router.post("/admin/{report_id}/review", response_model=ModerationQueueResponse)
async def review_report(
    report_id: int,
    request: ModerationActionRequest,
    current_user: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """审核举报（管理员权限）"""
    try:
        # 验证操作类型
        valid_actions = ['warning', 'message_deleted', 'user_suspended', 'user_banned', 'dismiss']
        if request.action not in valid_actions:
            raise APIException(
                code=ErrorCodes.VALIDATION_ERROR,
                message=f"无效的操作类型。有效选项: {', '.join(valid_actions)}",
                status_code=400
            )

        # 获取举报记录
        result = await session.execute(
            select(ModerationQueue).where(ModerationQueue.id == report_id)
        )
        report = result.scalar_one_or_none()

        if not report:
            raise APIException(
                code=ErrorCodes.NOT_FOUND,
                message="举报记录不存在",
                status_code=404
            )

        if report.status not in ['pending', 'reviewing']:
            raise APIException(
                code=ErrorCodes.CONFLICT,
                message="该举报已被处理",
                status_code=409
            )

        # 更新举报记录
        report.status = 'resolved' if request.action != 'dismiss' else 'dismissed'
        report.reviewer_admin_id = current_user.id
        report.review_notes = request.review_notes
        report.action_taken = request.action
        report.reviewed_at = datetime.utcnow()
        report.resolved_at = datetime.utcnow()

        if request.priority_change:
            valid_priorities = ['low', 'medium', 'high', 'urgent']
            if request.priority_change in valid_priorities:
                report.priority = request.priority_change

        # 执行相应操作
        await _execute_moderation_action(session, request.action, report, current_user)

        await session.commit()
        await session.refresh(report)

        # 构建响应数据
        response_data = await _build_moderation_response(session, report)

        logger.info(f"管理员 {current_user.id} 审核了举报 {report_id}，操作: {request.action}")

        return response_data

    except APIException:
        raise
    except Exception as e:
        logger.error(f"审核举报失败: {e}")
        await session.rollback()
        return handle_database_error(e)


@router.get("/admin/stats", response_model=ModerationStatsResponse)
async def get_moderation_stats(
    current_user: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """获取审核统计（管理员权限）"""
    try:
        # 总举报数
        total_result = await session.execute(
            select(func.count(ModerationQueue.id))
        )
        total_reports = total_result.scalar()

        # 按状态统计
        status_result = await session.execute(
            select(
                ModerationQueue.status,
                func.count(ModerationQueue.id).label('count')
            )
            .group_by(ModerationQueue.status)
        )
        status_counts = {row.status: row.count for row in status_result.fetchall()}

        # 按原因统计
        reason_result = await session.execute(
            select(
                ModerationQueue.report_reason,
                func.count(ModerationQueue.id).label('count')
            )
            .group_by(ModerationQueue.report_reason)
        )
        reason_counts = {row.report_reason: row.count for row in reason_result.fetchall()}

        # 按优先级统计
        priority_result = await session.execute(
            select(
                ModerationQueue.priority,
                func.count(ModerationQueue.id).label('count')
            )
            .group_by(ModerationQueue.priority)
        )
        priority_counts = {row.priority: row.count for row in priority_result.fetchall()}

        # 最近举报
        recent_result = await session.execute(
            select(ModerationQueue)
            .order_by(ModerationQueue.created_at.desc())
            .limit(10)
        )
        recent_reports_raw = recent_result.scalars().all()

        # 构建最近举报响应数据
        recent_reports = []
        for report in recent_reports_raw:
            recent_reports.append(await _build_moderation_response(session, report))

        return ModerationStatsResponse(
            total_reports=total_reports,
            pending_reports=status_counts.get('pending', 0),
            reviewing_reports=status_counts.get('reviewing', 0),
            resolved_reports=status_counts.get('resolved', 0),
            dismissed_reports=status_counts.get('dismissed', 0),
            reports_by_reason=reason_counts,
            reports_by_priority=priority_counts,
            recent_reports=recent_reports
        )

    except Exception as e:
        logger.error(f"获取审核统计失败: {e}")
        return handle_database_error(e)


# ==================== 辅助函数 ====================

async def _build_moderation_response(session: AsyncSession, report: ModerationQueue) -> ModerationQueueResponse:
    """构建审核响应数据"""
    # 获取消息内容
    message_content = None
    session_title = None
    if report.message_id:
        message_result = await session.execute(
            select(ConversationMessage, ConversationSession)
            .join(ConversationSession, ConversationMessage.session_id == ConversationSession.id)
            .where(ConversationMessage.id == report.message_id)
        )
        message_data = message_result.first()
        if message_data:
            message, conversation_session = message_data
            message_content = message.content
            session_title = conversation_session.title

    # 获取举报人用户名
    reporter_username = None
    if report.reporter_user_id:
        reporter_result = await session.execute(
            select(User.username).where(User.id == report.reporter_user_id)
        )
        reporter_username = reporter_result.scalar()

    # 获取被举报人用户名
    reported_username = None
    if report.reported_user_id:
        reported_result = await session.execute(
            select(User.username).where(User.id == report.reported_user_id)
        )
        reported_username = reported_result.scalar()

    # 获取审核管理员用户名
    reviewer_admin_username = None
    if report.reviewer_admin_id:
        reviewer_result = await session.execute(
            select(User.username).where(User.id == report.reviewer_admin_id)
        )
        reviewer_admin_username = reviewer_result.scalar()

    return ModerationQueueResponse(
        id=report.id,
        message_id=report.message_id,
        reporter_user_id=report.reporter_user_id,
        reported_user_id=report.reported_user_id,
        report_reason=report.report_reason,
        report_description=report.report_description,
        status=report.status,
        priority=report.priority,
        reviewer_admin_id=report.reviewer_admin_id,
        review_notes=report.review_notes,
        action_taken=report.action_taken,
        created_at=report.created_at,
        reviewed_at=report.reviewed_at,
        resolved_at=report.resolved_at,
        context_data=report.context_data,
        message_content=message_content,
        reporter_username=reporter_username,
        reported_username=reported_username,
        reviewer_admin_username=reviewer_admin_username,
        session_title=session_title
    )


async def _execute_moderation_action(
    session: AsyncSession,
    action: str,
    report: ModerationQueue,
    admin_user: User
):
    """执行审核操作"""
    try:
        if action == 'message_deleted':
            # 删除消息
            if report.message_id:
                delete_result = await session.execute(
                    ConversationMessage.__table__.delete()
                    .where(ConversationMessage.id == report.message_id)
                )
                logger.info(f"管理员 {admin_user.id} 删除了消息 {report.message_id}")

        elif action in ['user_suspended', 'user_banned']:
            # 封禁用户
            if report.reported_user_id:
                new_status = 'suspended' if action == 'user_suspended' else False
                await session.execute(
                    User.__table__.update()
                    .where(User.id == report.reported_user_id)
                    .values(is_active=new_status)
                )
                logger.info(f"管理员 {admin_user.id} {'暂停' if action == 'user_suspended' else '封禁'}了用户 {report.reported_user_id}")

        elif action == 'warning':
            # 警告用户（这里可以扩展为发送通知）
            logger.info(f"管理员 {admin_user.id} 对用户 {report.reported_user_id} 发出了警告")

        elif action == 'dismiss':
            # 驳回举报，无需额外操作
            logger.info(f"管理员 {admin_user.id} 驳回了举报 {report.id}")

    except Exception as e:
        logger.error(f"执行审核操作失败: {e}")
        # 不抛出异常，让主流程继续
        pass