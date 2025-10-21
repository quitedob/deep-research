# -*- coding: utf-8 -*-
"""
记忆存储器
提供持久化的记忆存储和检索功能
"""

import time
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from pathlib import Path

from .conversation_buffer import ChatMessage, ConversationBuffer
from .summarizer import get_summary_service

logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    """记忆条目数据类"""
    id: str
    content: str
    metadata: Dict[str, Any]
    timestamp: float
    memory_type: str = "general"
    importance: float = 0.5
    access_count: int = 0
    last_accessed: float = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """从字典创建实例"""
        return cls(**data)
    
    def update_access(self):
        """更新访问信息"""
        self.access_count += 1
        self.last_accessed = time.time()

class BaseMemoryStore(ABC):
    """记忆存储基类"""
    
    @abstractmethod
    async def store_memory(self, memory: MemoryEntry) -> bool:
        """存储记忆"""
        pass
    
    @abstractmethod
    async def retrieve_memories(
        self, 
        query: str = None, 
        memory_type: str = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """检索记忆"""
        pass
    
    @abstractmethod
    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """更新记忆"""
        pass
    
    @abstractmethod
    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        pass
    
    @abstractmethod
    async def clear_memories(self, memory_type: str = None) -> bool:
        """清空记忆"""
        pass

class InMemoryStore(BaseMemoryStore):
    """内存记忆存储"""
    
    def __init__(self):
        self.memories: Dict[str, MemoryEntry] = {}
    
    async def store_memory(self, memory: MemoryEntry) -> bool:
        """存储记忆到内存"""
        try:
            self.memories[memory.id] = memory
            logger.debug(f"Stored memory: {memory.id}")
            return True
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return False
    
    async def retrieve_memories(
        self, 
        query: str = None, 
        memory_type: str = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """从内存检索记忆"""
        try:
            memories = list(self.memories.values())
            
            # 按类型过滤
            if memory_type:
                memories = [m for m in memories if m.memory_type == memory_type]
            
            # 简单的文本搜索
            if query:
                query_lower = query.lower()
                memories = [
                    m for m in memories 
                    if query_lower in m.content.lower()
                ]
            
            # 按重要性和最近访问时间排序
            memories.sort(
                key=lambda m: (m.importance, m.last_accessed), 
                reverse=True
            )
            
            # 更新访问信息
            for memory in memories[:limit]:
                memory.update_access()
            
            return memories[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []
    
    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """更新记忆"""
        try:
            if memory_id in self.memories:
                memory = self.memories[memory_id]
                for key, value in updates.items():
                    if hasattr(memory, key):
                        setattr(memory, key, value)
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        try:
            if memory_id in self.memories:
                del self.memories[memory_id]
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False
    
    async def clear_memories(self, memory_type: str = None) -> bool:
        """清空记忆"""
        try:
            if memory_type:
                to_delete = [
                    memory_id for memory_id, memory in self.memories.items()
                    if memory.memory_type == memory_type
                ]
                for memory_id in to_delete:
                    del self.memories[memory_id]
            else:
                self.memories.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing memories: {e}")
            return False

class FileMemoryStore(BaseMemoryStore):
    """文件记忆存储"""
    
    def __init__(self, storage_path: str = "memories.json"):
        self.storage_path = Path(storage_path)
        self.memories: Dict[str, MemoryEntry] = {}
        self._load_memories()
    
    def _load_memories(self):
        """从文件加载记忆"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.memories = {
                    memory_id: MemoryEntry.from_dict(memory_data)
                    for memory_id, memory_data in data.items()
                }
                
                logger.info(f"Loaded {len(self.memories)} memories from {self.storage_path}")
        except Exception as e:
            logger.error(f"Error loading memories: {e}")
            self.memories = {}
    
    def _save_memories(self):
        """保存记忆到文件"""
        try:
            # 确保目录存在
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                memory_id: memory.to_dict()
                for memory_id, memory in self.memories.items()
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving memories: {e}")
    
    async def store_memory(self, memory: MemoryEntry) -> bool:
        """存储记忆到文件"""
        try:
            self.memories[memory.id] = memory
            self._save_memories()
            logger.debug(f"Stored memory to file: {memory.id}")
            return True
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return False
    
    async def retrieve_memories(
        self, 
        query: str = None, 
        memory_type: str = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """从文件检索记忆"""
        try:
            memories = list(self.memories.values())
            
            # 按类型过滤
            if memory_type:
                memories = [m for m in memories if m.memory_type == memory_type]
            
            # 简单的文本搜索
            if query:
                query_lower = query.lower()
                memories = [
                    m for m in memories 
                    if query_lower in m.content.lower()
                ]
            
            # 按重要性和最近访问时间排序
            memories.sort(
                key=lambda m: (m.importance, m.last_accessed), 
                reverse=True
            )
            
            # 更新访问信息
            for memory in memories[:limit]:
                memory.update_access()
            
            # 保存更新的访问信息
            if memories:
                self._save_memories()
            
            return memories[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []
    
    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """更新记忆"""
        try:
            if memory_id in self.memories:
                memory = self.memories[memory_id]
                for key, value in updates.items():
                    if hasattr(memory, key):
                        setattr(memory, key, value)
                self._save_memories()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        try:
            if memory_id in self.memories:
                del self.memories[memory_id]
                self._save_memories()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False
    
    async def clear_memories(self, memory_type: str = None) -> bool:
        """清空记忆"""
        try:
            if memory_type:
                to_delete = [
                    memory_id for memory_id, memory in self.memories.items()
                    if memory.memory_type == memory_type
                ]
                for memory_id in to_delete:
                    del self.memories[memory_id]
            else:
                self.memories.clear()
            
            self._save_memories()
            return True
        except Exception as e:
            logger.error(f"Error clearing memories: {e}")
            return False

class VectorMemoryStore(BaseMemoryStore):
    """向量记忆存储（集成RAG）"""
    
    def __init__(self, collection_name: str = "memories"):
        self.collection_name = collection_name
        self.file_store = FileMemoryStore(f"memories_{collection_name}.json")
        
        # 延迟初始化向量存储
        self._vector_store = None
        self._embedding_service = None
    
    async def _ensure_vector_store(self):
        """确保向量存储已初始化"""
        if self._vector_store is None:
            from ..rag.vector_store import ChromaVectorStore
            from ..llms.embeddings import get_embedding_service
            
            self._vector_store = ChromaVectorStore(collection_name=self.collection_name)
            self._embedding_service = get_embedding_service()
    
    async def store_memory(self, memory: MemoryEntry) -> bool:
        """存储记忆到向量存储"""
        try:
            # 存储到文件
            await self.file_store.store_memory(memory)
            
            # 存储到向量存储
            await self._ensure_vector_store()
            
            # 生成嵌入
            embedding = await self._embedding_service.embed_single_text(memory.content)
            
            # 添加到向量存储
            success = await self._vector_store.add_documents(
                ids=[memory.id],
                documents=[memory.content],
                embeddings=[embedding],
                metadatas=[memory.metadata]
            )
            
            logger.debug(f"Stored memory to vector store: {memory.id}")
            return success
            
        except Exception as e:
            logger.error(f"Error storing memory to vector store: {e}")
            return False
    
    async def retrieve_memories(
        self, 
        query: str = None, 
        memory_type: str = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """从向量存储检索记忆"""
        try:
            if query:
                # 使用向量搜索
                await self._ensure_vector_store()
                
                # 生成查询嵌入
                query_embedding = await self._embedding_service.embed_single_text(query)
                
                # 向量搜索
                results = await self._vector_store.search(
                    query_embeddings=[query_embedding],
                    n_results=limit * 2  # 获取更多结果用于过滤
                )
                
                # 从文件存储中获取完整的记忆信息
                memory_ids = results.get("ids", [[]])[0]
                retrieved_memories = []
                
                for memory_id in memory_ids:
                    if memory_id in self.file_store.memories:
                        memory = self.file_store.memories[memory_id]
                        
                        # 按类型过滤
                        if memory_type and memory.memory_type != memory_type:
                            continue
                        
                        memory.update_access()
                        retrieved_memories.append(memory)
                        
                        if len(retrieved_memories) >= limit:
                            break
                
                # 保存更新的访问信息
                if retrieved_memories:
                    self.file_store._save_memories()
                
                return retrieved_memories
            else:
                # 回退到文件存储搜索
                return await self.file_store.retrieve_memories(
                    query, memory_type, limit
                )
                
        except Exception as e:
            logger.error(f"Error retrieving memories from vector store: {e}")
            # 回退到文件存储
            return await self.file_store.retrieve_memories(query, memory_type, limit)
    
    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """更新记忆"""
        # 更新文件存储
        success = await self.file_store.update_memory(memory_id, updates)
        
        if success and 'content' in updates:
            # 如果内容更新了，需要更新向量存储
            try:
                await self._ensure_vector_store()
                
                # 重新生成嵌入
                new_content = updates['content']
                embedding = await self._embedding_service.embed_single_text(new_content)
                
                # 更新向量存储
                await self._vector_store.update_documents(
                    ids=[memory_id],
                    documents=[new_content],
                    embeddings=[embedding]
                )
                
            except Exception as e:
                logger.error(f"Error updating memory in vector store: {e}")
        
        return success
    
    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        # 从文件存储删除
        success = await self.file_store.delete_memory(memory_id)
        
        if success:
            try:
                await self._ensure_vector_store()
                
                # 从向量存储删除
                await self._vector_store.delete_documents([memory_id])
                
            except Exception as e:
                logger.error(f"Error deleting memory from vector store: {e}")
        
        return success
    
    async def clear_memories(self, memory_type: str = None) -> bool:
        """清空记忆"""
        if memory_type:
            # 按类型删除
            memories_to_delete = []
            for memory_id, memory in self.file_store.memories.items():
                if memory.memory_type == memory_type:
                    memories_to_delete.append(memory_id)
            
            for memory_id in memories_to_delete:
                await self.delete_memory(memory_id)
            
            return True
        else:
            # 清空所有
            success = await self.file_store.clear_memories()
            
            if success:
                try:
                    await self._ensure_vector_store()
                    
                    # 清空向量存储
                    await self._vector_store.clear()
                    
                except Exception as e:
                    logger.error(f"Error clearing vector store: {e}")
            
            return success

class MemoryManager:
    """记忆管理器"""
    
    def __init__(self, store_type: str = "file", **kwargs):
        if store_type == "memory":
            self.store = InMemoryStore()
        elif store_type == "file":
            self.store = FileMemoryStore(**kwargs)
        elif store_type == "vector":
            self.store = VectorMemoryStore(**kwargs)
        else:
            raise ValueError(f"Unknown store type: {store_type}")
        
        self.summary_service = get_summary_service()
    
    async def store_conversation(
        self, 
        conversation_buffer: ConversationBuffer,
        session_id: str,
        importance: float = 0.5
    ) -> bool:
        """存储对话记忆"""
        try:
            # 生成对话摘要
            summary = await self.summary_service.summarize_conversation(conversation_buffer)
            
            # 创建记忆条目
            memory = MemoryEntry(
                id=f"conversation_{session_id}_{int(time.time())}",
                content=summary,
                metadata={
                    "session_id": session_id,
                    "message_count": conversation_buffer.get_message_count(),
                    "type": "conversation_summary"
                },
                timestamp=time.time(),
                memory_type="conversation",
                importance=importance
            )
            
            return await self.store.store_memory(memory)
            
        except Exception as e:
            logger.error(f"Error storing conversation memory: {e}")
            return False
    
    async def store_fact(
        self, 
        content: str,
        metadata: Dict[str, Any] = None,
        importance: float = 0.7
    ) -> bool:
        """存储事实记忆"""
        try:
            memory = MemoryEntry(
                id=f"fact_{int(time.time())}_{hash(content) % 10000}",
                content=content,
                metadata=metadata or {},
                timestamp=time.time(),
                memory_type="fact",
                importance=importance
            )
            
            return await self.store.store_memory(memory)
            
        except Exception as e:
            logger.error(f"Error storing fact memory: {e}")
            return False
    
    async def store_preference(
        self, 
        content: str,
        metadata: Dict[str, Any] = None,
        importance: float = 0.8
    ) -> bool:
        """存储偏好记忆"""
        try:
            memory = MemoryEntry(
                id=f"preference_{int(time.time())}_{hash(content) % 10000}",
                content=content,
                metadata=metadata or {},
                timestamp=time.time(),
                memory_type="preference",
                importance=importance
            )
            
            return await self.store.store_memory(memory)
            
        except Exception as e:
            logger.error(f"Error storing preference memory: {e}")
            return False
    
    async def recall_memories(
        self, 
        query: str,
        memory_types: List[str] = None,
        limit: int = 5
    ) -> List[MemoryEntry]:
        """回忆相关记忆"""
        if memory_types is None:
            memory_types = ["fact", "preference", "conversation"]
        
        all_memories = []
        
        for memory_type in memory_types:
            memories = await self.store.retrieve_memories(
                query=query,
                memory_type=memory_type,
                limit=limit
            )
            all_memories.extend(memories)
        
        # 按重要性和相关性排序
        all_memories.sort(key=lambda m: m.importance, reverse=True)
        
        return all_memories[:limit]
    
    async def get_context_memories(self, session_id: str) -> List[MemoryEntry]:
        """获取会话相关的上下文记忆"""
        return await self.store.retrieve_memories(
            query=session_id,
            memory_type="conversation",
            limit=3
        )

# 全局记忆管理器实例
_memory_manager = None

def get_memory_manager(store_type: str = "file", **kwargs) -> MemoryManager:
    """获取全局记忆管理器实例"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager(store_type, **kwargs)
    return _memory_manager

# 便捷函数
async def store_conversation_memory(
    conversation_buffer: ConversationBuffer,
    session_id: str,
    importance: float = 0.5
) -> bool:
    """便捷的对话记忆存储函数"""
    manager = get_memory_manager()
    return await manager.store_conversation(conversation_buffer, session_id, importance)

async def recall_relevant_memories(query: str, limit: int = 5) -> List[MemoryEntry]:
    """便捷的记忆回忆函数"""
    manager = get_memory_manager()
    return await manager.recall_memories(query, limit=limit)
