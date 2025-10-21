# -*- coding: utf-8 -*-
"""
文本分块处理工具
根据不同的策略将文本分割成适合处理的块，支持多种分块方法
"""

import re
import logging
from typing import List, Optional, Dict, Any, Union, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    tiktoken = None
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """文本块数据类"""
    content: str
    start_index: int = 0
    end_index: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.end_index == 0:
            self.end_index = len(self.content)
    
    @property
    def length(self) -> int:
        """返回文本块长度"""
        return len(self.content)
    
    @property
    def word_count(self) -> int:
        """返回词汇数量"""
        return len(self.content.split())
    
    def __str__(self) -> str:
        return f"TextChunk(length={self.length}, content='{self.content[:50]}...')"


class BaseChunker(ABC):
    """文本分块器基类"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    @abstractmethod
    def split_text(self, text: str) -> List[TextChunk]:
        """分割文本为块"""
        pass
    
    def _create_chunks_with_overlap(self, text_parts: List[str], 
                                  separators: List[str] = None) -> List[TextChunk]:
        """创建带重叠的文本块"""
        chunks = []
        current_chunk = ""
        current_index = 0
        
        for i, part in enumerate(text_parts):
            # 检查是否需要开始新块
            if len(current_chunk) + len(part) > self.chunk_size and current_chunk:
                # 保存当前块
                chunk = TextChunk(
                    content=current_chunk.strip(),
                    start_index=current_index,
                    end_index=current_index + len(current_chunk)
                )
                chunks.append(chunk)
                
                # 创建重叠
                overlap_text = current_chunk[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                current_chunk = overlap_text + part
                current_index += len(current_chunk) - len(overlap_text)
            else:
                current_chunk += part
        
        # 添加最后一块
        if current_chunk.strip():
            chunk = TextChunk(
                content=current_chunk.strip(),
                start_index=current_index,
                end_index=current_index + len(current_chunk)
            )
            chunks.append(chunk)
        
        return chunks


class RecursiveCharacterChunker(BaseChunker):
    """递归字符分块器 - 尝试在句子、段落等自然边界分割"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200,
                 separators: Optional[List[str]] = None):
        super().__init__(chunk_size, chunk_overlap)
        if separators is None:
            self.separators = [
                "\n\n",  # 段落
                "\n",    # 行
                "。",    # 中文句号
                "！",    # 中文感叹号
                "？",    # 中文问号
                ". ",    # 英文句号
                "! ",    # 英文感叹号
                "? ",    # 英文问号
                ";",     # 分号
                ",",     # 逗号
                " ",     # 空格
                ""       # 字符级别（最后手段）
            ]
        else:
            self.separators = separators
    
    def split_text(self, text: str) -> List[TextChunk]:
        """递归分割文本"""
        return self._split_text_recursive(text, self.separators)
    
    def _split_text_recursive(self, text: str, separators: List[str]) -> List[TextChunk]:
        """递归分割文本实现"""
        chunks = []
        
        if not separators:
            # 没有分隔符时，直接按大小分割
            return self._split_by_size(text)
        
        separator = separators[0]
        remaining_separators = separators[1:]
        
        if separator == "":
            # 字符级别分割
            return self._split_by_size(text)
        
        splits = text.split(separator)
        current_chunk = ""
        start_index = 0
        
        for i, split in enumerate(splits):
            if i > 0:
                split = separator + split  # 保留分隔符
            
            if len(current_chunk + split) <= self.chunk_size:
                current_chunk += split
            else:
                if current_chunk:
                    # 递归处理当前块
                    if len(current_chunk) > self.chunk_size:
                        sub_chunks = self._split_text_recursive(current_chunk, remaining_separators)
                        chunks.extend(sub_chunks)
                    else:
                        chunk = TextChunk(
                            content=current_chunk.strip(),
                            start_index=start_index,
                            metadata={"separator": separator}
                        )
                        chunks.append(chunk)
                
                current_chunk = split
                start_index += len(current_chunk) - len(split)
        
        # 处理最后一块
        if current_chunk:
            if len(current_chunk) > self.chunk_size:
                sub_chunks = self._split_text_recursive(current_chunk, remaining_separators)
                chunks.extend(sub_chunks)
            else:
                chunk = TextChunk(
                    content=current_chunk.strip(),
                    start_index=start_index,
                    metadata={"separator": separator}
                )
                chunks.append(chunk)
        
        return chunks
    
    def _split_by_size(self, text: str) -> List[TextChunk]:
        """按固定大小分割"""
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            end_index = min(i + self.chunk_size, len(text))
            chunk_text = text[i:end_index]
            
            chunk = TextChunk(
                content=chunk_text,
                start_index=i,
                end_index=end_index,
                metadata={"method": "size_based"}
            )
            chunks.append(chunk)
            
            if end_index >= len(text):
                break
        
        return chunks


