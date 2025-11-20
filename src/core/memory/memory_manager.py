#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mem0 记忆管理器
整合向量存储、HyDE检索和数据库持久化
"""

import logging
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from src.core.memory.vector_store import VectorStore
from src.core.memory.hyde_retriever import HyDERetriever
from src.dao.memory_dao import MemoryDAO
from src.core.security.redis_client import redis_client

logger = logging.getLogger(__name__)


class Mem0MemoryManager:
    """
    Mem0 记忆管理器
    
    职责：
    1. 记忆写入：提取事实 -> 向量化 -> 存储到向量库和SQL
    2. 记忆检索：HyDE增强查询 -> 向量检索 -> 返回相关记忆
    3. 缓存管理：使用Redis缓存高频访问的用户画像
    """
    
    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        embedding_model: str = "embeddinggemma",
        generation_model: str = "gemma3:4b",
        chroma_persist_dir: str = "./data/chroma"
    ):
        """
        初始化记忆管理器
        
        Args:
            ollama_base_url: Ollama服务地址
            embedding_model: 嵌入模型
            generation_model: 生成模型
            chroma_persist_dir: ChromaDB持久化目录
        """
        self.hyde_retriever = HyDERetriever(
            ollama_base_url=ollama_base_url,
            embedding_model=embedding_model,
            generation_model=generation_model
        )
        
        try:
            self.vector_store = VectorStore(persist_directory=chroma_persist_dir)
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            self.vector_store = None
        
        self.memory_dao = MemoryDAO()
        self.cache_ttl = 3600  # 缓存1小时
        
        logger.info("Mem0 Memory Manager initialized")
    
    async def add_memory(
        self,
        user_id: str,
        fact_content: str,
        fact_type: str = "general",
        source_session_id: Optional[str] = None,
        source_message_id: Optional[int] = None,
        validity_score: float = 1.0
    ) -> Optional[str]:
        """
        添加记忆
        
        Args:
            user_id: 用户ID
            fact_content: 事实内容
            fact_type: 事实类型
            source_session_id: 来源会话
            source_message_id: 来源消息
            validity_score: 有效性分数
            
        Returns:
            记忆ID
        """
        if not self.vector_store:
            logger.error("Vector store not available")
            return None
        
        try:
            # 1. 生成向量
            embedding = await self.hyde_retriever.embed_text(fact_content)
            if not embedding:
                logger.error("Failed to generate embedding for fact")
                return None
            
            # 2. 生成记忆ID
            memory_id = str(uuid.uuid4())
            
            # 3. 存储到向量库
            metadata = {
                "user_id": user_id,
                "fact_type": fact_type,
                "source_session_id": source_session_id or "",
                "validity_score": validity_score,
                "created_at": datetime.utcnow().isoformat()
            }
            
            success = self.vector_store.add_memory(
                memory_id=memory_id,
                content=fact_content,
                embedding=embedding,
                metadata=metadata
            )
            
            if not success:
                logger.error("Failed to add memory to vector store")
                return None
            
            # 4. 存储到SQL数据库
            db_result = await self.memory_dao.create_user_fact(
                user_id=user_id,
                fact_content=fact_content,
                fact_type=fact_type,
                source_session_id=source_session_id,
                source_message_id=source_message_id,
                validity_score=validity_score,
                embedding_id=memory_id
            )
            
            if not db_result:
                logger.error("Failed to save memory to database")
                # 尝试清理向量库中的记忆
                self.vector_store.delete_memory(memory_id)
                return None
            
            # 5. 清除用户缓存
            await self._invalidate_user_cache(user_id)
            
            logger.info(f"Added memory {memory_id} for user {user_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return None
    
    async def retrieve_memories(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        use_hyde: bool = True,
        fact_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检索相关记忆
        
        Args:
            query: 查询文本
            user_id: 用户ID
            top_k: 返回数量
            use_hyde: 是否使用HyDE
            fact_type: 事实类型过滤
            
        Returns:
            相关记忆列表
        """
        if not self.vector_store:
            logger.error("Vector store not available")
            return []
        
        try:
            # 1. 检查缓存
            cache_key = f"memory:query:{user_id}:{hash(query)}"
            cached = await redis_client.get_json(cache_key)
            if cached:
                logger.debug(f"Cache hit for query: {query[:50]}")
                return cached
            
            # 2. 使用HyDE生成查询向量
            query_embedding = await self.hyde_retriever.embed_query_with_hyde(
                query=query,
                user_context=None,  # 可以传入用户上下文
                use_hyde=use_hyde
            )
            
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            # 3. 向量检索
            filter_metadata = {}
            if fact_type:
                filter_metadata["fact_type"] = fact_type
            
            memories = self.vector_store.search_memories(
                query_embedding=query_embedding,
                user_id=user_id,
                top_k=top_k,
                filter_metadata=filter_metadata
            )
            
            # 4. 缓存结果
            await redis_client.set_json(cache_key, memories, expire=300)  # 缓存5分钟
            
            logger.info(f"Retrieved {len(memories)} memories for user {user_id}")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []
    
    async def get_user_context(
        self,
        user_id: str,
        max_facts: int = 10
    ) -> str:
        """
        获取用户上下文摘要
        
        Args:
            user_id: 用户ID
            max_facts: 最大事实数量
            
        Returns:
            格式化的用户上下文字符串
        """
        try:
            # 检查缓存
            cache_key = f"memory:context:{user_id}"
            cached = await redis_client.get(cache_key)
            if cached:
                return cached
            
            # 从数据库获取高质量事实
            facts = await self.memory_dao.get_user_facts(
                user_id=user_id,
                min_validity_score=0.7,
                limit=max_facts
            )
            
            if not facts:
                return ""
            
            # 格式化为上下文字符串
            context_lines = []
            for fact in facts:
                fact_type = fact.get('fact_type', 'general')
                content = fact.get('fact_content', '')
                context_lines.append(f"- [{fact_type}] {content}")
            
            context = "\n".join(context_lines)
            
            # 缓存结果
            await redis_client.set(cache_key, context, expire=self.cache_ttl)
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get user context: {e}")
            return ""
    
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        try:
            # 1. 从向量库删除
            if self.vector_store:
                self.vector_store.delete_memory(memory_id)
            
            # 2. 从数据库删除
            await self.memory_dao.delete_fact(memory_id)
            
            # 3. 清除缓存
            await self._invalidate_user_cache(user_id)
            
            logger.info(f"Deleted memory {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False
    
    async def delete_user_memories(self, user_id: str) -> bool:
        """
        删除用户的所有记忆
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        try:
            # 1. 从向量库删除
            if self.vector_store:
                self.vector_store.delete_user_memories(user_id)
            
            # 2. 从数据库删除
            await self.memory_dao.delete_user_facts(user_id)
            
            # 3. 清除缓存
            await self._invalidate_user_cache(user_id)
            
            logger.info(f"Deleted all memories for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user memories: {e}")
            return False
    
    async def _invalidate_user_cache(self, user_id: str):
        """清除用户相关的所有缓存"""
        try:
            # 清除上下文缓存
            await redis_client.delete(f"memory:context:{user_id}")
            # 清除查询缓存（使用模式匹配）
            # 注意：这需要Redis支持SCAN命令
            logger.debug(f"Invalidated cache for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取记忆系统统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "vector_store_available": self.vector_store is not None
        }
        
        if self.vector_store:
            stats.update(self.vector_store.get_collection_stats())
        
        return stats
