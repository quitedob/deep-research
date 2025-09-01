# -*- coding: utf-8 -*-
"""
文本分块器模块
将长文本分割成适合向量化的小块
"""

import re
from typing import List, Optional
from abc import ABC, abstractmethod

from src.config.logging import get_logger

logger = get_logger("chunker")


class TextChunker(ABC):
    """文本分块器抽象基类"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        初始化分块器
        
        Args:
            chunk_size: 每个块的目标大小（字符数）
            chunk_overlap: 块之间的重叠大小（字符数）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    @abstractmethod
    def split_text(self, text: str) -> List[str]:
        """分割文本为块"""
        pass


class SimpleTextChunker(TextChunker):
    """简单文本分块器 - 按字符长度分割"""
    
    def split_text(self, text: str) -> List[str]:
        """按字符长度分割文本"""
        if not text or len(text) <= self.chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # 如果不是最后一块，尝试在句子边界分割
            if end < len(text):
                # 向后查找句子结束符
                sentence_end = self._find_sentence_boundary(text, end, start)
                if sentence_end != -1:
                    end = sentence_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 计算下一个块的起始位置（考虑重叠）
            start = max(start + 1, end - self.chunk_overlap)
        
        return chunks
    
    def _find_sentence_boundary(self, text: str, preferred_end: int, start: int) -> int:
        """查找合适的句子边界"""
        # 在preferred_end附近查找句子结束符
        search_range = min(50, self.chunk_size // 4)  # 搜索范围
        
        # 向前搜索句子结束符
        for i in range(preferred_end, max(start, preferred_end - search_range), -1):
            if text[i] in '.!?。！？\n':
                return i + 1
        
        # 如果没找到，向后搜索
        for i in range(preferred_end, min(len(text), preferred_end + search_range)):
            if text[i] in '.!?。！？\n':
                return i + 1
        
        return -1  # 没找到合适的边界


class SmartTextChunker(TextChunker):
    """智能文本分块器 - 按段落和句子分割"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        super().__init__(chunk_size, chunk_overlap)
        
        # 段落分隔符
        self.paragraph_separators = ['\n\n', '\r\n\r\n']
        
        # 句子分隔符
        self.sentence_separators = ['.', '!', '?', '。', '！', '？']
        
        # 子句分隔符
        self.clause_separators = [',', ';', ':', '，', '；', '：']
    
    def split_text(self, text: str) -> List[str]:
        """智能分割文本"""
        if not text:
            return []
        
        # 如果文本很短，直接返回
        if len(text) <= self.chunk_size:
            return [text.strip()]
        
        # 首先按段落分割
        paragraphs = self._split_by_paragraphs(text)
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # 如果当前段落很长，需要进一步分割
            if len(paragraph) > self.chunk_size:
                # 保存当前块
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # 分割长段落
                para_chunks = self._split_long_paragraph(paragraph)
                chunks.extend(para_chunks)
            else:
                # 检查是否可以添加到当前块
                if len(current_chunk) + len(paragraph) + 2 <= self.chunk_size:
                    if current_chunk:
                        current_chunk += "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
                else:
                    # 保存当前块，开始新块
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # 应用重叠策略
        return self._apply_overlap(chunks)
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """按段落分割文本"""
        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 按双换行分割段落
        paragraphs = text.split('\n\n')
        
        # 清理空段落和多余空白
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """分割长段落"""
        chunks = []
        
        # 首先按句子分割
        sentences = self._split_by_sentences(paragraph)
        
        current_chunk = ""
        for sentence in sentences:
            # 如果单个句子就超过了chunk_size，需要强制分割
            if len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # 强制分割长句子
                forced_chunks = self._force_split_sentence(sentence)
                chunks.extend(forced_chunks)
            else:
                # 检查是否可以添加到当前块
                if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                    if current_chunk:
                        current_chunk += " " + sentence
                    else:
                        current_chunk = sentence
                else:
                    # 保存当前块，开始新块
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """按句子分割文本"""
        # 使用正则表达式分割句子
        pattern = r'[.!?。！？]+\s*'
        sentences = re.split(pattern, text)
        
        # 清理空句子
        return [s.strip() for s in sentences if s.strip()]
    
    def _force_split_sentence(self, sentence: str) -> List[str]:
        """强制分割长句子"""
        chunks = []
        start = 0
        
        while start < len(sentence):
            end = start + self.chunk_size
            
            # 如果不是最后一段，尝试在合适的位置分割
            if end < len(sentence):
                # 查找合适的分割点（逗号、分号等）
                split_point = self._find_split_point(sentence, end, start)
                if split_point != -1:
                    end = split_point
            
            chunk = sentence[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end
        
        return chunks
    
    def _find_split_point(self, text: str, preferred_end: int, start: int) -> int:
        """查找合适的分割点"""
        # 在preferred_end附近查找分隔符
        search_range = min(50, self.chunk_size // 4)
        
        # 优先查找子句分隔符
        for i in range(preferred_end, max(start, preferred_end - search_range), -1):
            if text[i] in self.clause_separators:
                return i + 1
        
        # 查找空格
        for i in range(preferred_end, max(start, preferred_end - search_range), -1):
            if text[i] == ' ':
                return i + 1
        
        return -1
    
    def _apply_overlap(self, chunks: List[str]) -> List[str]:
        """应用重叠策略"""
        if len(chunks) <= 1 or self.chunk_overlap <= 0:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped_chunks.append(chunk)
            else:
                # 添加与前一个块的重叠部分
                prev_chunk = chunks[i-1]
                overlap_text = prev_chunk[-self.chunk_overlap:] if len(prev_chunk) > self.chunk_overlap else prev_chunk
                
                # 尝试在句子或单词边界截取重叠
                overlap_text = self._trim_overlap_to_boundary(overlap_text)
                
                if overlap_text:
                    overlapped_chunk = overlap_text + " " + chunk
                else:
                    overlapped_chunk = chunk
                
                overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks
    
    def _trim_overlap_to_boundary(self, text: str) -> str:
        """将重叠文本修剪到合适的边界"""
        # 查找最后一个完整的句子或单词
        for sep in self.sentence_separators:
            if sep in text:
                parts = text.split(sep)
                if len(parts) > 1:
                    return sep.join(parts[:-1]) + sep
        
        # 如果没有句子分隔符，查找最后一个单词边界
        words = text.split()
        if len(words) > 1:
            return ' '.join(words[:-1])
        
        return text


# 工厂函数
def create_chunker(chunker_type: str = "smart", **kwargs) -> TextChunker:
    """创建文本分块器"""
    if chunker_type == "simple":
        return SimpleTextChunker(**kwargs)
    elif chunker_type == "smart":
        return SmartTextChunker(**kwargs)
    else:
        raise ValueError(f"不支持的分块器类型: {chunker_type}")


# 默认导出
TextChunker = SmartTextChunker 