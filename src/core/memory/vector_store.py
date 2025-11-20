#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量存储管理器 - 基于 ChromaDB
低算力CPU方案的本地向量数据库
"""

import logging
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not installed. Vector store will not be available.")


class VectorStore:
    """
    向量存储管理器
    使用ChromaDB的嵌入式模式，适合低算力CPU环境
    """
    
    def __init__(
        self,
        persist_directory: str = "./data/chroma",
        collection_name: str = "user_memories"
    ):
        """
        初始化向量存储
        
        Args:
            persist_directory: 持久化目录
            collection_name: 集合名称
        """
        if not CHROMADB_AVAILABLE:
            raise RuntimeError("ChromaDB is not installed. Install with: pip install chromadb")
        
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # 初始化ChromaDB客户端（嵌入式模式）
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "User memory facts with embeddings"}
        )
        
        logger.info(f"Vector store initialized at {persist_directory}")
    
    def add_memory(
        self,
        memory_id: str,
        content: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        添加记忆到向量库
        
        Args:
            memory_id: 记忆唯一ID
            content: 记忆内容
            embedding: 向量表示
            metadata: 元数据（user_id, session_id, fact_type等）
            
        Returns:
            是否成功
        """
        try:
            self.collection.add(
                ids=[memory_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata]
            )
            logger.debug(f"Added memory {memory_id} to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add memory to vector store: {e}")
            return False
    
    def batch_add_memories(
        self,
        memory_ids: List[str],
        contents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> bool:
        """
        批量添加记忆
        
        Args:
            memory_ids: 记忆ID列表
            contents: 内容列表
            embeddings: 向量列表
            metadatas: 元数据列表
            
        Returns:
            是否成功
        """
        try:
            self.collection.add(
                ids=memory_ids,
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas
            )
            logger.info(f"Batch added {len(memory_ids)} memories to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to batch add memories: {e}")
            return False
    
    def search_memories(
        self,
        query_embedding: List[float],
        user_id: Optional[str] = None,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相关记忆
        
        Args:
            query_embedding: 查询向量
            user_id: 用户ID（用于过滤）
            top_k: 返回结果数量
            filter_metadata: 额外的元数据过滤条件
            
        Returns:
            相关记忆列表
        """
        try:
            # 构建过滤条件
            where_filter = {}
            if user_id:
                where_filter["user_id"] = user_id
            
            if filter_metadata:
                where_filter.update(filter_metadata)
            
            # 执行查询
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter if where_filter else None
            )
            
            # 格式化结果
            memories = []
            if results and results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    memory = {
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None,
                        'metadata': results['metadatas'][0][i] if 'metadatas' in results else {}
                    }
                    memories.append(memory)
            
            logger.debug(f"Found {len(memories)} relevant memories")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否成功
        """
        try:
            self.collection.delete(ids=[memory_id])
            logger.debug(f"Deleted memory {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False
    
    def delete_user_memories(self, user_id: str) -> bool:
        """
        删除用户的所有记忆
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        try:
            self.collection.delete(where={"user_id": user_id})
            logger.info(f"Deleted all memories for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user memories: {e}")
            return False
    
    def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        更新记忆
        
        Args:
            memory_id: 记忆ID
            content: 新内容
            embedding: 新向量
            metadata: 新元数据
            
        Returns:
            是否成功
        """
        try:
            update_data = {"ids": [memory_id]}
            
            if content is not None:
                update_data["documents"] = [content]
            if embedding is not None:
                update_data["embeddings"] = [embedding]
            if metadata is not None:
                update_data["metadatas"] = [metadata]
            
            self.collection.update(**update_data)
            logger.debug(f"Updated memory {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update memory: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        获取集合统计信息
        
        Returns:
            统计信息字典
        """
        try:
            count = self.collection.count()
            return {
                "total_memories": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
