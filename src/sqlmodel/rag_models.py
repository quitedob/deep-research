# -*- coding: utf-8 -*-
"""
RAG 相关数据模型
用于向量存储和检索增强生成
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import Column, String, DateTime, Text, JSON, Index, Integer, Float
from sqlmodel import SQLModel, Field


# RAG 基础模型
class RAGBase(SQLModel):
    """RAG 基础模型"""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow}
    )


class DocumentChunk(RAGBase, table=True):
    """文档块模型"""
    __tablename__ = "document_chunks"

    document_id: str = Field(index=True)
    chunk_id: str = Field(unique=True, index=True)
    content: str = Field(sa_column=Column(Text))
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="向量嵌入"
    )
    metadata_: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="元数据"
    )
    chunk_index: int = Field(default=0, description="块索引")
    source_type: str = Field(max_length=50, description="来源类型")

    # 索引
    __table_args__ = (
        Index("ix_document_chunks_document_id", "document_id"),
        Index("ix_document_chunks_chunk_id", "chunk_id"),
        Index("ix_document_chunks_source_type", "source_type"),
        Index("ix_document_chunks_created_at", "created_at"),
    )


class DocumentMetadata(RAGBase, table=True):
    """文档元数据模型"""
    __tablename__ = "document_metadata"

    document_id: str = Field(unique=True, index=True)
    title: str = Field(max_length=500)
    source_url: Optional[str] = Field(default=None, max_length=2000)
    file_path: Optional[str] = Field(default=None, max_length=1000)
    content_type: str = Field(max_length=100)
    content_length: int = Field(default=0)
    chunk_count: int = Field(default=0)
    processing_status: str = Field(max_length=50, default="pending")
    metadata_: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON)
    )

    # 索引
    __table_args__ = (
        Index("ix_document_metadata_document_id", "document_id"),
        Index("ix_document_metadata_content_type", "content_type"),
        Index("ix_document_metadata_processing_status", "processing_status"),
        Index("ix_document_metadata_created_at", "created_at"),
    )


class RetrievalHistory(RAGBase, table=True):
    """检索历史模型"""
    __tablename__ = "retrieval_history"

    session_id: Optional[str] = Field(default=None, index=True)
    user_id: Optional[str] = Field(default=None, index=True)
    query: str = Field(sa_column=Column(Text))
    retrieved_chunks: List[str] = Field(sa_column=Column(JSON))  # chunk_id 列表
    relevance_scores: List[float] = Field(sa_column=Column(JSON))
    retrieval_strategy: str = Field(max_length=100, default="vector_only")
    processing_time: float = Field(description="处理时间(秒)")
    result_count: int = Field(default=0)

    # 索引
    __table_args__ = (
        Index("ix_retrieval_history_session_id", "session_id"),
        Index("ix_retrieval_history_user_id", "user_id"),
        Index("ix_retrieval_history_created_at", "created_at"),
        Index("ix_retrieval_history_retrieval_strategy", "retrieval_strategy"),
    )


class EmbeddingCache(RAGBase, table=True):
    """嵌入缓存模型"""
    __tablename__ = "embedding_cache"

    content_hash: str = Field(unique=True, index=True, max_length=64)
    content: str = Field(sa_column=Column(Text))
    embedding: List[float] = Field(sa_column=Column(JSON))
    model_name: str = Field(max_length=100)
    embedding_dim: int = Field()
    usage_count: int = Field(default=1)

    # 索引
    __table_args__ = (
        Index("ix_embedding_cache_content_hash", "content_hash"),
        Index("ix_embedding_cache_model_name", "model_name"),
        Index("ix_embedding_cache_usage_count", "usage_count"),
    )


class KnowledgeGraphNode(RAGBase, table=True):
    """知识图谱节点模型"""
    __tablename__ = "knowledge_graph_nodes"

    node_id: str = Field(unique=True, index=True)
    node_type: str = Field(max_length=50)
    label: str = Field(max_length=200)
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON)
    )
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(JSON)
    )

    # 索引
    __table_args__ = (
        Index("ix_knowledge_graph_nodes_node_id", "node_id"),
        Index("ix_knowledge_graph_nodes_node_type", "node_type"),
        Index("ix_knowledge_graph_nodes_label", "label"),
    )


class KnowledgeGraphEdge(RAGBase, table=True):
    """知识图谱边模型"""
    __tablename__ = "knowledge_graph_edges"

    edge_id: str = Field(unique=True, index=True)
    source_node_id: str = Field(index=True)
    target_node_id: str = Field(index=True)
    edge_type: str = Field(max_length=50)
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON)
    )
    weight: float = Field(default=1.0)

    # 索引
    __table_args__ = (
        Index("ix_knowledge_graph_edges_edge_id", "edge_id"),
        Index("ix_knowledge_graph_edges_source_node_id", "source_node_id"),
        Index("ix_knowledge_graph_edges_target_node_id", "target_node_id"),
        Index("ix_knowledge_graph_edges_edge_type", "edge_type"),
    )


class RerankerHistory(RAGBase, table=True):
    """重排序历史模型"""
    __tablename__ = "reranker_history"

    session_id: Optional[str] = Field(default=None, index=True)
    query: str = Field(sa_column=Column(Text))
    original_chunks: List[str] = Field(sa_column=Column(JSON))  # 原始 chunk_id 列表
    reranked_chunks: List[str] = Field(sa_column=Column(JSON))  # 重排序后 chunk_id 列表
    original_scores: List[float] = Field(sa_column=Column(JSON))
    reranked_scores: List[float] = Field(sa_column=Column(JSON))
    reranker_model: str = Field(max_length=100)
    processing_time: float = Field(description="处理时间(秒)")

    # 索引
    __table_args__ = (
        Index("ix_reranker_history_session_id", "session_id"),
        Index("ix_reranker_history_created_at", "created_at"),
        Index("ix_reranker_history_reranker_model", "reranker_model"),
    )
