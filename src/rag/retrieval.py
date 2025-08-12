# -*- coding: utf-8 -*-
"""
检索服务
提供统一的文档检索接口，整合向量检索、关键词检索等多种检索策略
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

from .vector_store import VectorStore, ChromaVectorStore
from .retriever import DocumentRetriever
from .splitter import DocumentChunk, get_text_splitter
from ..llms.embeddings import get_embedding_service

logger = logging.getLogger(__name__)

class RetrievalStrategy(Enum):
    """检索策略枚举"""
    VECTOR_ONLY = "vector_only"           # 仅向量检索
    KEYWORD_ONLY = "keyword_only"         # 仅关键词检索
    HYBRID = "hybrid"                     # 混合检索
    RERANK = "rerank"                     # 重排序检索

@dataclass
class RetrievalResult:
    """检索结果数据类"""
    content: str
    metadata: Dict[str, Any]
    score: float
    source: str = ""
    chunk_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "score": self.score,
            "source": self.source,
            "chunk_id": self.chunk_id
        }

class DocumentIndex:
    """文档索引"""
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_service=None,
        collection_name: str = "documents"
    ):
        self.vector_store = vector_store or ChromaVectorStore(collection_name=collection_name)
        self.embedding_service = embedding_service or get_embedding_service()
        self.retriever = DocumentRetriever(self.vector_store, self.embedding_service)
        
        # 文档元数据存储（简单的内存存储）
        self.document_metadata: Dict[str, Dict[str, Any]] = {}
        
    async def add_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        doc_id: Optional[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[str]:
        """添加文档到索引"""
        try:
            # 文档分割
            splitter = get_text_splitter(
                splitter_type="recursive",
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            chunks = splitter.split_text(content, metadata)
            
            # 添加文档ID到元数据
            if doc_id:
                for chunk in chunks:
                    chunk.metadata["doc_id"] = doc_id
                    chunk.metadata["chunk_index"] = chunks.index(chunk)
            
            # 添加到向量存储
            chunk_ids = await self.retriever.add_documents([
                {"content": chunk.content, "metadata": chunk.metadata}
                for chunk in chunks
            ])
            
            # 存储文档元数据
            if doc_id:
                self.document_metadata[doc_id] = {
                    **metadata,
                    "chunk_count": len(chunks),
                    "chunk_ids": chunk_ids
                }
            
            logger.info(f"Added document with {len(chunks)} chunks to index")
            return chunk_ids
            
        except Exception as e:
            logger.error(f"Error adding document to index: {e}")
            raise
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[List[str]]:
        """批量添加文档"""
        all_chunk_ids = []
        
        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            doc_id = doc.get("id")
            
            chunk_ids = await self.add_document(
                content, metadata, doc_id, chunk_size, chunk_overlap
            )
            all_chunk_ids.append(chunk_ids)
        
        return all_chunk_ids
    
    async def search(
        self,
        query: str,
        strategy: RetrievalStrategy = RetrievalStrategy.VECTOR_ONLY,
        top_k: int = 5,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """搜索相关文档"""
        try:
            if strategy == RetrievalStrategy.VECTOR_ONLY:
                return await self._vector_search(query, top_k, score_threshold, filters)
            elif strategy == RetrievalStrategy.KEYWORD_ONLY:
                return await self._keyword_search(query, top_k, filters)
            elif strategy == RetrievalStrategy.HYBRID:
                return await self._hybrid_search(query, top_k, score_threshold, filters)
            elif strategy == RetrievalStrategy.RERANK:
                return await self._rerank_search(query, top_k, score_threshold, filters)
            else:
                raise ValueError(f"Unknown retrieval strategy: {strategy}")
                
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def _vector_search(
        self,
        query: str,
        top_k: int,
        score_threshold: float,
        filters: Optional[Dict[str, Any]]
    ) -> List[RetrievalResult]:
        """向量搜索"""
        results = await self.retriever.search(
            query, top_k=top_k, score_threshold=score_threshold
        )
        
        retrieval_results = []
        for result in results:
            retrieval_result = RetrievalResult(
                content=result["content"],
                metadata=result.get("metadata", {}),
                score=result.get("score", 0.0),
                source="vector_search",
                chunk_id=result.get("id")
            )
            retrieval_results.append(retrieval_result)
        
        return retrieval_results
    
    async def _keyword_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[RetrievalResult]:
        """关键词搜索（简单实现）"""
        # 这里是一个简化的关键词搜索实现
        # 实际应用中可能需要使用更复杂的文本搜索引擎如Elasticsearch
        
        # 获取所有文档
        all_docs = await self.retriever.get_all_documents()
        
        # 简单的关键词匹配
        query_words = query.lower().split()
        scored_docs = []
        
        for doc in all_docs:
            content = doc.get("content", "").lower()
            score = 0
            
            for word in query_words:
                score += content.count(word)
            
            if score > 0:
                scored_docs.append((doc, score))
        
        # 按分数排序
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # 转换为检索结果
        results = []
        for doc, score in scored_docs[:top_k]:
            result = RetrievalResult(
                content=doc["content"],
                metadata=doc.get("metadata", {}),
                score=float(score),
                source="keyword_search",
                chunk_id=doc.get("id")
            )
            results.append(result)
        
        return results
    
    async def _hybrid_search(
        self,
        query: str,
        top_k: int,
        score_threshold: float,
        filters: Optional[Dict[str, Any]]
    ) -> List[RetrievalResult]:
        """混合搜索（向量 + 关键词）"""
        # 并行执行向量搜索和关键词搜索
        vector_task = asyncio.create_task(
            self._vector_search(query, top_k * 2, score_threshold, filters)
        )
        keyword_task = asyncio.create_task(
            self._keyword_search(query, top_k * 2, filters)
        )
        
        vector_results, keyword_results = await asyncio.gather(vector_task, keyword_task)
        
        # 合并和去重结果
        combined_results = {}
        
        # 添加向量搜索结果（权重0.7）
        for result in vector_results:
            chunk_id = result.chunk_id
            if chunk_id:
                combined_results[chunk_id] = RetrievalResult(
                    content=result.content,
                    metadata=result.metadata,
                    score=result.score * 0.7,
                    source="hybrid_vector",
                    chunk_id=chunk_id
                )
        
        # 添加关键词搜索结果（权重0.3）
        for result in keyword_results:
            chunk_id = result.chunk_id
            if chunk_id:
                if chunk_id in combined_results:
                    # 合并分数
                    combined_results[chunk_id].score += result.score * 0.3
                    combined_results[chunk_id].source = "hybrid_combined"
                else:
                    combined_results[chunk_id] = RetrievalResult(
                        content=result.content,
                        metadata=result.metadata,
                        score=result.score * 0.3,
                        source="hybrid_keyword",
                        chunk_id=chunk_id
                    )
        
        # 按分数排序并返回top_k
        final_results = list(combined_results.values())
        final_results.sort(key=lambda x: x.score, reverse=True)
        
        return final_results[:top_k]
    
    async def _rerank_search(
        self,
        query: str,
        top_k: int,
        score_threshold: float,
        filters: Optional[Dict[str, Any]]
    ) -> List[RetrievalResult]:
        """重排序搜索"""
        # 首先获取更多的候选结果
        candidate_results = await self._vector_search(
            query, top_k * 3, score_threshold, filters
        )
        
        # 这里可以集成更复杂的重排序模型
        # 目前使用简单的文本相似度重排序
        reranked_results = []
        
        for result in candidate_results:
            # 计算查询和文档内容的词汇重叠度
            query_words = set(query.lower().split())
            content_words = set(result.content.lower().split())
            
            # Jaccard相似度
            intersection = len(query_words & content_words)
            union = len(query_words | content_words)
            jaccard_score = intersection / union if union > 0 else 0
            
            # 结合原始向量分数和Jaccard分数
            combined_score = result.score * 0.8 + jaccard_score * 0.2
            
            reranked_result = RetrievalResult(
                content=result.content,
                metadata=result.metadata,
                score=combined_score,
                source="rerank_search",
                chunk_id=result.chunk_id
            )
            reranked_results.append(reranked_result)
        
        # 按新分数排序
        reranked_results.sort(key=lambda x: x.score, reverse=True)
        
        return reranked_results[:top_k]
    
    async def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        try:
            if doc_id in self.document_metadata:
                metadata = self.document_metadata[doc_id]
                chunk_ids = metadata.get("chunk_ids", [])
                
                # 从向量存储中删除chunks
                for chunk_id in chunk_ids:
                    success = await self.retriever.delete_document(chunk_id)
                    if not success:
                        logger.warning(f"Failed to delete chunk {chunk_id}")
                
                # 删除元数据
                del self.document_metadata[doc_id]
                
                logger.info(f"Deleted document {doc_id} with {len(chunk_ids)} chunks")
                return True
            else:
                logger.warning(f"Document {doc_id} not found in index")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    async def get_document_info(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取文档信息"""
        return self.document_metadata.get(doc_id)
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """列出所有文档"""
        return [
            {"doc_id": doc_id, **metadata}
            for doc_id, metadata in self.document_metadata.items()
        ]
    
    async def clear_index(self) -> bool:
        """清空索引"""
        try:
            # 清空向量存储
            success = await self.retriever.clear()
            if success:
                # 清空元数据
                self.document_metadata.clear()
                logger.info("Cleared document index")
                return True
            else:
                logger.error("Failed to clear vector store")
                return False
                
        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            return False

