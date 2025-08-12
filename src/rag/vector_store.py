# -*- coding: utf-8 -*-
"""
向量存储模块
提供文档向量化存储和检索功能
"""

import uuid
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from src.config.logging import get_logger

logger = get_logger("vector_store")


@dataclass
class Document:
    """文档数据类"""
    id: str
    content: str
    metadata: Dict[str, Any] = None
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.id:
            self.id = str(uuid.uuid4())


class VectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档到向量存储"""
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5, 
              filter_metadata: Dict[str, Any] = None) -> List[Tuple[Document, float]]:
        """搜索相似文档"""
        pass
    
    @abstractmethod
    def delete_documents(self, document_ids: List[str]) -> bool:
        """删除文档"""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """清空所有文档"""
        pass
    
    @abstractmethod
    def get_document_count(self) -> int:
        """获取文档数量"""
        pass


class ChromaVectorStore(VectorStore):
    """基于ChromaDB的向量存储实现"""
    
    def __init__(self, collection_name: str = "documents", persist_directory: str = None):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self._client = None
        self._collection = None
        self._embedding_service = None
        
    def _get_client(self):
        """获取ChromaDB客户端"""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
                
                if self.persist_directory:
                    # 持久化存储
                    self._client = chromadb.PersistentClient(
                        path=self.persist_directory,
                        settings=Settings(allow_reset=True)
                    )
                else:
                    # 内存存储
                    self._client = chromadb.EphemeralClient()
                    
                logger.info(f"ChromaDB客户端已初始化 (persist_dir: {self.persist_directory})")
                
            except ImportError:
                logger.error("chromadb未安装，无法使用向量存储功能")
                raise ImportError("请安装chromadb: pip install chromadb")
        
        return self._client
    
    def _get_collection(self):
        """获取或创建集合"""
        if self._collection is None:
            client = self._get_client()
            try:
                self._collection = client.get_collection(name=self.collection_name)
                logger.debug(f"获取现有集合: {self.collection_name}")
            except Exception:
                # 集合不存在，创建新集合
                self._collection = client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "文档向量存储集合"}
                )
                logger.info(f"创建新集合: {self.collection_name}")
        
        return self._collection
    
    def _get_embedding_service(self):
        """获取嵌入服务"""
        if self._embedding_service is None:
            from .embeddings import get_embedding_service
            self._embedding_service = get_embedding_service()
        return self._embedding_service
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档到向量存储"""
        try:
            collection = self._get_collection()
            embedding_service = self._get_embedding_service()
            
            # 生成嵌入向量
            texts = [doc.content for doc in documents]
            embeddings = embedding_service.embed_documents(texts)
            
            # 准备数据
            ids = []
            metadatas = []
            documents_text = []
            
            for doc, embedding in zip(documents, embeddings):
                ids.append(doc.id)
                metadatas.append(doc.metadata or {})
                documents_text.append(doc.content)
            
            # 添加到ChromaDB
            collection.add(
                ids=ids,
                documents=documents_text,
                metadatas=metadatas,
                embeddings=embeddings
            )
            
            logger.info(f"成功添加 {len(documents)} 个文档到向量存储")
            return ids
            
        except Exception as e:
            logger.error(f"添加文档到向量存储失败: {e}")
            raise
    
    def search(self, query: str, top_k: int = 5, 
              filter_metadata: Dict[str, Any] = None) -> List[Tuple[Document, float]]:
        """搜索相似文档"""
        try:
            collection = self._get_collection()
            embedding_service = self._get_embedding_service()
            
            # 生成查询向量
            query_embedding = embedding_service.embed_query(query)
            
            # 构建过滤条件
            where = filter_metadata if filter_metadata else None
            
            # 搜索
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where
            )
            
            # 格式化结果
            search_results = []
            if results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    document = Document(
                        id=doc_id,
                        content=results['documents'][0][i] if results['documents'][0] else "",
                        metadata=results['metadatas'][0][i] if results['metadatas'][0] else {}
                    )
                    
                    # 距离转换为相似度分数 (1 - distance)
                    distance = results['distances'][0][i] if results['distances'][0] else 1.0
                    similarity_score = max(0.0, 1.0 - distance)
                    
                    search_results.append((document, similarity_score))
            
            logger.debug(f"搜索到 {len(search_results)} 个相关文档")
            return search_results
            
        except Exception as e:
            logger.error(f"搜索文档失败: {e}")
            return []
    
    def delete_documents(self, document_ids: List[str]) -> bool:
        """删除文档"""
        try:
            collection = self._get_collection()
            collection.delete(ids=document_ids)
            logger.info(f"成功删除 {len(document_ids)} 个文档")
            return True
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def clear(self) -> bool:
        """清空所有文档"""
        try:
            client = self._get_client()
            # 删除现有集合
            try:
                client.delete_collection(name=self.collection_name)
                logger.info(f"已删除集合: {self.collection_name}")
            except Exception:
                pass
            
            # 重新创建空集合
            self._collection = client.create_collection(
                name=self.collection_name,
                metadata={"description": "文档向量存储集合"}
            )
            logger.info(f"已重新创建空集合: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"清空向量存储失败: {e}")
            return False
    
    def get_document_count(self) -> int:
        """获取文档数量"""
        try:
            collection = self._get_collection()
            return collection.count()
        except Exception as e:
            logger.error(f"获取文档数量失败: {e}")
            return 0


class MemoryVectorStore(VectorStore):
    """内存向量存储实现（用于测试或简单场景）"""
    
    def __init__(self):
        self._documents: Dict[str, Document] = {}
        self._embedding_service = None
        
    def _get_embedding_service(self):
        """获取嵌入服务"""
        if self._embedding_service is None:
            from .embeddings import get_embedding_service
            self._embedding_service = get_embedding_service()
        return self._embedding_service
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档到内存存储"""
        try:
            embedding_service = self._get_embedding_service()
            
            # 生成嵌入向量
            texts = [doc.content for doc in documents]
            embeddings = embedding_service.embed_documents(texts)
            
            # 存储文档
            ids = []
            for doc, embedding in zip(documents, embeddings):
                doc.embedding = embedding
                self._documents[doc.id] = doc
                ids.append(doc.id)
            
            logger.info(f"成功添加 {len(documents)} 个文档到内存存储")
            return ids
            
        except Exception as e:
            logger.error(f"添加文档到内存存储失败: {e}")
            raise
    
    def search(self, query: str, top_k: int = 5, 
              filter_metadata: Dict[str, Any] = None) -> List[Tuple[Document, float]]:
        """搜索相似文档"""
        try:
            if not self._documents:
                return []
            
            embedding_service = self._get_embedding_service()
            query_embedding = embedding_service.embed_query(query)
            
            # 计算相似度
            similarities = []
            for doc in self._documents.values():
                if doc.embedding:
                    # 应用过滤条件
                    if filter_metadata:
                        match = all(
                            doc.metadata.get(k) == v 
                            for k, v in filter_metadata.items()
                        )
                        if not match:
                            continue
                    
                    # 计算余弦相似度
                    similarity = self._cosine_similarity(query_embedding, doc.embedding)
                    similarities.append((doc, similarity))
            
            # 排序并返回top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"搜索文档失败: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        import math
        
        # 计算点积
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # 计算向量长度
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def delete_documents(self, document_ids: List[str]) -> bool:
        """删除文档"""
        try:
            for doc_id in document_ids:
                if doc_id in self._documents:
                    del self._documents[doc_id]
            logger.info(f"成功删除 {len(document_ids)} 个文档")
            return True
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def clear(self) -> bool:
        """清空所有文档"""
        try:
            self._documents.clear()
            logger.info("已清空内存向量存储")
            return True
        except Exception as e:
            logger.error(f"清空内存存储失败: {e}")
            return False
    
    def get_document_count(self) -> int:
        """获取文档数量"""
        return len(self._documents)
