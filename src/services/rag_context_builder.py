#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG上下文构建器
优化知识库检索、上下文排序和融合
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """检索到的文档块"""
    content: str
    source: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "source": self.source,
            "score": self.score,
            "metadata": self.metadata,
            "chunk_id": self.chunk_id
        }


@dataclass
class RAGContext:
    """RAG上下文"""
    query: str
    chunks: List[RetrievedChunk]
    total_tokens: int
    retrieval_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_context_text(self, max_chunks: Optional[int] = None) -> str:
        """获取上下文文本"""
        chunks_to_use = self.chunks[:max_chunks] if max_chunks else self.chunks
        
        context_parts = []
        for i, chunk in enumerate(chunks_to_use, 1):
            context_parts.append(
                f"[文档 {i}] (来源: {chunk.source}, 相关度: {chunk.score:.2f})\n"
                f"{chunk.content}\n"
            )
        
        return "\n".join(context_parts)
    
    def get_sources(self) -> List[str]:
        """获取所有来源"""
        return list(set(chunk.source for chunk in self.chunks))


class RAGContextBuilder:
    """RAG上下文构建器"""
    
    def __init__(
        self,
        embedding_model: Optional[Any] = None,
        reranker_model: Optional[Any] = None,
        max_chunks: int = 5,
        min_score: float = 0.5,
        enable_reranking: bool = True
    ):
        self.embedding_model = embedding_model
        self.reranker_model = reranker_model
        self.max_chunks = max_chunks
        self.min_score = min_score
        self.enable_reranking = enable_reranking
        
    async def build_context(
        self,
        query: str,
        vector_store: Any,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 20
    ) -> RAGContext:
        """构建RAG上下文"""
        start_time = datetime.now()
        
        # 第一阶段：向量检索（召回）
        initial_chunks = await self._retrieve_chunks(
            query=query,
            vector_store=vector_store,
            filters=filters,
            top_k=top_k
        )
        
        # 第二阶段：重排序（可选）
        if self.enable_reranking and self.reranker_model:
            ranked_chunks = await self._rerank_chunks(query, initial_chunks)
        else:
            ranked_chunks = initial_chunks
        
        # 过滤低分文档
        filtered_chunks = [
            chunk for chunk in ranked_chunks
            if chunk.score >= self.min_score
        ]
        
        # 限制数量
        final_chunks = filtered_chunks[:self.max_chunks]
        
        # 去重
        final_chunks = self._deduplicate_chunks(final_chunks)
        
        # 计算token数
        total_tokens = sum(len(chunk.content.split()) for chunk in final_chunks)
        
        retrieval_time = (datetime.now() - start_time).total_seconds()
        
        return RAGContext(
            query=query,
            chunks=final_chunks,
            total_tokens=total_tokens,
            retrieval_time=retrieval_time,
            metadata={
                "initial_count": len(initial_chunks),
                "filtered_count": len(filtered_chunks),
                "final_count": len(final_chunks),
                "reranking_enabled": self.enable_reranking
            }
        )
    
    async def _retrieve_chunks(
        self,
        query: str,
        vector_store: Any,
        filters: Optional[Dict[str, Any]],
        top_k: int
    ) -> List[RetrievedChunk]:
        """从向量存储检索文档块"""
        try:
            # 这里需要根据实际的向量存储实现来调整
            # 假设vector_store有similarity_search方法
            if hasattr(vector_store, 'similarity_search_with_score'):
                results = await vector_store.similarity_search_with_score(
                    query=query,
                    k=top_k,
                    filter=filters
                )
                
                chunks = []
                for doc, score in results:
                    chunks.append(RetrievedChunk(
                        content=doc.page_content,
                        source=doc.metadata.get("source", "unknown"),
                        score=score,
                        metadata=doc.metadata,
                        chunk_id=doc.metadata.get("chunk_id")
                    ))
                
                return chunks
            else:
                logger.warning("Vector store does not support similarity_search_with_score")
                return []
                
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []
    
    async def _rerank_chunks(
        self,
        query: str,
        chunks: List[RetrievedChunk]
    ) -> List[RetrievedChunk]:
        """重排序文档块"""
        if not self.reranker_model or not chunks:
            return chunks
        
        try:
            # 准备重排序输入
            pairs = [(query, chunk.content) for chunk in chunks]
            
            # 调用重排序模型
            # 这里需要根据实际的重排序模型实现来调整
            if hasattr(self.reranker_model, 'predict'):
                scores = await self.reranker_model.predict(pairs)
                
                # 更新分数
                for chunk, score in zip(chunks, scores):
                    chunk.score = float(score)
                
                # 按新分数排序
                chunks.sort(key=lambda x: x.score, reverse=True)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error reranking chunks: {e}")
            return chunks
    
    def _deduplicate_chunks(
        self,
        chunks: List[RetrievedChunk],
        similarity_threshold: float = 0.9
    ) -> List[RetrievedChunk]:
        """去重文档块"""
        if not chunks:
            return chunks
        
        unique_chunks = [chunks[0]]
        
        for chunk in chunks[1:]:
            # 简单的基于内容相似度的去重
            is_duplicate = False
            for unique_chunk in unique_chunks:
                similarity = self._calculate_text_similarity(
                    chunk.content,
                    unique_chunk.content
                )
                if similarity >= similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_chunks.append(chunk)
        
        return unique_chunks
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简单实现）"""
        # 使用Jaccard相似度
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    async def build_multimodal_context(
        self,
        query: str,
        text_store: Any,
        image_store: Optional[Any] = None,
        audio_store: Optional[Any] = None
    ) -> RAGContext:
        """构建多模态RAG上下文"""
        all_chunks = []
        
        # 检索文本
        if text_store:
            text_chunks = await self._retrieve_chunks(
                query=query,
                vector_store=text_store,
                filters=None,
                top_k=self.max_chunks
            )
            all_chunks.extend(text_chunks)
        
        # 检索图像（如果支持）
        if image_store:
            try:
                image_chunks = await self._retrieve_chunks(
                    query=query,
                    vector_store=image_store,
                    filters={"type": "image"},
                    top_k=3
                )
                all_chunks.extend(image_chunks)
            except Exception as e:
                logger.warning(f"Image retrieval failed: {e}")
        
        # 检索音频（如果支持）
        if audio_store:
            try:
                audio_chunks = await self._retrieve_chunks(
                    query=query,
                    vector_store=audio_store,
                    filters={"type": "audio"},
                    top_k=2
                )
                all_chunks.extend(audio_chunks)
            except Exception as e:
                logger.warning(f"Audio retrieval failed: {e}")
        
        # 按分数排序
        all_chunks.sort(key=lambda x: x.score, reverse=True)
        
        # 限制总数
        final_chunks = all_chunks[:self.max_chunks]
        
        return RAGContext(
            query=query,
            chunks=final_chunks,
            total_tokens=sum(len(c.content.split()) for c in final_chunks),
            retrieval_time=0.0,
            metadata={"multimodal": True}
        )
    
    def format_context_for_prompt(
        self,
        context: RAGContext,
        include_sources: bool = True,
        include_scores: bool = False
    ) -> str:
        """格式化上下文用于提示词"""
        if not context.chunks:
            return "没有找到相关的上下文信息。"
        
        parts = ["以下是相关的背景信息：\n"]
        
        for i, chunk in enumerate(context.chunks, 1):
            part = f"\n[文档 {i}]"
            
            if include_sources:
                part += f" 来源: {chunk.source}"
            
            if include_scores:
                part += f" (相关度: {chunk.score:.2f})"
            
            part += f"\n{chunk.content}\n"
            parts.append(part)
        
        if include_sources:
            sources = context.get_sources()
            parts.append(f"\n参考来源: {', '.join(sources)}")
        
        return "".join(parts)


# 全局实例
_rag_context_builder: Optional[RAGContextBuilder] = None


def get_rag_context_builder() -> RAGContextBuilder:
    """获取RAG上下文构建器实例"""
    global _rag_context_builder
    if _rag_context_builder is None:
        _rag_context_builder = RAGContextBuilder()
    return _rag_context_builder


def set_rag_context_builder(builder: RAGContextBuilder):
    """设置RAG上下文构建器实例"""
    global _rag_context_builder
    _rag_context_builder = builder
