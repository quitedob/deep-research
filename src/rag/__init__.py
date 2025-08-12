# -*- coding: utf-8 -*-
"""
RAG (检索增强生成) 模块
提供文档向量化存储和语义检索功能
"""

# 向量存储
from .vector_store import VectorStore, ChromaVectorStore

# 文档检索器
from .retriever import DocumentRetriever

# 文本分块器
from .chunker import TextChunker

# 文档分割器
from .splitter import (
    DocumentChunk,
    BaseDocumentSplitter,
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    MarkdownTextSplitter,
    PythonCodeSplitter,
    LatexTextSplitter,
    TokenTextSplitter,
    get_text_splitter
)

# 检索服务
from .retrieval import (
    RetrievalStrategy,
    RetrievalResult,
    DocumentIndex,
    RetrievalService,
    get_retrieval_service,
    search_documents,
    add_document_to_index
)

# 使用llms模块中的嵌入服务
from ..llms.embeddings import (
    EmbeddingService,
    get_embedding_service
)

__all__ = [
    # 向量存储
    "VectorStore",
    "ChromaVectorStore",
    
    # 文档检索
    "DocumentRetriever",
    
    # 文本分块
    "TextChunker",
    
    # 文档分割
    "DocumentChunk",
    "BaseDocumentSplitter",
    "CharacterTextSplitter",
    "RecursiveCharacterTextSplitter",
    "MarkdownTextSplitter",
    "PythonCodeSplitter",
    "LatexTextSplitter",
    "TokenTextSplitter",
    "get_text_splitter",
    
    # 检索服务
    "RetrievalStrategy",
    "RetrievalResult",
    "DocumentIndex",
    "RetrievalService",
    "get_retrieval_service",
    "search_documents",
    "add_document_to_index",
    
    # 嵌入服务（来自llms模块）
    "EmbeddingService",
    "get_embedding_service"
] 