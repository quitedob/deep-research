# -*- coding: utf-8 -*-
"""
RAG 检索服务
实现多种检索策略：向量检索、混合检索等
支持知识库文档的智能检索
"""

import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from enum import Enum
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class RetrievalStrategy(Enum):
    """检索策略枚举"""
    VECTOR_ONLY = "vector_only"  # 仅向量检索
    HYBRID = "hybrid"  # 混合检索（向量+关键词）
    SEMANTIC = "semantic"  # 语义检索
    KEYWORD = "keyword"  # 关键词检索


@dataclass
class RetrievalResult:
    """检索结果"""
    content: str
    metadata: Dict[str, Any]
    score: float
    source: str
    chunk_id: str


class BaseRetriever:
    """基础检索器"""

    def __init__(self, vector_store=None, config: Optional[Dict[str, Any]] = None):
        """
        初始化检索器

        Args:
            vector_store: 向量存储实例
            config: 配置参数
        """
        self.vector_store = vector_store
        self.config = config or {}

    async def search(
        self,
        query: str,
        strategy: RetrievalStrategy = RetrievalStrategy.VECTOR_ONLY,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[RetrievalResult]:
        """
        执行检索

        Args:
            query: 查询字符串
            strategy: 检索策略
            top_k: 返回的文档数量
            filter_metadata: 元数据过滤条件
            score_threshold: 分数阈值

        Returns:
            检索结果列表
        """
        raise NotImplementedError("子类必须实现search方法")


class VectorRetriever(BaseRetriever):
    """向量检索器"""

    async def search(
        self,
        query: str,
        strategy: RetrievalStrategy = RetrievalStrategy.VECTOR_ONLY,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[RetrievalResult]:
        """
        执行向量检索

        Args:
            query: 查询字符串
            strategy: 检索策略（此实现主要用于VECTOR_ONLY）
            top_k: 返回的文档数量
            filter_metadata: 元数据过滤条件
            score_threshold: 分数阈值

        Returns:
            检索结果列表
        """
        if not self.vector_store:
            logger.warning("向量存储未初始化，返回空结果")
            return []

        try:
            # 执行向量检索
            # 检查向量存储的search方法签名
            import inspect
            sig = inspect.signature(self.vector_store.search)
            if 'query' in sig.parameters:
                # 向量存储支持query参数
                results = await self.vector_store.search(
                    query=query,
                    top_k=top_k,
                    filter_metadata=filter_metadata,
                    score_threshold=score_threshold
                )
            else:
                # 向量存储需要query_embedding参数，生成embedding
                try:
                    from src.llms.embeddings import get_embedding_model
                    embedding_model = get_embedding_model()
                    query_embedding = await embedding_model.get_embedding(query)

                    results = await self.vector_store.search(
                        query_embedding=query_embedding,
                        top_k=top_k,
                        filter_metadata=filter_metadata,
                        score_threshold=score_threshold
                    )
                except Exception as e:
                    logger.warning(f"生成query embedding失败: {e}，使用关键词匹配")
                    # 回退到关键词匹配
                    results = await self._keyword_search(query, top_k, filter_metadata, score_threshold)

            # 转换为RetrievalResult格式
            retrieval_results = []
            for doc, score in results:
                result = RetrievalResult(
                    content=getattr(doc, 'content', ''),
                    metadata=getattr(doc, 'metadata', {}),
                    score=float(score),
                    source=getattr(doc, 'source', 'unknown'),
                    chunk_id=getattr(doc, 'chunk_id', getattr(doc, 'id', ''))
                )
                retrieval_results.append(result)

            logger.info(f"向量检索完成，返回 {len(retrieval_results)} 个结果")
            return retrieval_results

        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []

    async def _keyword_search(
        self,
        query: str,
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]],
        score_threshold: float
    ) -> List[Tuple[Any, float]]:
        """
        关键词搜索回退方法

        Args:
            query: 查询字符串
            top_k: 返回的文档数量
            filter_metadata: 元数据过滤条件
            score_threshold: 分数阈值

        Returns:
            (文档, 分数) 元组列表
        """
        try:
            # 如果向量存储有documents属性，进行关键词匹配
            if hasattr(self.vector_store, 'documents'):
                query_terms = set(query.lower().split())
                scored_docs = []

                for doc in self.vector_store.documents:
                    # 应用元数据过滤
                    if filter_metadata:
                        if not self._matches_filter(doc.metadata, filter_metadata):
                            continue

                    content = getattr(doc, 'content', '').lower()
                    # 计算关键词匹配分数
                    term_matches = sum(1 for term in query_terms if term in content)
                    score = term_matches / len(query_terms) if query_terms else 0

                    if score >= score_threshold:
                        scored_docs.append((doc, score))

                # 排序并返回top_k
                scored_docs.sort(key=lambda x: x[1], reverse=True)
                return scored_docs[:top_k]

            return []
        except Exception as e:
            logger.error(f"关键词搜索失败: {e}")
            return []

    def _matches_filter(self, metadata: Dict[str, Any], filter_metadata: Dict[str, Any]) -> bool:
        """检查元数据是否匹配过滤条件"""
        for key, value in filter_metadata.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True


