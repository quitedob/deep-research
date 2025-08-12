# -*- coding: utf-8 -*-
"""
工具模块
提供搜索、文档处理、代码执行、OCR等功能
"""

# 基础工具
from .base_tool import BaseTool

# 搜索工具
from .search import SearchTool, TavilySearchTool
from .search.web_search import WebSearchService, SearchResult, get_web_search_service, search_web
from .search.wikipedia_tool import WikipediaSearchTool, WikipediaPage, WikipediaSearchResult, get_wikipedia_tool
from .search.arxiv_tool import ArxivSearchTool, ArxivPaper, ArxivService, get_arxiv_service, search_arxiv

# 文档处理工具
from .document_processor import DocumentProcessor

# 代码执行工具
from .code_executor import CodeExecutorTool
from .code_exec import (
    CodeExecutorService, 
    SecurePythonExecutor, 
    JupyterStyleExecutor,
    CodeExecutionResult,
    get_code_executor_service,
    execute_python_code,
    validate_python_code
)

# OCR工具
from .ocr import (
    OCRService,
    OCRResult,
    TesseractOCR,
    EasyOCR,
    PaddleOCR,
    get_ocr_service
)

__all__ = [
    # 基础工具
    "BaseTool",
    
    # 搜索工具
    "SearchTool",
    "TavilySearchTool",
    "WebSearchService",
    "SearchResult", 
    "get_web_search_service",
    "search_web",
    
    # Wikipedia工具
    "WikipediaSearchTool",
    "WikipediaPage",
    "WikipediaSearchResult",
    "get_wikipedia_tool",
    
    # arXiv工具
    "ArxivSearchTool",
    "ArxivPaper", 
    "ArxivService",
    "get_arxiv_service",
    "search_arxiv",
    
    # 文档处理
    "DocumentProcessor",
    
    # 代码执行
    "CodeExecutorTool",
    "CodeExecutorService",
    "SecurePythonExecutor",
    "JupyterStyleExecutor", 
    "CodeExecutionResult",
    "get_code_executor_service",
    "execute_python_code",
    "validate_python_code",
    
    # OCR
    "OCRService",
    "OCRResult",
    "TesseractOCR",
    "EasyOCR",
    "PaddleOCR",
    "get_ocr_service"
] 