class TokenBasedChunker(BaseChunker):
    """基于Token的分块器 - 考虑LLM的Token限制"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50,
                 model_name: str = "gpt-3.5-turbo"):
        super().__init__(chunk_size, chunk_overlap)
        self.model_name = model_name
        if not TIKTOKEN_AVAILABLE:
            logger.warning("tiktoken not available, falling back to character-based chunking")
            self.encoding = None
        else:
            try:
                self.encoding = tiktoken.encoding_for_model(model_name)
            except KeyError:
                # 如果模型不存在，使用默认编码
                self.encoding = tiktoken.get_encoding("cl100k_base")
                logger.warning(f"Model {model_name} not found, using cl100k_base encoding")
    
    def count_tokens(self, text: str) -> int:
        """计算文本的Token数量"""
        if self.encoding is None:
            # 如果tiktoken不可用，使用字符数作为粗略估计
            # 假设1个token约等于4个字符（这是一个粗略的估计）
            return len(text) // 4
        return len(self.encoding.encode(text))

    def split_text(self, text: str) -> List[TextChunk]:
        """基于Token数量分割文本"""
        if self.encoding is None:
            # 如果tiktoken不可用，回退到字符分块
            logger.warning("tiktoken not available, falling back to character-based chunking")
            char_chunker = RecursiveCharacterChunker(
                chunk_size=self.chunk_size * 4,  # 假设1 token ≈ 4 chars
                chunk_overlap=self.chunk_overlap * 4
            )
            chunks = char_chunker.split_text(text)
            # 更新元数据
            for chunk in chunks:
                chunk.metadata["method"] = "token_based_fallback"
                chunk.metadata["tokens"] = self.count_tokens(chunk.content)
            return chunks

        chunks = []

        # 首先尝试按段落分割
        paragraphs = text.split('\n\n')
        current_chunk = ""
        current_tokens = 0
        start_index = 0

        for paragraph in paragraphs:
            paragraph_tokens = self.count_tokens(paragraph)

            # 如果单个段落就超过chunk_size，需要进一步分割
            if paragraph_tokens > self.chunk_size:
                if current_chunk:
                    # 保存当前块
                    chunk = TextChunk(
                        content=current_chunk.strip(),
                        start_index=start_index,
                        metadata={"tokens": current_tokens, "method": "token_based"}
                    )
                    chunks.append(chunk)
                    current_chunk = ""
                    current_tokens = 0
                    start_index += len(chunk.content)

                # 分割大段落
                sub_chunks = self._split_large_paragraph(paragraph)
                chunks.extend(sub_chunks)

            elif current_tokens + paragraph_tokens > self.chunk_size:
                # 保存当前块
                if current_chunk:
                    chunk = TextChunk(
                        content=current_chunk.strip(),
                        start_index=start_index,
                        metadata={"tokens": current_tokens, "method": "token_based"}
                    )
                    chunks.append(chunk)

                # 开始新块（带重叠）
                overlap_text = ""
                if self.chunk_overlap > 0 and current_chunk:
                    words = current_chunk.split()
                    overlap_words = words[-self.chunk_overlap:]
                    overlap_text = " ".join(overlap_words)

                current_chunk = overlap_text + "\n\n" + paragraph if overlap_text else paragraph
                current_tokens = self.count_tokens(current_chunk)
                start_index += len(current_chunk) - len(overlap_text) - len(paragraph)

            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_tokens += paragraph_tokens

        # 添加最后一块
        if current_chunk.strip():
            chunk = TextChunk(
                content=current_chunk.strip(),
                start_index=start_index,
                metadata={"tokens": current_tokens, "method": "token_based"}
            )
            chunks.append(chunk)

        return chunks
    
    def _split_large_paragraph(self, paragraph: str) -> List[TextChunk]:
        """分割大段落"""
        sentences = re.split(r'[.!?。！？]\s+', paragraph)
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                chunk = TextChunk(
                    content=current_chunk.strip(),
                    metadata={"tokens": current_tokens, "method": "token_based_sentence"}
                )
                chunks.append(chunk)
                current_chunk = sentence
                current_tokens = sentence_tokens
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_tokens += sentence_tokens
        
        if current_chunk.strip():
            chunk = TextChunk(
                content=current_chunk.strip(),
                metadata={"tokens": current_tokens, "method": "token_based_sentence"}
            )
            chunks.append(chunk)
        
        return chunks


class MarkdownChunker(BaseChunker):
    """Markdown文档分块器 - 按照Markdown结构分割"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        super().__init__(chunk_size, chunk_overlap)
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    
    def split_text(self, text: str) -> List[TextChunk]:
        """按Markdown结构分割"""
        chunks = []
        
        # 按标题分割
        sections = self._split_by_headers(text)
        
        for section in sections:
            if len(section["content"]) <= self.chunk_size:
                chunk = TextChunk(
                    content=section["content"].strip(),
                    metadata={
                        "header": section["header"],
                        "level": section["level"],
                        "method": "markdown_section"
                    }
                )
                chunks.append(chunk)
            else:
                # 如果section太大，进一步分割
                sub_chunker = RecursiveCharacterChunker(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap
                )
                sub_chunks = sub_chunker.split_text(section["content"])
                
                for sub_chunk in sub_chunks:
                    sub_chunk.metadata.update({
                        "header": section["header"],
                        "level": section["level"],
                        "method": "markdown_subsection"
                    })
                
                chunks.extend(sub_chunks)
        
        return chunks
    
    def _split_by_headers(self, text: str) -> List[Dict[str, Any]]:
        """按标题分割文档"""
        sections = []
        lines = text.split('\n')
        current_section = {"header": "", "level": 0, "content": ""}
        
        for line in lines:
            header_match = self.header_pattern.match(line)
            
            if header_match:
                # 保存当前section
                if current_section["content"].strip():
                    sections.append(current_section)
                
                # 开始新section
                level = len(header_match.group(1))
                header_text = header_match.group(2)
                current_section = {
                    "header": header_text,
                    "level": level,
                    "content": line + "\n"
                }
            else:
                current_section["content"] += line + "\n"
        
        # 添加最后一个section
        if current_section["content"].strip():
            sections.append(current_section)
        
        return sections


