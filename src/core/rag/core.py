# -*- coding: utf-8 -*-
"""
RAG 核心模块
实现知识库管理、文件处理和RAG核心功能
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """知识库类"""

    def __init__(self, name: str, path: Optional[Path] = None):
        """
        初始化知识库

        Args:
            name: 知识库名称
            path: 存储路径
        """
        self.name = name
        self.path = path or Path(f"rag_data/knowledge_bases/{name}")
        self.documents = []
        self._initialized = False

    async def initialize(self):
        """初始化知识库"""
        if not self._initialized:
            self.path.mkdir(parents=True, exist_ok=True)
            self._initialized = True
            logger.info(f"知识库 {self.name} 初始化完成")

    async def add_document(self, content: str, metadata: Dict[str, Any]) -> str:
        """
        添加文档到知识库

        Args:
            content: 文档内容
            metadata: 元数据

        Returns:
            文档ID
        """
        if not self._initialized:
            await self.initialize()

        doc_id = f"doc_{len(self.documents)}"
        document = {
            'id': doc_id,
            'content': content,
            'metadata': metadata
        }
        self.documents.append(document)

        logger.debug(f"文档 {doc_id} 已添加到知识库 {self.name}")
        return doc_id

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        在知识库中搜索

        Args:
            query: 查询字符串
            top_k: 返回的文档数量

        Returns:
            搜索结果列表
        """
        if not self.documents:
            return []

        # 简单的关键词匹配
        query_terms = set(query.lower().split())
        scored_docs = []

        for doc in self.documents:
            content = doc.get('content', '').lower()
            term_matches = sum(1 for term in query_terms if term in content)
            score = term_matches / len(query_terms) if query_terms else 0

            if score > 0:
                scored_docs.append({**doc, 'score': score})

        # 排序并返回top_k
        scored_docs.sort(key=lambda x: x['score'], reverse=True)
        return scored_docs[:top_k]


class FileProcessor:
    """文件处理器"""

    def __init__(self):
        """初始化文件处理器"""
        self.supported_extensions = ['.txt', '.md', '.pdf', '.docx']

    async def process_file(self, file_path: Path) -> Dict[str, Any]:
        """
        处理文件

        Args:
            file_path: 文件路径

        Returns:
            处理结果
        """
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        extension = file_path.suffix.lower()

        if extension not in self.supported_extensions:
            raise ValueError(f"不支持的文件类型: {extension}")

        try:
            if extension == '.txt':
                content = await self._process_text_file(file_path)
            elif extension == '.md':
                content = await self._process_markdown_file(file_path)
            elif extension == '.pdf':
                content = await self._process_pdf_file(file_path)
            elif extension == '.docx':
                content = await self._process_docx_file(file_path)
            else:
                content = ""

            return {
                'content': content,
                'metadata': {
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'file_size': file_path.stat().st_size,
                    'file_type': extension
                }
            }

        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {e}")
            raise

    async def _process_text_file(self, file_path: Path) -> str:
        """处理文本文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    async def _process_markdown_file(self, file_path: Path) -> str:
        """处理Markdown文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    async def _process_pdf_file(self, file_path: Path) -> str:
        """处理PDF文件"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            logger.warning("PyPDF2 未安装，使用占位符内容")
            return f"PDF文件内容: {file_path.name}"

    async def _process_docx_file(self, file_path: Path) -> str:
        """处理DOCX文件"""
        try:
            import docx
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            logger.warning("python-docx 未安装，使用占位符内容")
            return f"DOCX文件内容: {file_path.name}"


class RAGCore:
    """RAG核心类"""

    def __init__(self):
        """初始化RAG核心"""
        self.knowledge_bases = {}
        self.file_processor = FileProcessor()

    async def create_knowledge_base(self, name: str) -> KnowledgeBase:
        """
        创建知识库

        Args:
            name: 知识库名称

        Returns:
            知识库实例
        """
        if name in self.knowledge_bases:
            raise ValueError(f"知识库 {name} 已存在")

        kb = KnowledgeBase(name)
        await kb.initialize()
        self.knowledge_bases[name] = kb

        logger.info(f"知识库 {name} 创建成功")
        return kb

    async def get_knowledge_base(self, name: str) -> Optional[KnowledgeBase]:
        """
        获取知识库

        Args:
            name: 知识库名称

        Returns:
            知识库实例或None
        """
        return self.knowledge_bases.get(name)

    async def process_and_add_file(self, kb_name: str, file_path: Path) -> str:
        """
        处理文件并添加到知识库

        Args:
            kb_name: 知识库名称
            file_path: 文件路径

        Returns:
            文档ID
        """
        kb = await self.get_knowledge_base(kb_name)
        if not kb:
            raise ValueError(f"知识库 {kb_name} 不存在")

        # 处理文件
        processed_data = await self.file_processor.process_file(file_path)

        # 添加到知识库
        doc_id = await kb.add_document(
            content=processed_data['content'],
            metadata=processed_data['metadata']
        )

        logger.info(f"文件 {file_path.name} 已添加到知识库 {kb_name}")
        return doc_id

    async def search(self, kb_name: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        在知识库中搜索

        Args:
            kb_name: 知识库名称
            query: 查询字符串
            top_k: 返回的文档数量

        Returns:
            搜索结果
        """
        kb = await self.get_knowledge_base(kb_name)
        if not kb:
            return []

        return await kb.search(query, top_k)
