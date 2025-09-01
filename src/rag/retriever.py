# -*- coding: utf-8 -*-
"""
文档检索器模块
整合向量存储和搜索功能，提供统一的文档检索接口
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .vector_store import VectorStore, ChromaVectorStore, MemoryVectorStore, Document
from .embeddings import get_embedding_service
from .chunker import TextChunker
from src.config.logging import get_logger

logger = get_logger("retriever")


@dataclass
class RetrievalResult:
    """检索结果"""
    documents: List[Document]
    scores: List[float]
    query: str
    total_found: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.total_found:
            self.total_found = len(self.documents)


class DocumentRetriever:
    """文档检索器"""
    
    def __init__(self, vector_store: Optional[VectorStore] = None, 
                 chunk_size: int = 500, chunk_overlap: int = 50):
        """
        初始化文档检索器
        
        Args:
            vector_store: 向量存储实例，如果为None则使用内存存储
            chunk_size: 文档分块大小
            chunk_overlap: 分块重叠大小
        """
        self.vector_store = vector_store or MemoryVectorStore()
        self.chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self._document_count = 0
        
    def add_document(self, content: str, metadata: Dict[str, Any] = None,
                    doc_id: str = None) -> str:
        """添加单个文档"""
        return self.add_documents([content], [metadata or {}], [doc_id])[0]
    
    def add_documents(self, contents: List[str], metadatas: List[Dict[str, Any]] = None,
                     doc_ids: List[str] = None) -> List[str]:
        """
        添加多个文档到检索器
        
        Args:
            contents: 文档内容列表
            metadatas: 文档元数据列表
            doc_ids: 文档ID列表
            
        Returns:
            添加的文档ID列表
        """
        try:
            if not contents:
                return []
                
            # 准备元数据和ID
            if metadatas is None:
                metadatas = [{}] * len(contents)
            if doc_ids is None:
                doc_ids = [None] * len(contents)
                
            # 处理每个文档
            all_documents = []
            
            for i, content in enumerate(contents):
                metadata = metadatas[i] if i < len(metadatas) else {}
                doc_id = doc_ids[i] if i < len(doc_ids) else None
                
                # 分块文档
                chunks = self.chunker.split_text(content)
                
                # 为每个块创建Document对象
                for j, chunk in enumerate(chunks):
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        "chunk_index": j,
                        "total_chunks": len(chunks),
                        "original_doc_id": doc_id,
                        "source": metadata.get("source", "unknown")
                    })
                    
                    chunk_id = f"{doc_id}_chunk_{j}" if doc_id else None
                    document = Document(
                        id=chunk_id,
                        content=chunk,
                        metadata=chunk_metadata
                    )
                    all_documents.append(document)
            
            # 添加到向量存储
            added_ids = self.vector_store.add_documents(all_documents)
            self._document_count += len(added_ids)
            
            logger.info(f"成功添加 {len(contents)} 个文档，生成 {len(added_ids)} 个文档块")
            return added_ids
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise
    
    def search(self, query: str, top_k: int = 5, 
              filter_metadata: Dict[str, Any] = None,
              min_score: float = 0.0) -> RetrievalResult:
        """
        搜索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件
            min_score: 最小相似度分数
            
        Returns:
            检索结果
        """
        try:
            # 使用向量存储搜索
            search_results = self.vector_store.search(
                query=query,
                top_k=top_k,
                filter_metadata=filter_metadata
            )
            
            # 过滤低分结果
            filtered_results = [
                (doc, score) for doc, score in search_results 
                if score >= min_score
            ]
            
            # 分离文档和分数
            documents = [result[0] for result in filtered_results]
            scores = [result[1] for result in filtered_results]
            
            # 合并来自同一原始文档的块（可选）
            merged_documents, merged_scores = self._merge_document_chunks(
                documents, scores
            )
            
            result = RetrievalResult(
                documents=merged_documents,
                scores=merged_scores,
                query=query,
                total_found=len(search_results),
                metadata={
                    "filtered_count": len(filtered_results),
                    "min_score": min_score,
                    "filter_metadata": filter_metadata
                }
            )
            
            logger.debug(f"搜索查询'{query}'返回 {len(merged_documents)} 个结果")
            return result
            
        except Exception as e:
            logger.error(f"搜索文档失败: {e}")
            return RetrievalResult(
                documents=[],
                scores=[],
                query=query,
                total_found=0,
                metadata={"error": str(e)}
            )
    
    def _merge_document_chunks(self, documents: List[Document], 
                              scores: List[float]) -> Tuple[List[Document], List[float]]:
        """合并来自同一原始文档的块"""
        try:
            # 按原始文档ID分组
            doc_groups = {}
            for doc, score in zip(documents, scores):
                original_doc_id = doc.metadata.get("original_doc_id")
                if original_doc_id not in doc_groups:
                    doc_groups[original_doc_id] = []
                doc_groups[original_doc_id].append((doc, score))
            
            merged_documents = []
            merged_scores = []
            
            for original_doc_id, group in doc_groups.items():
                if len(group) == 1:
                    # 单个块，直接添加
                    doc, score = group[0]
                    merged_documents.append(doc)
                    merged_scores.append(score)
                else:
                    # 多个块，合并内容
                    group.sort(key=lambda x: x[0].metadata.get("chunk_index", 0))
                    
                    merged_content = "\n\n".join([doc.content for doc, _ in group])
                    best_score = max([score for _, score in group])
                    
                    # 创建合并后的文档
                    base_doc = group[0][0]
                    merged_doc = Document(
                        id=f"{original_doc_id}_merged",
                        content=merged_content,
                        metadata={
                            **base_doc.metadata,
                            "merged_chunks": len(group),
                            "chunk_index": None,  # 清除chunk_index
                        }
                    )
                    
                    merged_documents.append(merged_doc)
                    merged_scores.append(best_score)
            
            return merged_documents, merged_scores
            
        except Exception as e:
            logger.warning(f"合并文档块失败: {e}")
            return documents, scores
    
    def delete_documents(self, doc_ids: List[str]) -> bool:
        """删除文档"""
        try:
            success = self.vector_store.delete_documents(doc_ids)
            if success:
                self._document_count = max(0, self._document_count - len(doc_ids))
            return success
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def clear_all_documents(self) -> bool:
        """清空所有文档"""
        try:
            success = self.vector_store.clear()
            if success:
                self._document_count = 0
            return success
        except Exception as e:
            logger.error(f"清空文档失败: {e}")
            return False
    
    def get_document_count(self) -> int:
        """获取文档数量"""
        try:
            return self.vector_store.get_document_count()
        except Exception as e:
            logger.error(f"获取文档数量失败: {e}")
            return self._document_count
    
    def get_stats(self) -> Dict[str, Any]:
        """获取检索器统计信息"""
        return {
            "document_count": self.get_document_count(),
            "chunk_size": self.chunker.chunk_size,
            "chunk_overlap": self.chunker.chunk_overlap,
            "vector_store_type": type(self.vector_store).__name__,
            "embedding_dimension": self._get_embedding_dimension()
        }
    
    def _get_embedding_dimension(self) -> int:
        """获取嵌入维度"""
        try:
            embedding_service = get_embedding_service()
            return embedding_service.get_dimension()
        except Exception:
            return -1


def create_default_retriever(persist_directory: str = None) -> DocumentRetriever:
    """创建默认的文档检索器"""
    try:
        # 尝试使用ChromaDB
        vector_store = ChromaVectorStore(
            collection_name="documents",
            persist_directory=persist_directory
        )
        logger.info("使用ChromaDB向量存储")
    except Exception as e:
        logger.warning(f"ChromaDB不可用，使用内存向量存储: {e}")
        vector_store = MemoryVectorStore()
    
    return DocumentRetriever(vector_store=vector_store) 