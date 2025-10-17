# -*- coding: utf-8 -*-
"""
向量存储模块
提供内存向量存储实现
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """向量存储文档"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class MemoryVectorStore:
    """内存向量存储"""

    def __init__(self):
        """初始化内存向量存储"""
        self.documents: List[Document] = []
        self._id_counter = 0

    async def add_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        embedding: List[float],
        doc_id: Optional[str] = None
    ) -> str:
        """
        添加文档到向量存储

        Args:
            content: 文档内容
            metadata: 元数据
            embedding: 向量嵌入
            doc_id: 文档ID（如果不提供则自动生成）

        Returns:
            文档ID
        """
        if doc_id is None:
            self._id_counter += 1
            doc_id = f"doc_{self._id_counter}"

        document = Document(
            id=doc_id,
            content=content,
            metadata=metadata,
            embedding=embedding
        )

        # 检查是否已存在，如果存在则更新
        existing_index = None
        for i, doc in enumerate(self.documents):
            if doc.id == doc_id:
                existing_index = i
                break

        if existing_index is not None:
            self.documents[existing_index] = document
        else:
            self.documents.append(document)

        logger.debug(f"文档 {doc_id} 已添加到内存向量存储")
        return doc_id

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[Tuple[Document, float]]:
        """
        向量相似度搜索

        Args:
            query_embedding: 查询向量
            top_k: 返回的文档数量
            filter_metadata: 元数据过滤条件
            score_threshold: 分数阈值

        Returns:
            (文档, 分数) 元组列表
        """
        if not self.documents:
            return []

        query_vec = np.array(query_embedding)
        similarities = []

        for doc in self.documents:
            # 应用元数据过滤
            if filter_metadata:
                if not self._matches_filter(doc.metadata, filter_metadata):
                    continue

            if doc.embedding:
                doc_vec = np.array(doc.embedding)

                # 计算余弦相似度
                norm_query = np.linalg.norm(query_vec)
                norm_doc = np.linalg.norm(doc_vec)

                if norm_query > 0 and norm_doc > 0:
                    similarity = np.dot(query_vec, doc_vec) / (norm_query * norm_doc)
                    similarity = float(similarity)

                    if similarity >= score_threshold:
                        similarities.append((doc, similarity))
                else:
                    # 如果向量为零向量，使用0相似度
                    similarities.append((doc, 0.0))

        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    async def delete_document(self, doc_id: str):
        """
        删除文档

        Args:
            doc_id: 文档ID
        """
        self.documents = [doc for doc in self.documents if doc.id != doc_id]
        logger.debug(f"文档 {doc_id} 已从内存向量存储中删除")

    def _matches_filter(self, metadata: Dict[str, Any], filter_metadata: Dict[str, Any]) -> bool:
        """
        检查元数据是否匹配过滤条件

        Args:
            metadata: 文档元数据
            filter_metadata: 过滤条件

        Returns:
            是否匹配
        """
        for key, value in filter_metadata.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return {
            "total_documents": len(self.documents),
            "total_chunks": sum(len(doc.content.split()) for doc in self.documents)
        }
