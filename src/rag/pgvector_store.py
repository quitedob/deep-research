# -*- coding: utf-8 -*-
"""
基于 PostgreSQL + pgvector 的向量存储实现
提供高性能的向量检索和证据链支持
"""

import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json

from sqlalchemy import select, delete, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector

from ..sqlmodel.rag_models import Document, Chunk, Embedding, Evidence
from ..llms.embeddings import get_embedding_service
from pkg.db import get_db_session
from .vector_store import VectorStore, Document as VectorDocument

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """向量搜索结果"""
    chunk_id: int
    document_id: int
    content: str
    score: float
    source_url: Optional[str] = None
    snippet: Optional[str] = None
    citation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PgVectorStore(VectorStore):
    """基于 PostgreSQL + pgvector 的向量存储"""
    
    def __init__(self, embedding_dim: int = 1536):
        self.embedding_dim = embedding_dim
        self._embedding_service = None
    
    def _get_embedding_service(self):
        """获取嵌入服务"""
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service()
        return self._embedding_service
    
    async def add_documents(self, documents: List[VectorDocument]) -> List[str]:
        """添加文档到向量存储"""
        try:
            embedding_service = self._get_embedding_service()
            
            async for session in get_db_session():
                # 生成嵌入向量
                texts = [doc.content for doc in documents]
                embeddings = await embedding_service.embed_documents(texts)
                
                added_ids = []
                
                for doc, embedding in zip(documents, embeddings):
                    # 创建文档记录
                    db_doc = Document(
                        original_filename=doc.metadata.get('filename', 'unknown'),
                        source_url=doc.metadata.get('source_url'),
                        text=doc.content,
                        metadata=doc.metadata,
                        user_id=doc.metadata.get('user_id')
                    )
                    session.add(db_doc)
                    await session.flush()  # 获取文档ID
                    
                    # 创建分块记录
                    chunk = Chunk(
                        document_id=db_doc.id,
                        index=0,
                        text=doc.content,
                        start_pos=doc.metadata.get('start_pos'),
                        end_pos=doc.metadata.get('end_pos'),
                        citation_id=doc.metadata.get('citation_id', str(uuid.uuid4())),
                        metadata=doc.metadata
                    )
                    session.add(chunk)
                    await session.flush()  # 获取分块ID
                    
                    # 创建嵌入记录
                    db_embedding = Embedding(
                        chunk_id=chunk.id,
                        vector=embedding,
                        vector_json=json.dumps(embedding),  # 备用存储
                        model_name=embedding_service.model_name if hasattr(embedding_service, 'model_name') else 'unknown'
                    )
                    session.add(db_embedding)
                    
                    added_ids.append(str(chunk.id))
                
                await session.commit()
                logger.info(f"成功添加 {len(documents)} 个文档到 pgvector 存储")
                return added_ids
                
        except Exception as e:
            logger.error(f"添加文档到 pgvector 存储失败: {e}")
            raise
    
    async def search(
        self, 
        query: str, 
        top_k: int = 5, 
        filter_metadata: Dict[str, Any] = None,
        score_threshold: float = 0.0
    ) -> List[Tuple[VectorDocument, float]]:
        """向量搜索"""
        try:
            embedding_service = self._get_embedding_service()
            query_embedding = await embedding_service.embed_query(query)
            
            async for session in get_db_session():
                # 构建查询
                query_stmt = (
                    select(
                        Chunk.id,
                        Chunk.text,
                        Chunk.citation_id,
                        Chunk.metadata,
                        Document.id.label('document_id'),
                        Document.source_url,
                        Document.original_filename,
                        Embedding.vector.cosine_distance(query_embedding).label('distance')
                    )
                    .join(Embedding, Chunk.id == Embedding.chunk_id)
                    .join(Document, Chunk.document_id == Document.id)
                    .where(Embedding.vector.is_not(None))
                )
                
                # 应用过滤条件
                if filter_metadata:
                    for key, value in filter_metadata.items():
                        if key == 'user_id':
                            query_stmt = query_stmt.where(Document.user_id == value)
                        elif key == 'source_type':
                            query_stmt = query_stmt.where(
                                func.jsonb_extract_path_text(Chunk.metadata, 'source_type') == value
                            )
                
                # 排序和限制
                query_stmt = query_stmt.order_by('distance').limit(top_k)
                
                result = await session.execute(query_stmt)
                rows = result.fetchall()
                
                # 转换结果
                search_results = []
                for row in rows:
                    # 距离转换为相似度分数 (1 - distance)
                    similarity_score = max(0.0, 1.0 - row.distance)
                    
                    if similarity_score >= score_threshold:
                        doc = VectorDocument(
                            id=str(row.id),
                            content=row.text,
                            metadata={
                                'document_id': row.document_id,
                                'source_url': row.source_url,
                                'filename': row.original_filename,
                                'citation_id': row.citation_id,
                                **(row.metadata or {})
                            }
                        )
                        search_results.append((doc, similarity_score))
                
                logger.debug(f"pgvector 搜索到 {len(search_results)} 个相关文档")
                return search_results
                
        except Exception as e:
            logger.error(f"pgvector 搜索失败: {e}")
            return []
    
    async def search_with_evidence(
        self,
        query: str,
        top_k: int = 5,
        conversation_id: Optional[str] = None,
        research_session_id: Optional[str] = None
    ) -> List[SearchResult]:
        """带证据链的搜索"""
        try:
            embedding_service = self._get_embedding_service()
            query_embedding = await embedding_service.embed_query(query)
            
            async for session in get_db_session():
                # 执行向量搜索
                query_stmt = (
                    select(
                        Chunk.id,
                        Chunk.text,
                        Chunk.citation_id,
                        Chunk.snippet_html,
                        Chunk.metadata,
                        Document.id.label('document_id'),
                        Document.source_url,
                        Document.original_filename,
                        Embedding.vector.cosine_distance(query_embedding).label('distance')
                    )
                    .join(Embedding, Chunk.id == Embedding.chunk_id)
                    .join(Document, Chunk.document_id == Document.id)
                    .where(Embedding.vector.is_not(None))
                    .order_by('distance')
                    .limit(top_k)
                )
                
                result = await session.execute(query_stmt)
                rows = result.fetchall()
                
                # 转换为搜索结果并记录证据
                search_results = []
                for row in rows:
                    similarity_score = max(0.0, 1.0 - row.distance)
                    
                    # 创建证据记录
                    evidence = Evidence(
                        conversation_id=conversation_id,
                        research_session_id=research_session_id,
                        source_type='document',
                        source_url=row.source_url,
                        source_title=row.original_filename,
                        content=row.text,
                        snippet=row.text[:200] + '...' if len(row.text) > 200 else row.text,
                        relevance_score=similarity_score,
                        confidence_score=similarity_score,
                        metadata={
                            'chunk_id': row.id,
                            'document_id': row.document_id,
                            'search_query': query
                        }
                    )
                    session.add(evidence)
                    
                    search_result = SearchResult(
                        chunk_id=row.id,
                        document_id=row.document_id,
                        content=row.text,
                        score=similarity_score,
                        source_url=row.source_url,
                        snippet=row.snippet_html or row.text[:200],
                        citation_id=row.citation_id,
                        metadata=row.metadata
                    )
                    search_results.append(search_result)
                
                await session.commit()
                logger.info(f"记录了 {len(search_results)} 条证据到证据链")
                return search_results
                
        except Exception as e:
            logger.error(f"带证据链的搜索失败: {e}")
            return []
    
    async def delete_documents(self, document_ids: List[str]) -> bool:
        """删除文档"""
        try:
            async for session in get_db_session():
                # 删除文档（级联删除分块和嵌入）
                stmt = delete(Document).where(Document.id.in_([int(id) for id in document_ids]))
                await session.execute(stmt)
                await session.commit()
                
                logger.info(f"成功删除 {len(document_ids)} 个文档")
                return True
                
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    async def clear(self) -> bool:
        """清空所有文档"""
        try:
            async for session in get_db_session():
                # 删除所有文档（级联删除）
                await session.execute(delete(Document))
                await session.commit()
                
                logger.info("已清空 pgvector 存储")
                return True
                
        except Exception as e:
            logger.error(f"清空 pgvector 存储失败: {e}")
            return False
    
    async def get_document_count(self) -> int:
        """获取文档数量"""
        try:
            async for session in get_db_session():
                result = await session.execute(select(func.count(Document.id)))
                count = result.scalar()
                return count or 0
                
        except Exception as e:
            logger.error(f"获取文档数量失败: {e}")
            return 0
    
    async def create_vector_index(self, index_type: str = 'ivfflat'):
        """创建向量索引以提升性能"""
        try:
            async for session in get_db_session():
                if index_type == 'ivfflat':
                    # IVFFlat 索引 - 适合大多数场景
                    await session.execute(text(
                        "CREATE INDEX IF NOT EXISTS embeddings_vector_idx "
                        "ON embeddings USING ivfflat (vector vector_cosine_ops) "
                        "WITH (lists = 100)"
                    ))
                elif index_type == 'hnsw':
                    # HNSW 索引 - 更高精度但更慢
                    await session.execute(text(
                        "CREATE INDEX IF NOT EXISTS embeddings_vector_hnsw_idx "
                        "ON embeddings USING hnsw (vector vector_cosine_ops) "
                        "WITH (m = 16, ef_construction = 64)"
                    ))
                
                await session.commit()
                logger.info(f"成功创建 {index_type} 向量索引")
                
        except Exception as e:
            logger.error(f"创建向量索引失败: {e}")
            raise


# 全局实例
_pgvector_store = None

def get_pgvector_store() -> PgVectorStore:
    """获取全局 pgvector 存储实例"""
    global _pgvector_store
    if _pgvector_store is None:
        _pgvector_store = PgVectorStore()
    return _pgvector_store