# -*- coding: utf-8 -*-
"""
核心数据库模型：Users、Subscriptions、ApiUsageLog。
使用 SQLAlchemy 2.0 ORM，支持UUID主键和完整的Stripe集成。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    Text,
    Enum,
    func,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AgentConfiguration(Base):
    """智能体 LLM 配置模型"""
    __tablename__ = "agent_configurations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    agent_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    llm_provider: Mapped[str] = mapped_column(
        Enum('doubao', 'kimi', 'deepseek', 'ollama', 'zhipuai', name='llm_provider'),
        nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    updated_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # 关系定义
    updated_by_user: Mapped[Optional["User"]] = relationship(
        foreign_keys=[updated_by],
        back_populates="updated_agent_configs"
    )

    __table_args__ = (
        UniqueConstraint("agent_id", name="uq_agent_config_agent_id"),
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum('free', 'subscribed', 'admin', name='user_role'), 
        default='free', 
        nullable=False
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=func.now(), 
        nullable=False
    )

    # 关系定义
    subscriptions: Mapped[list[Subscription]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    api_usage_logs: Mapped[list[ApiUsageLog]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    conversation_sessions: Mapped[list[ConversationSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    updated_agent_configs: Mapped[list[AgentConfiguration]] = relationship(
        foreign_keys=[AgentConfiguration.updated_by],
        back_populates="updated_by_user"
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    stripe_subscription_id: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        index=True, 
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum('active', 'canceled', 'past_due', 'incomplete', name='subscription_status'), 
        default='inactive', 
        nullable=False
    )
    current_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    plan_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # 关系定义
    user: Mapped[User] = relationship(back_populates="subscriptions")

    __table_args__ = (
        UniqueConstraint("stripe_subscription_id", name="uq_subscription_stripe_id"),
    )


class ApiUsageLog(Base):
    __tablename__ = "api_usage_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    endpoint_called: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=func.now(), 
        index=True, 
        nullable=False
    )
    extra: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 关系定义
    user: Mapped[User] = relationship(back_populates="api_usage_logs")


# DocumentProcessingJob 已移至 rag_models.py



class ConversationSession(Base):
    """对话会话模型"""
    __tablename__ = "conversation_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # 关系定义
    user: Mapped[User] = relationship(back_populates="conversation_sessions")
    messages: Mapped[list[ConversationMessage]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan"
    )


class ConversationMessage(Base):
    """对话消息模型"""
    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    role: Mapped[str] = mapped_column(
        Enum('user', 'assistant', 'system', name='message_role'),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[Optional[str]] = mapped_column(String(50), default='text')
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False
    )

    # 关系定义
    session: Mapped[ConversationSession] = relationship(back_populates="messages")


# 更新User模型的关系定义
User.conversation_sessions: Mapped[list[ConversationSession]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan"
)


class AdminAuditLog(Base):
    """管理员操作审计日志"""
    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="执行操作的管理员ID"
    )
    action: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
        comment="操作类型"
    )
    target_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        comment="被操作的用户ID（如果适用）"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        index=True,
        nullable=False,
        comment="操作时间戳"
    )
    details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="操作详情（JSON格式）"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="操作者IP地址"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="用户代理字符串"
    )
    endpoint: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="API端点路径"
    )
    status: Mapped[str] = mapped_column(
        Enum('success', 'failed', 'partial', name='audit_status'),
        default='success',
        nullable=False,
        comment="操作状态"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息（如果操作失败）"
    )

    # 关系定义
    admin_user: Mapped[User] = relationship(
        foreign_keys=[admin_user_id],
        back_populates="audit_logs_as_admin"
    )
    target_user: Mapped[Optional[User]] = relationship(
        foreign_keys=[target_user_id],
        back_populates="audit_logs_as_target"
    )

    __table_args__ = (
        {"comment": "管理员操作审计日志表"},
    )


# 更新User模型添加审计日志关系
User.audit_logs_as_admin: Mapped[list[AdminAuditLog]] = relationship(
    foreign_keys=[AdminAuditLog.admin_user_id],
    back_populates="admin_user",
    cascade="all, delete-orphan"
)

User.audit_logs_as_target: Mapped[list[AdminAuditLog]] = relationship(
    foreign_keys=[AdminAuditLog.target_user_id],
    back_populates="target_user",
    cascade="all, delete-orphan"
)


class MessageFeedback(Base):
    """消息反馈模型"""
    __tablename__ = "message_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversation_messages.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="对话消息ID"
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="用户ID"
    )
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="反馈评分：1=👍(赞)，-1=👎(踩)"
    )
    comment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="用户评论（可选）"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        index=True,
        nullable=False,
        comment="反馈时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )
    feedback_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="反馈类型（如：quality, relevance, helpfulness）"
    )
    context: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="反馈上下文信息（如：对话主题、模型名称等）"
    )

    # 关系定义
    user: Mapped[User] = relationship(back_populates="feedback")
    message: Mapped[ConversationMessage] = relationship(back_populates="feedback")

    __table_args__ = (
        {"comment": "消息反馈表"},
    )


# 更新User模型添加反馈关系
User.feedback: Mapped[list[MessageFeedback]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan"
)

# 更新ConversationMessage模型添加反馈关系
ConversationMessage.feedback: Mapped[MessageFeedback] = relationship(
    back_populates="message",
    cascade="all, delete-orphan"
)


class ModerationQueue(Base):
    """内容审核队列模型"""
    __tablename__ = "moderation_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversation_messages.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="被举报的消息ID"
    )
    reporter_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="举报人用户ID"
    )
    reported_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        comment="被举报的用户ID（消息发送者）"
    )
    report_reason: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="举报原因类型"
    )
    report_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="举报详细描述"
    )
    status: Mapped[str] = mapped_column(
        Enum('pending', 'reviewing', 'resolved', 'dismissed', name='moderation_status'),
        default='pending',
        nullable=False,
        comment="审核状态"
    )
    priority: Mapped[str] = mapped_column(
        Enum('low', 'medium', 'high', 'urgent', name='moderation_priority'),
        default='medium',
        nullable=False,
        comment="优先级"
    )
    reviewer_admin_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        comment="审核管理员ID"
    )
    review_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="审核备注"
    )
    action_taken: Mapped[Optional[str]] = mapped_column(
        Enum('none', 'warning', 'message_deleted', 'user_suspended', 'user_banned', name='moderation_action'),
        default='none',
        nullable=True,
        comment="采取的措施"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        index=True,
        nullable=False,
        comment="举报时间"
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="审核时间"
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="解决时间"
    )
    context_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="上下文信息（如对话片段等）"
    )

    # 关系定义
    reporter: Mapped[User] = relationship(
        foreign_keys=[reporter_user_id],
        back_populates="reports_made"
    )
    reported_user: Mapped[Optional[User]] = relationship(
        foreign_keys=[reported_user_id],
        back_populates="reports_received"
    )
    reviewer_admin: Mapped[Optional[User]] = relationship(
        foreign_keys=[reviewer_admin_id],
        back_populates="moderation_reviews"
    )
    message: Mapped[ConversationMessage] = relationship(back_populates="moderation_reports")

    __table_args__ = (
        {"comment": "内容审核队列表"},
    )


# 更新User模型添加审核关系
User.reports_made: Mapped[list[ModerationQueue]] = relationship(
    foreign_keys=[ModerationQueue.reporter_user_id],
    back_populates="reporter",
    cascade="all, delete-orphan"
)

User.reports_received: Mapped[list[ModerationQueue]] = relationship(
    foreign_keys=[ModerationQueue.reported_user_id],
    back_populates="reported_user",
    cascade="all, delete-orphan"
)

User.moderation_reviews: Mapped[list[ModerationQueue]] = relationship(
    foreign_keys=[ModerationQueue.reviewer_admin_id],
    back_populates="reviewer_admin",
    cascade="all, delete-orphan"
)

# 更新ConversationMessage模型添加审核关系
ConversationMessage.moderation_reports: Mapped[list[ModerationQueue]] = relationship(
    back_populates="message",
    cascade="all, delete-orphan"
)

