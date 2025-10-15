# -*- coding: utf-8 -*-
"""
管理员 API 端点
提供用户管理、数据监控和系统管理功能
"""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import require_auth
from ..api.errors import create_error_response, ErrorCodes, handle_database_error, handle_not_found_error, APIException
from ..sqlmodel.models import User, AdminAuditLog
from ..core.db import get_async_session
from ..service.audit_service import AuditService, audit_admin_action, log_admin_action_dependency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# ==================== 请求/响应模型 ====================

class UserListResponse(BaseModel):
    """用户列表响应"""
    id: str
    username: str
    email: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserDetailResponse(BaseModel):
    """用户详情响应"""
    id: str
    username: str
    email: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    stripe_customer_id: Optional[str]
    
    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """用户统计响应"""
    total_users: int
    active_users: int
    admin_users: int
    subscribed_users: int
    free_users: int


class UserUpdateRequest(BaseModel):
    """用户更新请求"""
    is_active: Optional[bool] = None
    role: Optional[str] = None


class ConversationSessionResponse(BaseModel):
    """对话会话响应"""
    id: str
    user_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int
    
    class Config:
        from_attributes = True


class APIUsageResponse(BaseModel):
    """API使用记录响应"""
    id: int
    user_id: str
    endpoint_called: str
    timestamp: datetime
    extra: Optional[str]

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """审计日志响应"""
    id: int
    admin_user_id: str
    admin_username: Optional[str]
    action: str
    target_user_id: Optional[str]
    target_username: Optional[str]
    timestamp: datetime
    details: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    endpoint: Optional[str]
    status: str
    error_message: Optional[str]

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """审计日志列表响应"""
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int


# ==================== 权限检查 ====================

async def require_admin(current_user: User = Depends(require_auth)) -> User:
    """要求管理员权限"""
    if current_user.role != "admin":
        raise APIException(
            code=ErrorCodes.FORBIDDEN,
            message="需要管理员权限",
            status_code=403
        )
    return current_user


# ==================== 用户管理端点 ====================

