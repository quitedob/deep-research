# -*- coding: utf-8 -*-
"""
RAG 重排序服务
实现两阶段检索：召回（Recall）+ 重排序（Re-rank）
使用交叉编码器模型进行精确的重排序
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DocumentScore:
    """文档评分结果"""
    document_id: str
    content: str
    metadata: Dict[str, Any]
    recall_score: float  # 召回阶段分数
    rerank_score: float  # 重排序阶段分数
    final_score: float    # 最终综合分数


class CrossEncoderReranker:
    """基于交叉编码器的重排序器"""

    def __init__(self, model_name: str = "ms-marco-MiniLM-L-6-v2"):
        """
        初始化重排序器

        Args:
            model_name: 交叉编码器模型名称
        """
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        """加载交叉编码器模型"""
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.model_name)
            logger.info(f"成功加载交叉编码器模型: {self.model_name}")
        except ImportError:
            logger.warning("sentence-transformers 未安装，将使用简单的重排序方法")
            self.model = None
        except Exception as e:
            logger.error(f"加载交叉编码器模型失败: {e}")
            self.model = None

    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5,
        batch_size: int = 16
    ) -> List[DocumentScore]:
        """
        对文档进行重排序

        Args:
            query: 查询字符串
            documents: 文档列表，每个文档包含 content 和 metadata
            top_k: 返回的文档数量
            batch_size: 批处理大小

        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []

        if self.model is None:
            # 回退到简单的关键词重排序
            return await self._simple_rerank(query, documents, top_k)

        try:
            # 准备输入数据
            doc_contents = [doc.get('content', '') for doc in documents]

            # 分批处理
            all_scores = []
            for i in range(0, len(doc_contents), batch_size):
                batch_docs = doc_contents[i:i + batch_size]
                batch_queries = [query] * len(batch_docs)

                # 预测相关性分数
                scores = self.model.predict(list(zip(batch_queries, batch_docs)))
                all_scores.extend(scores)

            # 创建评分结果
            scored_docs = []
            for i, (doc, score) in enumerate(zip(documents, all_scores)):
                # 获取原始召回分数（如果有）
                recall_score = doc.get('score', 0.0)

                # 计算最终分数（可以调整权重）
                final_score = 0.7 * score + 0.3 * recall_score

                scored_docs.append(DocumentScore(
                    document_id=doc.get('id', str(i)),
                    content=doc.get('content', ''),
                    metadata=doc.get('metadata', {}),
                    recall_score=recall_score,
                    rerank_score=float(score),
                    final_score=final_score
                ))

            # 按最终分数排序并返回前top_k个
            scored_docs.sort(key=lambda x: x.final_score, reverse=True)
            return scored_docs[:top_k]

        except Exception as e:
            logger.error(f"交叉编码器重排序失败: {e}")
            # 回退到简单重排序
            return await self._simple_rerank(query, documents, top_k)

    async def _simple_rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int
    ) -> List[DocumentScore]:
        """
        简单的重排序方法（基于关键词匹配）

        Args:
            query: 查询字符串
            documents: 文档列表
            top_k: 返回的文档数量

        Returns:
            重排序后的文档列表
        """
        query_terms = set(query.lower().split())

        scored_docs = []
        for i, doc in enumerate(documents):
            content = doc.get('content', '').lower()
            recall_score = doc.get('score', 0.0)

            # 计算关键词匹配分数
            term_matches = sum(1 for term in query_terms if term in content)
            max_possible_matches = len(query_terms)
            keyword_score = term_matches / max_possible_matches if max_possible_matches > 0 else 0

            # 计算最终分数
            final_score = 0.6 * keyword_score + 0.4 * recall_score

            scored_docs.append(DocumentScore(
                document_id=doc.get('id', str(i)),
                content=doc.get('content', ''),
                metadata=doc.get('metadata', {}),
                recall_score=recall_score,
                rerank_score=keyword_score,
                final_score=final_score
            ))

        # 按分数排序
        scored_docs.sort(key=lambda x: x.final_score, reverse=True)
        return scored_docs[:top_k]


