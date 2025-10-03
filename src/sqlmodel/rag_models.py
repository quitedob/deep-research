# -*- coding: utf-8 -*-
"""
RAG 相关模型：文档处理任务、文档、分块、嵌入 + 证据链支持。
集成 pgvector 实现真实向量检索。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List
import json

from sqlalchemy import Integer, String, DateTime, ForeignKey, Text, Float, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .models import Base


class DocumentProcessingJob(Base):
    __tablename__ = "document_processing_jobs"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    filename: Mapped[str] = mapped_column(String(255))  # 原始文件名
    file_path: Mapped[str] = mapped_column(String(512))  # 文件存储路径
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending/processing/embedding/indexed/completed/failed
    progress: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0-1.0 进度
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 错误信息
    result: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # 处理结果元数据

    # 时间戳字段
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # 开始处理时间
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # 完成时间
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)  # 原始文件路径

    # 证据链支持
    source_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)  # 来源URL（不建索引，太长）
    source_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # 'upload', 'web', 'api'
    source_title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)  # 来源标题
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # 内容哈希（去重）

    # 文档内容
    text: Mapped[str] = mapped_column(Text)
    text_length: Mapped[int] = mapped_column(Integer, default=0)  # 文本长度
    language: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)  # 语言代码

    # 元数据
    doc_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 文档元数据
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # 标签列表

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chunks: Mapped[list[Chunk]] = relationship(back_populates="document", cascade="all, delete-orphan")

    # 索引优化
    __table_args__ = (
        Index('ix_documents_user_type', 'user_id', 'source_type'),
        Index('ix_documents_content_hash', 'content_hash'),
        {'extend_existing': True}
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    index: Mapped[int] = mapped_column(Integer, default=0)  # 在文档中的分块索引

    # 文本内容
    text: Mapped[str] = mapped_column(Text)
    text_length: Mapped[int] = mapped_column(Integer, default=0)  # 文本长度
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # token数量

    # 证据链支持 - 精确位置信息
    start_pos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)  # 在原文档中的起始字符位置
    end_pos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)    # 在原文档中的结束字符位置
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # PDF页码
    section_title: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)  # 所在章节标题

    # 引用和片段
    citation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)  # 唯一引用ID
    snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 关键片段（纯文本）
    snippet_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 高亮HTML片段

    # 质量评分
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 相关性评分
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 质量评分

    # 元数据
    chunk_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 分块元数据

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped[Document] = relationship(back_populates="chunks")
    embedding: Mapped[Optional["DocumentEmbedding"]] = relationship(back_populates="chunk", cascade="all, delete-orphan")

    # 索引优化
    __table_args__ = (
        Index('ix_chunks_document_position', 'document_id', 'start_pos', 'end_pos'),
        Index('ix_chunks_citation', 'citation_id'),
        Index('ix_chunks_relevance', 'relevance_score'),
    )


class DocumentEmbedding(Base):
    __tablename__ = "document_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("chunks.id", ondelete="CASCADE"), unique=True)
    
    # 向量嵌入（存储为JSON，实际向量搜索使用FAISS）
    vector: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # 向量数据存储为JSON
    
    # 嵌入元数据
    model_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # 使用的嵌入模型
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    chunk: Mapped["Chunk"] = relationship(back_populates="embedding")

    # 创建常规索引以提升检索性能
    __table_args__ = (
        Index('ix_embeddings_chunk_id', 'chunk_id'),
        Index('ix_embeddings_created_at', 'created_at'),
    )


class Evidence(Base):
    """证据链记录表 - 用于追踪研究过程中的证据来源和引用"""
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 关联信息
    conversation_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    research_session_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)

    # 证据来源
    source_type: Mapped[str] = mapped_column(String(32))  # 'document', 'web', 'api', 'search', 'database'
    source_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # 关联的源ID（文档ID、网页ID等）
    source_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)  # 不建索引，太长
    source_title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # 证据内容
    content: Mapped[str] = mapped_column(Text)  # 完整内容
    snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 关键片段（纯文本）
    snippet_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 高亮HTML片段

    # 位置信息（用于文档证据）
    document_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    chunk_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    start_pos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 在原文档中的起始位置
    end_pos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)   # 在原文档中的结束位置

    # 评分与置信度
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 相关性评分 (0-1)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 置信度评分 (0-1)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 质量评分 (0-1)

    # 引用和使用情况
    citation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)  # 唯一引用ID
    citation_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 生成的引用文本
    used_in_response: Mapped[bool] = mapped_column(default=False, index=True)  # 是否被用于最终回答
    verified_by_user: Mapped[bool] = mapped_column(default=False)  # 用户是否验证过

    # 搜索和查询信息
    search_query: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)  # 相关的搜索查询
    search_engine: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # 使用的搜索引擎

    # 元数据
    evidence_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # 标签列表

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # 最后访问时间

    # 索引优化
    __table_args__ = (
        Index('ix_evidence_conversation_score', 'conversation_id', 'relevance_score'),
        Index('ix_evidence_research_session', 'research_session_id', 'created_at'),
        Index('ix_evidence_source_type', 'source_type'),
        Index('ix_evidence_citation', 'citation_id'),
        Index('ix_evidence_used_response', 'used_in_response'),
        Index('ix_evidence_user_created', 'user_id', 'created_at'),
    )
