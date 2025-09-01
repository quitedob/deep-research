# -*- coding: utf-8 -*-
"""
文档分割器
提供多种文档分割策略，用于将长文档分割成适合嵌入的块
"""

import re
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """文档块数据类"""
    content: str
    metadata: Dict[str, Any]
    chunk_id: Optional[str] = None
    start_index: int = 0
    end_index: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "chunk_id": self.chunk_id,
            "start_index": self.start_index,
            "end_index": self.end_index
        }

class BaseDocumentSplitter(ABC):
    """文档分割器基类"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    @abstractmethod
    def split_text(self, text: str, metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        """分割文本"""
        pass
    
    def split_documents(self, documents: List[Dict[str, Any]]) -> List[DocumentChunk]:
        """分割多个文档"""
        all_chunks = []
        
        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            
            chunks = self.split_text(content, metadata)
            all_chunks.extend(chunks)
        
        return all_chunks

class CharacterTextSplitter(BaseDocumentSplitter):
    """基于字符数的文本分割器"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, separator: str = "\n\n"):
        super().__init__(chunk_size, chunk_overlap)
        self.separator = separator
        
    def split_text(self, text: str, metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        """按字符数分割文本"""
        if not text:
            return []
        
        metadata = metadata or {}
        chunks = []
        
        # 首先按分隔符分割
        if self.separator in text:
            sections = text.split(self.separator)
        else:
            sections = [text]
        
        current_chunk = ""
        start_index = 0
        
        for section in sections:
            # 如果当前块加上新段落超过限制
            if len(current_chunk) + len(section) + len(self.separator) > self.chunk_size:
                if current_chunk:
                    # 保存当前块
                    chunk = DocumentChunk(
                        content=current_chunk.strip(),
                        metadata=metadata.copy(),
                        start_index=start_index,
                        end_index=start_index + len(current_chunk)
                    )
                    chunks.append(chunk)
                    
                    # 开始新块，考虑重叠
                    if self.chunk_overlap > 0:
                        overlap_text = current_chunk[-self.chunk_overlap:]
                        current_chunk = overlap_text + self.separator + section
                        start_index = start_index + len(current_chunk) - len(overlap_text) - len(self.separator)
                    else:
                        current_chunk = section
                        start_index = start_index + len(current_chunk)
                else:
                    current_chunk = section
            else:
                if current_chunk:
                    current_chunk += self.separator + section
                else:
                    current_chunk = section
        
        # 保存最后一块
        if current_chunk:
            chunk = DocumentChunk(
                content=current_chunk.strip(),
                metadata=metadata.copy(),
                start_index=start_index,
                end_index=start_index + len(current_chunk)
            )
            chunks.append(chunk)
        
        return chunks

class RecursiveCharacterTextSplitter(BaseDocumentSplitter):
    """递归字符分割器"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, separators: List[str] = None):
        super().__init__(chunk_size, chunk_overlap)
        self.separators = separators or ["\n\n", "\n", " ", ""]
        
    def split_text(self, text: str, metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        """递归分割文本"""
        if not text:
            return []
        
        metadata = metadata or {}
        return self._split_text_recursive(text, self.separators, metadata)
    
    def _split_text_recursive(self, text: str, separators: List[str], metadata: Dict[str, Any], start_index: int = 0) -> List[DocumentChunk]:
        """递归分割文本"""
        final_chunks = []
        separator = separators[-1]
        new_separators = []
        
        for i, sep in enumerate(separators):
            if sep == "":
                separator = sep
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1:]
                break
        
        # 分割文本
        splits = text.split(separator) if separator else [text]
        good_splits = []
        
        for split in splits:
            if len(split) < self.chunk_size:
                good_splits.append(split)
            else:
                if good_splits:
                    merged_text = separator.join(good_splits)
                    if len(merged_text) > 0:
                        chunk = DocumentChunk(
                            content=merged_text,
                            metadata=metadata.copy(),
                            start_index=start_index,
                            end_index=start_index + len(merged_text)
                        )
                        final_chunks.append(chunk)
                        start_index += len(merged_text) + len(separator)
                    good_splits = []
                
                if new_separators:
                    sub_chunks = self._split_text_recursive(split, new_separators, metadata, start_index)
                    final_chunks.extend(sub_chunks)
                    start_index += len(split) + len(separator)
                else:
                    # 强制分割
                    for i in range(0, len(split), self.chunk_size):
                        chunk_text = split[i:i + self.chunk_size]
                        chunk = DocumentChunk(
                            content=chunk_text,
                            metadata=metadata.copy(),
                            start_index=start_index + i,
                            end_index=start_index + i + len(chunk_text)
                        )
                        final_chunks.append(chunk)
                    start_index += len(split) + len(separator)
        
        if good_splits:
            merged_text = separator.join(good_splits)
            chunk = DocumentChunk(
                content=merged_text,
                metadata=metadata.copy(),
                start_index=start_index,
                end_index=start_index + len(merged_text)
            )
            final_chunks.append(chunk)
        
        return final_chunks

class MarkdownTextSplitter(BaseDocumentSplitter):
    """Markdown文档分割器"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        super().__init__(chunk_size, chunk_overlap)
        self.separators = [
            "\n## ",  # 二级标题
            "\n### ", # 三级标题
            "\n#### ", # 四级标题
            "\n\n",   # 段落
            "\n",     # 行
            " ",      # 空格
            ""        # 字符
        ]
        
    def split_text(self, text: str, metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        """分割Markdown文本"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators
        )
        return splitter.split_text(text, metadata)

class PythonCodeSplitter(BaseDocumentSplitter):
    """Python代码分割器"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        super().__init__(chunk_size, chunk_overlap)
        self.separators = [
            "\nclass ",   # 类定义
            "\ndef ",     # 函数定义
            "\n\ndef ",   # 独立函数
            "\n\n",       # 空行
            "\n",         # 行
            " ",          # 空格
            ""            # 字符
        ]
        
    def split_text(self, text: str, metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        """分割Python代码"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators
        )
        return splitter.split_text(text, metadata)

class LatexTextSplitter(BaseDocumentSplitter):
    """LaTeX文档分割器"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        super().__init__(chunk_size, chunk_overlap)
        self.separators = [
            "\n\\section{",    # 章节
            "\n\\subsection{", # 子章节
            "\n\\subsubsection{", # 子子章节
            "\n\\paragraph{",  # 段落
            "\n\n",           # 空行
            "\n",             # 行
            " ",              # 空格
            ""                # 字符
        ]
        
    def split_text(self, text: str, metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        """分割LaTeX文本"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators
        )
        return splitter.split_text(text, metadata)

class TokenTextSplitter(BaseDocumentSplitter):
    """基于Token的文本分割器"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, encoding_name: str = "cl100k_base"):
        super().__init__(chunk_size, chunk_overlap)
        self.encoding_name = encoding_name
        self._encoding = None
        
    @property
    def encoding(self):
        """懒加载tiktoken编码器"""
        if self._encoding is None:
            try:
                import tiktoken
                self._encoding = tiktoken.get_encoding(self.encoding_name)
            except ImportError:
                logger.warning("tiktoken not installed, falling back to character-based splitting")
                return None
        return self._encoding
    
    def split_text(self, text: str, metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        """按Token数分割文本"""
        if not text:
            return []
        
        if not self.encoding:
            # 回退到字符分割
            char_splitter = CharacterTextSplitter(
                chunk_size=self.chunk_size * 4,  # 粗略估算
                chunk_overlap=self.chunk_overlap * 4
            )
            return char_splitter.split_text(text, metadata)
        
        metadata = metadata or {}
        chunks = []
        
        # 将文本编码为tokens
        tokens = self.encoding.encode(text)
        
        start_idx = 0
        while start_idx < len(tokens):
            # 计算结束位置
            end_idx = start_idx + self.chunk_size
            
            # 获取当前块的tokens
            chunk_tokens = tokens[start_idx:end_idx]
            
            # 解码为文本
            chunk_text = self.encoding.decode(chunk_tokens)
            
            # 创建文档块
            chunk = DocumentChunk(
                content=chunk_text,
                metadata=metadata.copy(),
                start_index=start_idx,
                end_index=min(end_idx, len(tokens))
            )
            chunks.append(chunk)
            
            # 移动到下一个位置，考虑重叠
            start_idx = end_idx - self.chunk_overlap
            
            if start_idx >= len(tokens):
                break
        
        return chunks

# 便捷函数
def get_text_splitter(
    splitter_type: str = "recursive",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    **kwargs
) -> BaseDocumentSplitter:
    """获取文本分割器"""
    splitter_map = {
        "character": CharacterTextSplitter,
        "recursive": RecursiveCharacterTextSplitter,
        "markdown": MarkdownTextSplitter,
        "python": PythonCodeSplitter,
        "latex": LatexTextSplitter,
        "token": TokenTextSplitter
    }
    
    if splitter_type not in splitter_map:
        raise ValueError(f"Unknown splitter type: {splitter_type}")
    
    splitter_class = splitter_map[splitter_type]
    return splitter_class(chunk_size=chunk_size, chunk_overlap=chunk_overlap, **kwargs)
