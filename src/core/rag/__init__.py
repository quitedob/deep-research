# RAG核心模块包
# 包含RAG相关的配置、知识库、文件处理等功能

from .core import KnowledgeBase, FileProcessor, RAGCore
from .retrieval import search_documents, RetrievalStrategy, get_retriever
from .reranker import rerank_documents
from .config import KB_NAME_PATTERN, MAX_KBS, MAX_FILE_SIZE_MB, initialize_rag_directories

__all__ = [
    'KnowledgeBase',
    'FileProcessor',
    'RAGCore',
    'search_documents',
    'RetrievalStrategy',
    'get_retriever',
    'rerank_documents',
    'KB_NAME_PATTERN',
    'MAX_KBS',
    'MAX_FILE_SIZE_MB',
    'initialize_rag_directories'
]