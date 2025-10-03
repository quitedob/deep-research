# -*- coding: utf-8 -*-
"""
RAG 功能包：基于 rag_example.txt 实现的知识库管理系统
"""

from .config import *
from .knowledge_base import KnowledgeBase, KBQueryResult, KBHit
from .file_processor import FileProcessor
from .rag_core import RAGCore

__all__ = [
    "KnowledgeBase",
    "KBQueryResult", 
    "KBHit",
    "FileProcessor",
    "RAGCore"
]