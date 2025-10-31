# -*- coding: utf-8 -*-
"""
SQLModel 数据库模型定义
包含所有核心数据模型，支持异步CRUD操作
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlmodel import SQLModel, Field, Relationship


class MessageRole(str, Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class ConversationMode(str, Enum):
    """对话模式枚举"""
    CHAT = "chat"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    CODING = "coding"


class RAGStatus(str, Enum):
    """RAG状态枚举"""
    DISABLED = "disabled"
    ENABLED = "enabled"
    ACTIVE = "active"


# 基础模型
class Base(SQLModel):
    """基础模型类"""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": func.now()}
    )


# 用户模型
class User(Base, table=True):
    """用户模型"""
    __tablename__ = "users"

    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)

    # 关联
    conversations: List["ConversationSession"] = Relationship(back_populates="user")

    # 索引
    __table_args__ = (
        Index("ix_users_username", "username"),
        Index("ix_users_email", "email"),
        Index("ix_users_is_active", "is_active"),
    )


# 对话会话模型 - 增强版
class ConversationSession(Base, table=True):
    """对话会话模型 - 增强版，包含 AgentScope 相关字段"""
    __tablename__ = "conversation_sessions"

    # 基础字段
    user_id: str = Field(index=True)
    title: str = Field(max_length=200)
    last_message: Optional[str] = Field(default=None, max_length=500)

    # AgentScope 增强字段
    message_count: int = Field(default=0, description="消息总数")
    conversation_mode: ConversationMode = Field(
        default=ConversationMode.CHAT,
        description="对话模式"
    )
    rag_status: RAGStatus = Field(
        default=RAGStatus.DISABLED,
        description="RAG状态"
    )

    # AgentScope 状态管理
    enable_clarification: bool = Field(
        default=False,
        description="是否启用澄清功能"
    )
    clarification_rounds: int = Field(
        default=0,
        description="澄清轮次数"
    )
    max_clarification_rounds: int = Field(
        default=3,
        description="最大澄清轮次数"
    )

    # 长期记忆状态
    enable_long_term_memory: bool = Field(
        default=False,
        description="是否启用长期记忆"
    )
    memory_summary: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="对话记忆摘要"
    )

    # 性能指标
    total_tokens: int = Field(default=0, description="总token数")
    total_cost: float = Field(default=0.0, description="总成本")
    average_response_time: float = Field(default=0.0, description="平均响应时间")

    # 元数据
    metadata_: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="额外元数据"
    )

    # 关联
    user: Optional[User] = Relationship(back_populates="conversations")
    messages: List["ConversationMessage"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"order_by": "ConversationMessage.created_at"}
    )

    # 索引优化
    __table_args__ = (
        Index("ix_conversation_sessions_user_id", "user_id"),
        Index("ix_conversation_sessions_created_at", "created_at"),
        Index("ix_conversation_sessions_updated_at", "updated_at"),
        Index("ix_conversation_sessions_mode", "conversation_mode"),
        Index("ix_conversation_sessions_rag_status", "rag_status"),
        Index("ix_conversation_sessions_enable_clarification", "enable_clarification"),
    )


# 对话消息模型 - 增强版
class ConversationMessage(Base, table=True):
    """对话消息模型 - 增强版，包含 AgentScope 相关字段"""
    __tablename__ = "conversation_messages"

    # 基础字段
    session_id: str = Field(
        sa_column=Column(String, ForeignKey("conversation_sessions.id", ondelete="CASCADE")),
        index=True
    )
    role: MessageRole
    content: str = Field(sa_column=Column(Text))
    message_type: str = Field(default="text", max_length=50)

    # AgentScope 增强字段
    token_count: Optional[int] = Field(default=None, description="消息token数")
    cost: Optional[float] = Field(default=None, description="消息成本")
    response_time: Optional[float] = Field(default=None, description="响应时间(秒)")

    # 工具调用相关
    tool_calls: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="工具调用信息"
    )
    tool_results: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="工具调用结果"
    )

    # 澄清相关
    is_clarification_question: bool = Field(
        default=False,
        description="是否为澄清问题"
    )
    clarification_round: Optional[int] = Field(
        default=None,
        description="澄清轮次"
    )

    # 思维链相关
    reasoning_steps: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="推理步骤"
    )
    confidence_score: Optional[float] = Field(
        default=None,
        description="置信度分数"
    )

    # 长期记忆相关
    memory_importance: Optional[float] = Field(
        default=None,
        description="记忆重要性评分"
    )
    memory_tags: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="记忆标签"
    )

    # 元数据
    metadata_: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="额外元数据"
    )

    # 关联
    session: Optional[ConversationSession] = Relationship(back_populates="messages")

    # 索引优化
    __table_args__ = (
        Index("ix_conversation_messages_session_id", "session_id"),
        Index("ix_conversation_messages_created_at", "created_at"),
        Index("ix_conversation_messages_role", "role"),
        Index("ix_conversation_messages_message_type", "message_type"),
        Index("ix_conversation_messages_is_clarification_question", "is_clarification_question"),
        Index("ix_conversation_messages_clarification_round", "clarification_round"),
    )


# 长期记忆模型
class MemorySummary(Base, table=True):
    """记忆摘要模型"""
    __tablename__ = "memory_summaries"

    session_id: str = Field(index=True)
    user_id: str = Field(index=True)
    summary_text: str = Field(sa_column=Column(Text))
    key_points: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="关键点列表"
    )
    time_range_start: Optional[datetime] = Field(default=None)
    time_range_end: Optional[datetime] = Field(default=None)

    # 索引
    __table_args__ = (
        Index("ix_memory_summaries_session_id", "session_id"),
        Index("ix_memory_summaries_user_id", "user_id"),
        Index("ix_memory_summaries_created_at", "created_at"),
    )


class MemoryKeypoint(Base, table=True):
    """记忆关键点模型"""
    __tablename__ = "memory_keypoints"

    session_id: str = Field(index=True)
    user_id: str = Field(index=True)
    keypoint_text: str = Field(sa_column=Column(Text))
    importance_score: float = Field(default=0.5)
    category: Optional[str] = Field(default=None, max_length=100)
    tags: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON)
    )

    # 索引
    __table_args__ = (
        Index("ix_memory_keypoints_session_id", "session_id"),
        Index("ix_memory_keypoints_user_id", "user_id"),
        Index("ix_memory_keypoints_importance_score", "importance_score"),
        Index("ix_memory_keypoints_category", "category"),
    )


class MemoryIndex(Base, table=True):
    """记忆索引模型"""
    __tablename__ = "memory_index"

    session_id: str = Field(index=True)
    user_id: str = Field(index=True)
    content_hash: str = Field(unique=True, max_length=64)
    content_preview: str = Field(max_length=500)
    vector_embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="向量嵌入"
    )
    metadata_: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON)
    )

    # 索引
    __table_args__ = (
        Index("ix_memory_index_session_id", "session_id"),
        Index("ix_memory_index_user_id", "user_id"),
        Index("ix_memory_index_content_hash", "content_hash"),
    )


# 监控数据模型
class ConversationSnapshot(Base, table=True):
    """对话状态快照模型"""
    __tablename__ = "conversation_snapshots"

    session_id: str = Field(index=True)
    user_id: str = Field(index=True)
    snapshot_type: str = Field(max_length=50)  # "periodic", "milestone", "error"
    state_data: Dict[str, Any] = Field(sa_column=Column(JSON))
    performance_metrics: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON)
    )

    # 索引
    __table_args__ = (
        Index("ix_conversation_snapshots_session_id", "session_id"),
        Index("ix_conversation_snapshots_user_id", "user_id"),
        Index("ix_conversation_snapshots_created_at", "created_at"),
        Index("ix_conversation_snapshots_snapshot_type", "snapshot_type"),
    )


class ModeSwitchHistory(Base, table=True):
    """模式切换历史模型"""
    __tablename__ = "mode_switch_history"

    session_id: str = Field(index=True)
    user_id: str = Field(index=True)
    from_mode: str = Field(max_length=50)
    to_mode: str = Field(max_length=50)
    trigger_reason: Optional[str] = Field(
        default=None,
        max_length=200,
        description="切换触发原因"
    )
    context_info: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="切换时的上下文信息"
    )

    # 索引
    __table_args__ = (
        Index("ix_mode_switch_history_session_id", "session_id"),
        Index("ix_mode_switch_history_user_id", "user_id"),
        Index("ix_mode_switch_history_created_at", "created_at"),
        Index("ix_mode_switch_history_from_mode", "from_mode"),
        Index("ix_mode_switch_history_to_mode", "to_mode"),
    )


class PerformanceMetric(Base, table=True):
    """性能指标记录模型"""
    __tablename__ = "performance_metrics"

    session_id: Optional[str] = Field(default=None, index=True)
    user_id: Optional[str] = Field(default=None, index=True)
    metric_type: str = Field(max_length=100)  # "response_time", "token_usage", "cost", etc.
    metric_value: float
    metric_unit: str = Field(max_length=50)  # "seconds", "tokens", "usd", etc.
    context_info: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="指标上下文信息"
    )

    # 索引
    __table_args__ = (
        Index("ix_performance_metrics_session_id", "session_id"),
        Index("ix_performance_metrics_user_id", "user_id"),
        Index("ix_performance_metrics_created_at", "created_at"),
        Index("ix_performance_metrics_metric_type", "metric_type"),
    )


# AgentScope 数据表
class AgentScopeSession(Base, table=True):
    """AgentScope 会话数据表"""
    __tablename__ = "agentscope_sessions"

    session_id: str = Field(unique=True, index=True)
    user_id: str = Field(index=True)
    agent_type: str = Field(max_length=100)
    session_data: Dict[str, Any] = Field(sa_column=Column(JSON))
    is_active: bool = Field(default=True)

    # 索引
    __table_args__ = (
        Index("ix_agentscope_sessions_session_id", "session_id"),
        Index("ix_agentscope_sessions_user_id", "user_id"),
        Index("ix_agentscope_sessions_agent_type", "agent_type"),
        Index("ix_agentscope_sessions_is_active", "is_active"),
    )