class HybridRetriever(BaseRetriever):
    """混合检索器（向量+关键词）"""

    async def search(
        self,
        query: str,
        strategy: RetrievalStrategy = RetrievalStrategy.HYBRID,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[RetrievalResult]:
        """
        执行混合检索

        Args:
            query: 查询字符串
            strategy: 检索策略
            top_k: 返回的文档数量
            filter_metadata: 元数据过滤条件
            score_threshold: 分数阈值

        Returns:
            检索结果列表
        """
        if not self.vector_store:
            logger.warning("向量存储未初始化，返回空结果")
            return []

        try:
            # 获取向量检索结果
            vector_results = await self.vector_store.search(
                query=query,
                top_k=top_k * 2,  # 获取更多结果用于融合
                filter_metadata=filter_metadata,
                score_threshold=score_threshold
            )

            # 关键词匹配评分
            query_terms = set(query.lower().split())
            hybrid_results = []

            for doc, vector_score in vector_results:
                content = getattr(doc, 'content', '').lower()

                # 计算关键词匹配分数
                term_matches = sum(1 for term in query_terms if term in content)
                max_possible_matches = len(query_terms)
                keyword_score = term_matches / max_possible_matches if max_possible_matches > 0 else 0

                # 融合分数（向量分数和关键词分数）
                hybrid_score = 0.7 * float(vector_score) + 0.3 * keyword_score

                result = RetrievalResult(
                    content=getattr(doc, 'content', ''),
                    metadata=getattr(doc, 'metadata', {}),
                    score=hybrid_score,
                    source=getattr(doc, 'source', 'unknown'),
                    chunk_id=getattr(doc, 'chunk_id', getattr(doc, 'id', ''))
                )
                hybrid_results.append(result)

            # 按混合分数排序
            hybrid_results.sort(key=lambda x: x.score, reverse=True)

            logger.info(f"混合检索完成，返回 {len(hybrid_results[:top_k])} 个结果")
            return hybrid_results[:top_k]

        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            return []


class SimpleRetriever(BaseRetriever):
    """简单检索器（用于测试或无向量存储的情况）"""

    def __init__(self, mock_data: Optional[List[Dict[str, Any]]] = None, config: Optional[Dict[str, Any]] = None):
        """
        初始化简单检索器

        Args:
            mock_data: 模拟数据
            config: 配置参数
        """
        super().__init__(None, config)
        self.mock_data = mock_data or []

    async def search(
        self,
        query: str,
        strategy: RetrievalStrategy = RetrievalStrategy.KEYWORD,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[RetrievalResult]:
        """
        执行简单检索

        Args:
            query: 查询字符串
            strategy: 检索策略
            top_k: 返回的文档数量
            filter_metadata: 元数据过滤条件
            score_threshold: 分数阈值

        Returns:
            检索结果列表
        """
        try:
            if not self.mock_data:
                # 生成一些模拟数据
                self.mock_data = self._generate_mock_data(query)

            # 简单的关键词匹配
            query_terms = set(query.lower().split())
            scored_results = []

            for i, doc in enumerate(self.mock_data):
                content = doc.get('content', '').lower()
                metadata = doc.get('metadata', {})

                # 应用元数据过滤
                if filter_metadata:
                    if not self._matches_filter(metadata, filter_metadata):
                        continue

                # 计算匹配分数
                term_matches = sum(1 for term in query_terms if term in content)
                score = term_matches / len(query_terms) if query_terms else 0

                if score >= score_threshold:
                    result = RetrievalResult(
                        content=doc.get('content', ''),
                        metadata=metadata,
                        score=score,
                        source=doc.get('source', 'mock'),
                        chunk_id=doc.get('chunk_id', f'mock_{i}')
                    )
                    scored_results.append(result)

            # 排序并返回top_k
            scored_results.sort(key=lambda x: x.score, reverse=True)

            logger.info(f"简单检索完成，返回 {len(scored_results[:top_k])} 个结果")
            return scored_results[:top_k]

        except Exception as e:
            logger.error(f"简单检索失败: {e}")
            return []

    def _generate_mock_data(self, query: str) -> List[Dict[str, Any]]:
        """生成模拟数据"""
        return [
            {
                'content': f'这是一个关于{query}的示例文档。包含了一些相关信息和背景知识。',
                'metadata': {'source': 'mock', 'type': 'example'},
                'source': 'mock',
                'chunk_id': 'mock_1'
            },
            {
                'content': f'{query}是一个重要的研究主题，有很多值得探讨的方面和应用场景。',
                'metadata': {'source': 'mock', 'type': 'example'},
                'source': 'mock',
                'chunk_id': 'mock_2'
            },
            {
                'content': f'在讨论{query}时，我们需要考虑多个因素和不同的观点。',
                'metadata': {'source': 'mock', 'type': 'example'},
                'source': 'mock',
                'chunk_id': 'mock_3'
            }
        ]

    def _matches_filter(self, metadata: Dict[str, Any], filter_metadata: Dict[str, Any]) -> bool:
        """检查元数据是否匹配过滤条件"""
        for key, value in filter_metadata.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True


# 全局检索器实例
_default_retriever = None


def get_retriever(retriever_type: str = "simple", **kwargs) -> BaseRetriever:
    """
    获取检索器实例

    Args:
        retriever_type: 检索器类型 ('vector', 'hybrid', 'simple')
        **kwargs: 初始化参数

    Returns:
        检索器实例
    """
    global _default_retriever

    if _default_retriever is None:
        if retriever_type == "vector":
            _default_retriever = VectorRetriever(**kwargs)
        elif retriever_type == "hybrid":
            _default_retriever = HybridRetriever(**kwargs)
        else:
            _default_retriever = SimpleRetriever(**kwargs)

    return _default_retriever


async def search_documents(
    query: str,
    strategy: RetrievalStrategy = RetrievalStrategy.VECTOR_ONLY,
    top_k: int = 10,
    filter_metadata: Optional[Dict[str, Any]] = None,
    score_threshold: float = 0.0
) -> List[RetrievalResult]:
    """
    检索文档的主入口函数

    Args:
        query: 查询字符串
        strategy: 检索策略
        top_k: 返回的文档数量
        filter_metadata: 元数据过滤条件
        score_threshold: 分数阈值

    Returns:
        检索结果列表
    """
    retriever = get_retriever()

    try:
        results = await retriever.search(
            query=query,
            strategy=strategy,
            top_k=top_k,
            filter_metadata=filter_metadata,
            score_threshold=score_threshold
        )
        return results

    except Exception as e:
        logger.error(f"文档检索失败: {e}")
        # 返回空结果而不是抛出异常
        return []