@router.get("/users", response_model=List[UserListResponse])
async def list_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取所有用户列表
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数
    - **role**: 按角色筛选（free, subscribed, admin）
    - **is_active**: 按激活状态筛选
    """
    try:
        # 构建查询
        query = select(User)
        
        # 添加筛选条件
        conditions = []
        if role:
            conditions.append(User.role == role)
        if is_active is not None:
            conditions.append(User.is_active == is_active)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 添加分页
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        
        # 执行查询
        result = await session.execute(query)
        users = result.scalars().all()
        
        return [UserListResponse.from_orm(user) for user in users]
    
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        return handle_database_error(e)


@router.get("/users/{user_id}", response_model=UserDetailResponse)
@audit_admin_action(AuditService.ACTION_USER_VIEW, include_target=True)
async def get_user_detail(
    user_id: str,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """获取用户详细信息"""
    try:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return handle_not_found_error("用户", user_id)

        return UserDetailResponse.from_orm(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户详情失败: {e}")
        return handle_database_error(e)


@router.patch("/users/{user_id}")
@audit_admin_action(AuditService.ACTION_USER_UPDATE, include_target=True)
async def update_user(
    user_id: str,
    update_data: UserUpdateRequest,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """
    更新用户信息

    - **is_active**: 封禁/解封用户
    - **role**: 修改用户角色
    """
    try:
        # 查询用户
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return handle_not_found_error("用户", user_id)

        # 防止管理员封禁自己
        if user.id == current_admin.id and update_data.is_active is False:
            raise APIException(
                code=ErrorCodes.BUSINESS_LOGIC_ERROR,
                message="不能封禁自己",
                status_code=400
            )

        # 更新字段
        if update_data.is_active is not None:
            user.is_active = update_data.is_active

        if update_data.role is not None:
            if update_data.role not in ["free", "subscribed", "admin"]:
                raise APIException(
                    code=ErrorCodes.VALIDATION_ERROR,
                    message="无效的角色",
                    status_code=400
                )
            user.role = update_data.role

        await session.commit()
        await session.refresh(user)

        return {
            "success": True,
            "message": "用户信息已更新",
            "user": UserDetailResponse.from_orm(user)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户失败: {e}")
        await session.rollback()
        return handle_database_error(e)


@router.post("/users/{user_id}/toggle-active")
@audit_admin_action(AuditService.ACTION_USER_BAN, include_target=True)
async def toggle_user_active(
    user_id: str,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """切换用户激活状态（封禁/解封）"""
    try:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return handle_not_found_error("用户", user_id)

        # 防止管理员封禁自己
        if user.id == current_admin.id:
            raise APIException(
                code=ErrorCodes.BUSINESS_LOGIC_ERROR,
                message="不能封禁自己",
                status_code=400
            )

        # 切换状态
        old_status = user.is_active
        user.is_active = not user.is_active
        await session.commit()
        await session.refresh(user)

        # 动态确定操作类型
        action = AuditService.ACTION_USER_UNBAN if user.is_active else AuditService.ACTION_USER_BAN

        # 手动记录详细的审计信息
        await AuditService.log_admin_action(
            session=session,
            admin_user_id=current_admin.id,
            action=action,
            target_user_id=user_id,
            details={
                "old_status": old_status,
                "new_status": user.is_active,
                "username": user.username
            },
            ip_address=current_admin.__dict__.get("ip_address"),
            user_agent=current_admin.__dict__.get("user_agent"),
            endpoint=f"POST /admin/users/{user_id}/toggle-active",
            status="success"
        )

        action_text = "解封" if user.is_active else "封禁"

        return {
            "success": True,
            "message": f"用户已{action_text}",
            "is_active": user.is_active
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换用户状态失败: {e}")
        await session.rollback()
        return handle_database_error(e)


# ==================== 统计端点 ====================

@router.get("/stats/users", response_model=UserStatsResponse)
async def get_user_stats(
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """获取用户统计信息"""
    try:
        # 总用户数
        total_result = await session.execute(select(func.count(User.id)))
        total_users = total_result.scalar()
        
        # 活跃用户数
        active_result = await session.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_result.scalar()
        
        # 管理员数
        admin_result = await session.execute(
            select(func.count(User.id)).where(User.role == "admin")
        )
        admin_users = admin_result.scalar()
        
        # 订阅用户数
        subscribed_result = await session.execute(
            select(func.count(User.id)).where(User.role == "subscribed")
        )
        subscribed_users = subscribed_result.scalar()
        
        # 免费用户数
        free_result = await session.execute(
            select(func.count(User.id)).where(User.role == "free")
        )
        free_users = free_result.scalar()
        
        return UserStatsResponse(
            total_users=total_users,
            active_users=active_users,
            admin_users=admin_users,
            subscribed_users=subscribed_users,
            free_users=free_users
        )
    
    except Exception as e:
        logger.error(f"获取用户统计失败: {e}")
        return handle_database_error(e)


# ==================== 对话记录端点 ====================

@router.get("/users/{user_id}/conversations")
async def get_user_conversations(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """获取指定用户的对话记录"""
    try:
        # 验证用户存在
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return handle_not_found_error("用户", user_id)
        
        # 导入对话模型
        from ..sqlmodel.models import ConversationSession, ConversationMessage
        
        # 查询对话会话
        query = select(ConversationSession).where(
            ConversationSession.user_id == user_id
        ).order_by(ConversationSession.updated_at.desc()).offset(skip).limit(limit)
        
        result = await session.execute(query)
        sessions = result.scalars().all()
        
        # 获取每个会话的消息数量
        sessions_with_count = []
        for sess in sessions:
            count_result = await session.execute(
                select(func.count(ConversationMessage.id)).where(
                    ConversationMessage.session_id == sess.id
                )
            )
            message_count = count_result.scalar()
            
            sessions_with_count.append({
                "id": str(sess.id),
                "user_id": str(sess.user_id),
                "title": sess.title,
                "created_at": sess.created_at,
                "updated_at": sess.updated_at,
                "message_count": message_count
            })
        
        return {
            "user_id": user_id,
            "username": user.username,
            "total_sessions": len(sessions_with_count),
            "sessions": sessions_with_count
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户对话记录失败: {e}")
        return handle_database_error(e)


# ==================== API 使用记录端点 ====================

@router.get("/users/{user_id}/api-usage", response_model=List[APIUsageResponse])
async def get_user_api_usage(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """获取指定用户的 API 使用记录"""
    try:
        # 验证用户存在
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return handle_not_found_error("用户", user_id)
        
        # 导入 API 使用日志模型
        from ..sqlmodel.models import APIUsageLog
        
        # 查询 API 使用记录
        query = select(APIUsageLog).where(
            APIUsageLog.user_id == user_id
        ).order_by(APIUsageLog.timestamp.desc()).offset(skip).limit(limit)
        
        result = await session.execute(query)
        usage_logs = result.scalars().all()
        
        return [APIUsageResponse.from_orm(log) for log in usage_logs]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 API 使用记录失败: {e}")
        return handle_database_error(e)


# ==================== 文档处理任务端点 ====================

@router.get("/users/{user_id}/documents")
async def get_user_documents(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """获取指定用户的文档处理任务"""
    try:
        # 验证用户存在
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return handle_not_found_error("用户", user_id)
        
        # 导入文档处理任务模型
        from ..sqlmodel.models import DocumentProcessingJob
        
        # 查询文档处理任务
        query = select(DocumentProcessingJob).where(
            DocumentProcessingJob.user_id == user_id
        ).order_by(DocumentProcessingJob.created_at.desc()).offset(skip).limit(limit)
        
        result = await session.execute(query)
        jobs = result.scalars().all()
        
        return {
            "user_id": user_id,
            "username": user.username,
            "total_jobs": len(jobs),
            "jobs": [
                {
                    "id": str(job.id),
                    "filename": job.filename,
                    "status": job.status,
                    "created_at": job.created_at,
                    "updated_at": job.updated_at,
                    "error_message": job.error_message
                }
                for job in jobs
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档处理任务失败: {e}")
        return handle_database_error(e)


# ==================== 研究报告端点 ====================

@router.get("/research-reports")
async def get_all_research_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """获取所有研究报告"""
    try:
        # 导入文档块模型
        from ..sqlmodel.models import DocumentChunk
        
        # 查询所有文档块（研究报告存储在这里）
        query = select(DocumentChunk).order_by(
            DocumentChunk.created_at.desc()
        ).offset(skip).limit(limit)
        
        result = await session.execute(query)
        chunks = result.scalars().all()
        
        # 按文档分组
        documents = {}
        for chunk in chunks:
            doc_id = chunk.document_id
            if doc_id not in documents:
                documents[doc_id] = {
                    "document_id": doc_id,
                    "chunks": [],
                    "total_chunks": 0,
                    "created_at": chunk.created_at
                }
            
            documents[doc_id]["chunks"].append({
                "id": str(chunk.id),
                "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                "chunk_index": chunk.chunk_index
            })
            documents[doc_id]["total_chunks"] += 1
        
        return {
            "total_documents": len(documents),
            "documents": list(documents.values())
        }
    
    except Exception as e:
        logger.error(f"获取研究报告失败: {e}")
        return handle_database_error(e)


@router.get("/research-reports/{document_id}")
async def get_research_report_detail(
    document_id: str,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """获取研究报告详情"""
    try:
        from ..sqlmodel.models import DocumentChunk
        
        # 查询文档的所有块
        query = select(DocumentChunk).where(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index)
        
        result = await session.execute(query)
        chunks = result.scalars().all()
        
        if not chunks:
            return handle_not_found_error("研究报告", document_id)
        
        # 合并所有块的内容
        full_content = "\n\n".join([chunk.content for chunk in chunks])
        
        return {
            "document_id": document_id,
            "total_chunks": len(chunks),
            "content": full_content,
            "chunks": [
                {
                    "id": str(chunk.id),
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "metadata": chunk.metadata
                }
                for chunk in chunks
            ],
            "created_at": chunks[0].created_at if chunks else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取研究报告详情失败: {e}")
        return handle_database_error(e)


# ==================== 订阅管理端点 ====================

@router.get("/subscriptions")
async def get_all_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = Query(None),
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """获取所有订阅记录"""
    try:
        from ..sqlmodel.models import Subscription
        
        # 构建查询
        query = select(Subscription)
        
        if status:
            query = query.where(Subscription.status == status)
        
        query = query.order_by(Subscription.created_at.desc()).offset(skip).limit(limit)
        
        result = await session.execute(query)
        subscriptions = result.scalars().all()
        
        # 获取用户信息
        subscriptions_with_user = []
        for sub in subscriptions:
            user_result = await session.execute(
                select(User).where(User.id == sub.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            subscriptions_with_user.append({
                "id": str(sub.id),
                "user_id": str(sub.user_id),
                "username": user.username if user else "Unknown",
                "stripe_subscription_id": sub.stripe_subscription_id,
                "status": sub.status,
                "current_period_start": sub.current_period_start,
                "current_period_end": sub.current_period_end,
                "created_at": sub.created_at
            })
        
        return {
            "total": len(subscriptions_with_user),
            "subscriptions": subscriptions_with_user
        }
    
    except Exception as e:
        logger.error(f"获取订阅记录失败: {e}")
        return handle_database_error(e)


@router.patch("/subscriptions/{subscription_id}")
async def update_subscription(
    subscription_id: str,
    status: str,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """更新订阅状态"""
    try:
        from ..sqlmodel.models import Subscription
        
        # 查询订阅
        result = await session.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return handle_not_found_error("订阅", subscription_id)
        
        # 验证状态
        valid_statuses = ["active", "canceled", "past_due", "unpaid"]
        if status not in valid_statuses:
            raise APIException(
                code=ErrorCodes.VALIDATION_ERROR,
                message=f"无效的状态。有效值: {valid_statuses}",
                status_code=400
            )
        
        # 更新状态
        subscription.status = status
        await session.commit()
        await session.refresh(subscription)
        
        return {
            "success": True,
            "message": "订阅状态已更新",
            "subscription": {
                "id": str(subscription.id),
                "status": subscription.status
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新订阅状态失败: {e}")
        await session.rollback()
        return handle_database_error(e)


# ==================== 审计日志端点 ====================

@router.get("/audit-logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    admin_user_id: Optional[str] = Query(None, description="管理员ID筛选"),
    action: Optional[str] = Query(None, description="操作类型筛选"),
    target_user_id: Optional[str] = Query(None, description="目标用户ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """获取审计日志列表"""
    try:
        # 计算偏移量
        offset = (page - 1) * page_size

        # 获取审计日志
        logs, total = await AuditService.get_audit_logs(
            session=session,
            admin_user_id=admin_user_id,
            action=action,
            target_user_id=target_user_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=page_size,
            offset=offset
        )

        # 补充用户信息
        log_responses = []
        for log in logs:
            # 获取管理员用户名
            admin_username = None
            if log.admin_user_id:
                admin_result = await session.execute(
                    select(User.username).where(User.id == log.admin_user_id)
                )
                admin_username = admin_result.scalar()

            # 获取目标用户名
            target_username = None
            if log.target_user_id:
                target_result = await session.execute(
                    select(User.username).where(User.id == log.target_user_id)
                )
                target_username = target_result.scalar()

            log_response = AuditLogResponse(
                id=log.id,
                admin_user_id=log.admin_user_id,
                admin_username=admin_username,
                action=log.action,
                target_user_id=log.target_user_id,
                target_username=target_username,
                timestamp=log.timestamp,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                endpoint=log.endpoint,
                status=log.status,
                error_message=log.error_message
            )
            log_responses.append(log_response)

        return AuditLogListResponse(
            logs=log_responses,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"获取审计日志失败: {e}")
        return handle_database_error(e)


@router.get("/audit-logs/summary")
async def get_audit_log_summary(
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    """获取审计日志统计摘要"""
    try:
        from sqlalchemy import select, func, and_
        from datetime import datetime, timedelta

        # 获取过去30天的数据
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        # 总操作数
        total_ops_result = await session.execute(
            select(func.count(AdminAuditLog.id))
            .where(AdminAuditLog.timestamp >= thirty_days_ago)
        )
        total_operations = total_ops_result.scalar()

        # 按操作类型统计
        action_stats_result = await session.execute(
            select(
                AdminAuditLog.action,
                func.count(AdminAuditLog.id).label('count')
            )
            .where(AdminAuditLog.timestamp >= thirty_days_ago)
            .group_by(AdminAuditLog.action)
            .order_by(func.count(AdminAuditLog.id).desc())
        )
        action_stats = action_stats_result.fetchall()

        # 按状态统计
        status_stats_result = await session.execute(
            select(
                AdminAuditLog.status,
                func.count(AdminAuditLog.id).label('count')
            )
            .where(AdminAuditLog.timestamp >= thirty_days_ago)
            .group_by(AdminAuditLog.status)
        )
        status_stats = status_stats_result.fetchall()

        # 活跃管理员统计
        active_admins_result = await session.execute(
            select(func.count(func.distinct(AdminAuditLog.admin_user_id)))
            .where(AdminAuditLog.timestamp >= thirty_days_ago)
        )
        active_admins = active_admins_result.scalar()

        # 最近7天每日操作数
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        daily_ops_result = await session.execute(
            select(
                func.date(AdminAuditLog.timestamp).label('date'),
                func.count(AdminAuditLog.id).label('count')
            )
            .where(AdminAuditLog.timestamp >= seven_days_ago)
            .group_by(func.date(AdminAuditLog.timestamp))
            .order_by(func.date(AdminAuditLog.timestamp))
        )
        daily_ops = daily_ops_result.fetchall()

        return {
            "summary": {
                "total_operations_30_days": total_operations,
                "active_admins_30_days": active_admins,
                "period_days": 30
            },
            "action_breakdown": [
                {"action": row.action, "count": row.count}
                for row in action_stats
            ],
            "status_breakdown": [
                {"status": row.status, "count": row.count}
                for row in status_stats
            ],
            "daily_operations": [
                {"date": str(row.date), "count": row.count}
                for row in daily_ops
            ]
        }

    except Exception as e:
        logger.error(f"获取审计日志统计失败: {e}")
        return handle_database_error(e)


# ==================== 系统健康检查 ====================

@router.get("/health")
@audit_admin_action(AuditService.ACTION_SYSTEM_HEALTH_CHECK, include_target=False)
async def system_health_check(
    current_admin: User = Depends(require_admin)
):
    """系统健康检查"""
    try:
        from ..core.db_init import check_database_health

        # 数据库健康检查
        db_health = await check_database_health()

        # LLM 提供商健康检查
        llm_health = {}
        try:
            from ..llms.router import SmartModelRouter
            from pathlib import Path

            router = SmartModelRouter.from_conf(Path("conf.yaml"))
            llm_health = router.health()
        except Exception as e:
            logger.error(f"LLM 健康检查失败: {e}")
            llm_health = {"error": str(e)}

        # OCR 服务健康检查
        ocr_health = {}
        try:
            from ..services.ocr_service import get_ocr_service
            ocr_service = get_ocr_service()
            ocr_health = {
                "available": ocr_service.doubao_provider is not None,
                "provider": "doubao"
            }
        except Exception as e:
            logger.error(f"OCR 健康检查失败: {e}")
            ocr_health = {"error": str(e)}

        return {
            "status": "healthy" if db_health["healthy"] else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": db_health,
                "llm": llm_health,
                "ocr": ocr_health
            }
        }

    except Exception as e:
        logger.error(f"系统健康检查失败: {e}")
        return handle_database_error(e)
