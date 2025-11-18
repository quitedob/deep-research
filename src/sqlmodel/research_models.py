#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
研究相关的SQLAlchemy模型
定义研究会话、发现、引用等数据模型
"""

from sqlalchemy import Column, String, Text, Float, DateTime, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.sqlmodel.models import Base


class ResearchSession(Base):
    """
    研究会话模型
    """
    __tablename__ = "research_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True, index=True)  # 允许匿名会话
    title = Column(String(500), nullable=False)
    status = Column(String(50), default="active", index=True)  # active, completed, interrupted, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # 关联关系
    findings = relationship("ResearchFinding", back_populates="session", cascade="all, delete-orphan")
    citations = relationship("ResearchCitation", back_populates="session", cascade="all, delete-orphan")
    memory_messages = relationship("ResearchMemory", back_populates="session", cascade="all, delete-orphan")


class ResearchFinding(Base):
    """
    研究发现模型
    """
    __tablename__ = "research_findings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("research_sessions.id"), nullable=False)
    source_type = Column(String(50), nullable=False, index=True)  # web, wiki, arxiv, image等
    source_url = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    relevance_score = Column(Float, default=0.8, index=True)
    metadata = Column(JSON, nullable=True)  # 额外的元数据
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    session = relationship("ResearchSession", back_populates="findings")


class ResearchCitation(Base):
    """
    研究引用模型
    """
    __tablename__ = "research_citations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("research_sessions.id"), nullable=False)
    title = Column(Text, nullable=False)
    authors = Column(JSON, nullable=False)  # 作者列表
    source_url = Column(Text, nullable=True)
    publication_year = Column(Integer, nullable=True)
    doi = Column(String(255), nullable=True, unique=True)
    citation_type = Column(String(50), default="article")  # article, book, conference等
    journal = Column(String(255), nullable=True)
    volume = Column(String(50), nullable=True)
    issue = Column(String(50), nullable=True)
    pages = Column(String(50), nullable=True)
    abstract = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    session = relationship("ResearchSession", back_populates="citations")


class ResearchMemory(Base):
    """
    研究记忆模型
    存储对话历史和长期记忆
    """
    __tablename__ = "research_memory"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("research_sessions.id"), nullable=False)
    message_role = Column(String(50), nullable=False)  # user, assistant, system
    message_name = Column(String(255), nullable=True)
    message_content = Column(Text, nullable=False)
    timestamp = Column(String(50), nullable=True)  # 原始时间戳
    message_type = Column(String(50), default="text")  # text, image, tool_call等
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    session = relationship("ResearchSession", back_populates="memory_messages")


class ResearchToolUsage(Base):
    """
    研究工具使用记录模型
    """
    __tablename__ = "research_tool_usage"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("research_sessions.id"), nullable=False)
    tool_name = Column(String(100), nullable=False, index=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    execution_time = Column(Float, nullable=True)  # 执行时间（秒）
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    session = relationship("ResearchSession")


class ResearchExport(Base):
    """
    研究导出记录模型
    """
    __tablename__ = "research_exports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("research_sessions.id"), nullable=False)
    export_format = Column(String(50), nullable=False)  # pdf, markdown, json, docx等
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)  # 文件大小（字节）
    export_data = Column(JSON, nullable=True)  # 导出的数据
    download_count = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)  # 过期时间
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    session = relationship("ResearchSession")


class ResearchFeedback(Base):
    """
    研究反馈模型
    """
    __tablename__ = "research_feedback"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("research_sessions.id"), nullable=False)
    user_id = Column(String, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5星评分
    feedback_text = Column(Text, nullable=True)
    feedback_type = Column(String(50), nullable=True)  # quality, accuracy, usefulness等
    suggestions = Column(JSON, nullable=True)  # 改进建议
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    session = relationship("ResearchSession")


# 创建索引的SQL语句
RESEARCH_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_research_sessions_user_id ON research_sessions(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_research_sessions_status ON research_sessions(status);",
    "CREATE INDEX IF NOT EXISTS idx_research_sessions_created_at ON research_sessions(created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_research_findings_session_id ON research_findings(session_id);",
    "CREATE INDEX IF NOT EXISTS idx_research_findings_source_type ON research_findings(source_type);",
    "CREATE INDEX IF NOT EXISTS idx_research_findings_relevance_score ON research_findings(relevance_score DESC);",
    "CREATE INDEX IF NOT EXISTS idx_research_citations_session_id ON research_citations(session_id);",
    "CREATE INDEX IF NOT EXISTS idx_research_citations_doi ON research_citations(doi);",
    "CREATE INDEX IF NOT EXISTS idx_research_citations_publication_year ON research_citations(publication_year DESC);",
    "CREATE INDEX IF NOT EXISTS idx_research_memory_session_id ON research_memory(session_id);",
    "CREATE INDEX IF NOT EXISTS idx_research_memory_timestamp ON research_memory(created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_research_tool_usage_session_id ON research_tool_usage(session_id);",
    "CREATE INDEX IF NOT EXISTS idx_research_tool_usage_tool_name ON research_tool_usage(tool_name);",
    "CREATE INDEX IF NOT EXISTS idx_research_exports_session_id ON research_exports(session_id);",
    "CREATE INDEX IF NOT EXISTS idx_research_feedback_session_id ON research_feedback(session_id);"
]

# 全文搜索索引
FULLTEXT_SEARCH_INDEXES = [
    # PostgreSQL全文搜索索引
    "CREATE INDEX IF NOT EXISTS idx_research_findings_content_fts ON research_findings USING gin(to_tsvector('english', content));",
    "CREATE INDEX IF NOT EXISTS idx_research_citations_title_fts ON research_citations USING gin(to_tsvector('english', title));",
    "CREATE INDEX IF NOT EXISTS idx_research_memory_content_fts ON research_memory USING gin(to_tsvector('english', message_content));"
]