class RetrievalService:
    """检索服务管理器"""
    
    def __init__(self):
        self.indexes: Dict[str, DocumentIndex] = {}
        self.default_index_name = "default"
        
    def get_index(self, index_name: str = None) -> DocumentIndex:
        """获取文档索引"""
        index_name = index_name or self.default_index_name
        
        if index_name not in self.indexes:
            self.indexes[index_name] = DocumentIndex(collection_name=index_name)
        
        return self.indexes[index_name]
    
    async def add_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        doc_id: Optional[str] = None,
        index_name: str = None
    ) -> List[str]:
        """添加文档"""
        index = self.get_index(index_name)
        return await index.add_document(content, metadata, doc_id)
    
    async def search_documents(
        self,
        query: str,
        strategy: RetrievalStrategy = RetrievalStrategy.VECTOR_ONLY,
        top_k: int = 5,
        index_name: str = None
    ) -> List[RetrievalResult]:
        """搜索文档"""
        index = self.get_index(index_name)
        return await index.search(query, strategy, top_k)
    
    async def delete_document(self, doc_id: str, index_name: str = None) -> bool:
        """删除文档"""
        index = self.get_index(index_name)
        return await index.delete_document(doc_id)
    
    def list_indexes(self) -> List[str]:
        """列出所有索引"""
        return list(self.indexes.keys())

# 全局检索服务实例
_retrieval_service = None

def get_retrieval_service() -> RetrievalService:
    """获取全局检索服务实例"""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service

# 便捷函数
async def search_documents(
    query: str,
    strategy: RetrievalStrategy = RetrievalStrategy.VECTOR_ONLY,
    top_k: int = 5,
    index_name: str = None
) -> List[RetrievalResult]:
    """便捷的文档搜索函数"""
    service = get_retrieval_service()
    return await service.search_documents(query, strategy, top_k, index_name)

async def add_document_to_index(
    content: str,
    metadata: Dict[str, Any],
    doc_id: Optional[str] = None,
    index_name: str = None
) -> List[str]:
    """便捷的文档添加函数"""
    service = get_retrieval_service()
    return await service.add_document(content, metadata, doc_id, index_name)
