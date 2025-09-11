# -*- coding: utf-8 -*-
"""
文档重排序模块，用于提升RAG检索结果的相关性。
"""

from typing import List, Dict, Any
from sentence_transformers.cross_encoder import CrossEncoder

# 使用一个轻量级但高效的跨编码器模型
# 在首次使用时会自动下载
_reranker_model = None


def get_reranker_model():
    """
    单例模式加载重排序模型。
    """
    global _reranker_model
    if _reranker_model is None:
        print("Initializing reranker model (ms-marco-MiniLM-L-6-v2)...")
        _reranker_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        print("Reranker model initialized.")
    return _reranker_model


async def rerank_documents(query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    对检索到的文档列表进行重排序。

    Args:
        query: 用户的查询。
        documents: 一个文档字典列表，每个字典至少包含 'content' 键。

    Returns:
        一个按相关性得分从高到低排序的文档字典列表。
    """
    if not documents:
        return []

    try:
        model = get_reranker_model()

        # 创建模型需要的输入对
        sentence_pairs = [(query, doc.get('content', '')) for doc in documents]

        # 计算得分
        scores = model.predict(sentence_pairs)

        # 将得分添加到文档中
        for doc, score in zip(documents, scores):
            doc['rerank_score'] = float(score)

        # 按新得分排序
        sorted_documents = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)

        return sorted_documents

    except Exception as e:
        print(f"Reranking failed: {e}, returning original documents")
        # 如果重排序失败，返回原始文档
        return documents