class CodeChunker(BaseChunker):
    """代码文件分块器 - 按照代码结构分割"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100,
                 language: str = "python"):
        super().__init__(chunk_size, chunk_overlap)
        self.language = language.lower()
        
        # 定义不同语言的函数/类模式
        self.patterns = {
            "python": {
                "function": re.compile(r'^(def\s+\w+.*?:)\s*$', re.MULTILINE),
                "class": re.compile(r'^(class\s+\w+.*?:)\s*$', re.MULTILINE),
                "import": re.compile(r'^(import\s+.*|from\s+.*\s+import\s+.*)\s*$', re.MULTILINE)
            },
            "javascript": {
                "function": re.compile(r'^(function\s+\w+.*?\{|const\s+\w+\s*=\s*.*?=>)', re.MULTILINE),
                "class": re.compile(r'^(class\s+\w+.*?\{)', re.MULTILINE)
            },
            "java": {
                "function": re.compile(r'^(\s*(?:public|private|protected)?\s*(?:static)?\s*\w+\s+\w+\s*\([^)]*\)\s*\{)', re.MULTILINE),
                "class": re.compile(r'^(\s*(?:public|private)?\s*class\s+\w+.*?\{)', re.MULTILINE)
            }
        }
    
    def split_text(self, text: str) -> List[TextChunk]:
        """按代码结构分割"""
        if self.language not in self.patterns:
            # 不支持的语言，使用通用分割
            return RecursiveCharacterChunker(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            ).split_text(text)
        
        chunks = []
        patterns = self.patterns[self.language]
        
        # 找到所有函数和类的位置
        functions = []
        classes = []
        
        if "function" in patterns:
            functions = [(m.start(), m.end(), "function") for m in patterns["function"].finditer(text)]
        if "class" in patterns:
            classes = [(m.start(), m.end(), "class") for m in patterns["class"].finditer(text)]
        
        # 合并并排序
        code_blocks = sorted(functions + classes)
        
        if not code_blocks:
            # 没有找到代码结构，使用通用分割
            return RecursiveCharacterChunker(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            ).split_text(text)
        
        # 按代码块分割
        current_pos = 0
        
        for i, (start, end, block_type) in enumerate(code_blocks):
            # 获取到下一个代码块开始的文本
            next_start = code_blocks[i + 1][0] if i + 1 < len(code_blocks) else len(text)
            block_text = text[start:next_start]
            
            if len(block_text) <= self.chunk_size:
                chunk = TextChunk(
                    content=block_text.strip(),
                    start_index=start,
                    end_index=next_start,
                    metadata={
                        "type": block_type,
                        "language": self.language,
                        "method": "code_block"
                    }
                )
                chunks.append(chunk)
            else:
                # 代码块太大，进一步分割
                sub_chunker = RecursiveCharacterChunker(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    separators=["\n\n", "\n", "{", "}", ";", " ", ""]
                )
                sub_chunks = sub_chunker.split_text(block_text)
                
                for sub_chunk in sub_chunks:
                    sub_chunk.metadata.update({
                        "type": block_type,
                        "language": self.language,
                        "method": "code_subblock"
                    })
                
                chunks.extend(sub_chunks)
        
        return chunks


class SemanticChunker(BaseChunker):
    """语义分块器 - 基于语义相似度分割（简化版）"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200,
                 similarity_threshold: float = 0.7):
        super().__init__(chunk_size, chunk_overlap)
        self.similarity_threshold = similarity_threshold
    
    def split_text(self, text: str) -> List[TextChunk]:
        """基于语义相似度分割（简化实现）"""
        # 这里是一个简化的实现，实际的语义分块需要embedding模型
        # 目前回退到句子级别的分割
        
        # 按句子分割
        sentences = re.split(r'[.!?。！？]\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= self.chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk.strip():
                    chunk = TextChunk(
                        content=current_chunk.strip(),
                        metadata={"method": "semantic_sentence"}
                    )
                    chunks.append(chunk)
                
                current_chunk = sentence + ". "
        
        # 添加最后一块
        if current_chunk.strip():
            chunk = TextChunk(
                content=current_chunk.strip(),
                metadata={"method": "semantic_sentence"}
            )
            chunks.append(chunk)
        
        return chunks


class ChunkingManager:
    """分块管理器 - 统一管理不同的分块策略"""
    
    def __init__(self):
        self.chunkers = {
            "recursive": RecursiveCharacterChunker,
            "token": TokenBasedChunker,
            "markdown": MarkdownChunker,
            "code": CodeChunker,
            "semantic": SemanticChunker
        }
    
    def chunk_text(self, text: str, method: str = "recursive",
                   chunk_size: int = 1000, chunk_overlap: int = 200,
                   **kwargs) -> List[TextChunk]:
        """使用指定方法分块文本"""
        if method not in self.chunkers:
            raise ValueError(f"Unsupported chunking method: {method}")
        
        chunker_class = self.chunkers[method]
        chunker = chunker_class(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            **kwargs
        )
        
        return chunker.split_text(text)
    
    def chunk_file(self, file_path: Union[str, Path], method: str = "auto",
                   chunk_size: int = 1000, chunk_overlap: int = 200,
                   **kwargs) -> List[TextChunk]:
        """分块文件内容"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 自动检测分块方法
        if method == "auto":
            method = self._detect_chunking_method(file_path, text)
        
        chunks = self.chunk_text(text, method, chunk_size, chunk_overlap, **kwargs)
        
        # 为所有块添加文件信息
        for chunk in chunks:
            chunk.metadata.update({
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_extension": file_path.suffix
            })
        
        return chunks
    
    def _detect_chunking_method(self, file_path: Path, text: str) -> str:
        """自动检测分块方法"""
        extension = file_path.suffix.lower()
        
        # 根据文件扩展名决定
        if extension == ".md":
            return "markdown"
        elif extension in [".py", ".js", ".java", ".cpp", ".c", ".go", ".rs"]:
            return "code"
        elif "```" in text or text.count("\n") > text.count(" ") * 0.1:
            # 可能是代码文件
            return "code"
        elif text.count("#") > 10 and re.search(r'^#+\s', text, re.MULTILINE):
            # 可能是Markdown
            return "markdown"
        else:
            return "recursive"
    
    def get_optimal_chunk_size(self, text: str, target_chunks: int = 10) -> int:
        """根据文本长度和目标块数计算最优块大小"""
        text_length = len(text)
        optimal_size = text_length // target_chunks
        
        # 限制在合理范围内
        return max(500, min(optimal_size, 2000))


# 全局分块管理器实例
chunking_manager = ChunkingManager()


# 便捷函数
def chunk_text(text: str, method: str = "recursive", 
               chunk_size: int = 1000, chunk_overlap: int = 200,
               **kwargs) -> List[TextChunk]:
    """便捷的文本分块函数"""
    return chunking_manager.chunk_text(text, method, chunk_size, chunk_overlap, **kwargs)


def chunk_file(file_path: Union[str, Path], method: str = "auto",
               chunk_size: int = 1000, chunk_overlap: int = 200,
               **kwargs) -> List[TextChunk]:
    """便捷的文件分块函数"""
    return chunking_manager.chunk_file(file_path, method, chunk_size, chunk_overlap, **kwargs)