class TwoStageRAGRetriever:
    """两阶段RAG检索器"""

    def __init__(
        self,
        vector_store,
        reranker: Optional[CrossEncoderReranker] = None,
        recall_top_k: int = 50,
        final_top_k: int = 5,
        min_score_threshold: float = 0.1
    ):
        """
        初始化两阶段检索器

        Args:
            vector_store: 向量存储实例
            reranker: 重排序器实例
            recall_top_k: 召回阶段的文档数量
            final_top_k: 最终返回的文档数量
            min_score_threshold: 最小分数阈值
        """
        self.vector_store = vector_store
        self.reranker = reranker or CrossEncoderReranker()
        self.recall_top_k = recall_top_k
        self.final_top_k = final_top_k
        self.min_score_threshold = min_score_threshold

    async def search(
        self,
        query: str,
        filter_metadata: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[DocumentScore]:
        """
        执行两阶段检索

        Args:
            query: 查询字符串
            filter_metadata: 元数据过滤条件
            score_threshold: 召回阶段分数阈值

        Returns:
            检索结果列表
        """
        try:
            # 第一阶段：召回（Recall）
            recalled_docs = await self._recall_phase(query, filter_metadata, score_threshold)

            if not recalled_docs:
                logger.info(f"查询 '{query}' 未召回任何文档")
                return []

            logger.info(f"查询 '{query}' 召回了 {len(recalled_docs)} 个文档")

            # 第二阶段：重排序（Re-rank）
            reranked_docs = await self._rerank_phase(query, recalled_docs)

            # 应用最小分数阈值
            filtered_docs = [
                doc for doc in reranked_docs
                if doc.final_score >= self.min_score_threshold
            ]

            logger.info(f"查询 '{query}' 最终返回 {len(filtered_docs)} 个文档")
            return filtered_docs

        except Exception as e:
            logger.error(f"两阶段检索失败: {e}")
            return []

    async def _recall_phase(
        self,
        query: str,
        filter_metadata: Optional[Dict[str, Any]],
        score_threshold: float
    ) -> List[Dict[str, Any]]:
        """
        召回阶段：从向量存储中检索大量相关文档

        Args:
            query: 查询字符串
            filter_metadata: 过滤条件
            score_threshold: 分数阈值

        Returns:
            召回的文档列表
        """
        try:
            # 使用更大的top_k值进行召回
            results = await self.vector_store.search(
                query=query,
                top_k=self.recall_top_k,
                filter_metadata=filter_metadata,
                score_threshold=score_threshold
            )

            # 转换为统一格式
            documents = []
            for doc, score in results:
                documents.append({
                    'id': getattr(doc, 'id', ''),
                    'content': getattr(doc, 'content', ''),
                    'metadata': getattr(doc, 'metadata', {}),
                    'score': float(score)
                })

            return documents

        except Exception as e:
            logger.error(f"召回阶段失败: {e}")
            return []

    async def _rerank_phase(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> List[DocumentScore]:
        """
        重排序阶段：使用交叉编码器精确排序

        Args:
            query: 查询字符串
            documents: 召回的文档列表

        Returns:
            重排序后的文档列表
        """
        try:
            reranked_docs = await self.reranker.rerank(
                query=query,
                documents=documents,
                top_k=self.final_top_k
            )
            return reranked_docs

        except Exception as e:
            logger.error(f"重排序阶段失败: {e}")
            # 如果重排序失败，按召回分数排序
            documents.sort(key=lambda x: x.get('score', 0), reverse=True)
            return [
                DocumentScore(
                    document_id=doc.get('id', ''),
                    content=doc.get('content', ''),
                    metadata=doc.get('metadata', {}),
                    recall_score=doc.get('score', 0),
                    rerank_score=0,
                    final_score=doc.get('score', 0)
                )
                for doc in documents[:self.final_top_k]
            ]

    def get_search_stats(self) -> Dict[str, Any]:
        """获取检索统计信息"""
        return {
            "recall_top_k": self.recall_top_k,
            "final_top_k": self.final_top_k,
            "min_score_threshold": self.min_score_threshold,
            "reranker_model": self.reranker.model_name if self.reranker.model else "simple"
        }