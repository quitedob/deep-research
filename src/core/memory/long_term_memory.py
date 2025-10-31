# -*- coding: utf-8 -*-
"""
AgentScope v1.0 长期记忆系统
支持 Mem0LongTermMemory 和 ReMePersonalLongTermMemory
"""

import logging
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from abc import ABC, abstractmethod

from agentscope.memory import MemoryBase

if TYPE_CHECKING:
    from agentscope.agents import AgentBase

logger = logging.getLogger(__name__)


class LongTermMemoryBase(MemoryBase, ABC):
    """AgentScope v1.0 长期记忆基类"""

    def __init__(
        self,
        memory_type: str = "agent_control",
        enable_static_memory: bool = False,
        **kwargs
    ):
        """
        初始化长期记忆

        Args:
            memory_type: 记忆类型 ("agent_control" 或 "static_control")
            enable_static_memory: 是否启用静态记忆模式
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self.memory_type = memory_type
        self.enable_static_memory = enable_static_memory

    @abstractmethod
    def store_memory(self, agent: "AgentBase", content: str, metadata: Dict[str, Any] = None) -> None:
        """存储记忆"""
        pass

    @abstractmethod
    def retrieve_memory(self, agent: "AgentBase", query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """检索记忆"""
        pass

    @abstractmethod
    def update_memory(self, memory_id: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """更新记忆"""
        pass

    @abstractmethod
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        pass


class Mem0LongTermMemory(LongTermMemoryBase):
    """基于 Mem0 的长期记忆实现"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        memory_type: str = "agent_control",
        enable_static_memory: bool = False,
        **kwargs
    ):
        super().__init__(memory_type=memory_type, enable_static_memory=enable_static_memory, **kwargs)

        try:
            from mem0 import Memory

            self.client = Memory(api_key=api_key)
            logger.info("Mem0LongTermMemory initialized successfully")

        except ImportError:
            logger.error("Mem0 not installed. Please install with: pip install mem0ai")
            raise ImportError("Mem0 is required for Mem0LongTermMemory")

    def store_memory(self, agent: "AgentBase", content: str, metadata: Dict[str, Any] = None) -> None:
        """存储记忆到 Mem0"""
        try:
            user_id = getattr(agent, 'name', 'default_agent')
            metadata = metadata or {}

            # 添加代理相关信息到元数据
            metadata.update({
                "agent_name": agent.name,
                "agent_role": getattr(agent, 'role', ''),
                "memory_type": self.memory_type,
                "timestamp": self._get_timestamp()
            })

            result = self.client.add(content, user_id=user_id, metadata=metadata)
            logger.info(f"Stored memory for agent {agent.name}: {result}")

        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            raise

    def retrieve_memory(self, agent: "AgentBase", query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """从 Mem0 检索记忆"""
        try:
            user_id = getattr(agent, 'name', 'default_agent')

            results = self.client.search(query, user_id=user_id, limit=top_k)

            # 格式化结果
            memories = []
            for result in results:
                memory = {
                    "id": result.get("id", ""),
                    "content": result.get("memory", ""),
                    "metadata": result.get("metadata", {}),
                    "score": result.get("score", 0.0),
                    "timestamp": result.get("created_at", "")
                }
                memories.append(memory)

            logger.info(f"Retrieved {len(memories)} memories for agent {agent.name}")
            return memories

        except Exception as e:
            logger.error(f"Error retrieving memory: {e}")
            return []

    def update_memory(self, memory_id: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """更新 Mem0 中的记忆"""
        try:
            # Mem0 的更新操作
            result = self.client.update(memory_id=memory_id, data={"content": content, **(metadata or {})})
            logger.info(f"Updated memory {memory_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {e}")
            return False

    def delete_memory(self, memory_id: str) -> bool:
        """删除 Mem0 中的记忆"""
        try:
            self.client.delete(memory_id=memory_id)
            logger.info(f"Deleted memory {memory_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            return False

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


class ReMePersonalLongTermMemory(LongTermMemoryBase):
    """基于 ReMe 的个人长期记忆实现"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        memory_type: str = "agent_control",
        enable_static_memory: bool = False,
        **kwargs
    ):
        super().__init__(memory_type=memory_type, enable_static_memory=enable_static_memory, **kwargs)

        try:
            # 假设 ReMe 有类似的 API
            # from reme import PersonalMemory
            # self.client = PersonalMemory(api_key=api_key)
            logger.warning("ReMe integration not implemented yet. Using placeholder.")
            self.client = None

        except ImportError:
            logger.error("ReMe not installed. Please install ReMe SDK")
            raise ImportError("ReMe is required for ReMePersonalLongTermMemory")

    def store_memory(self, agent: "AgentBase", content: str, metadata: Dict[str, Any] = None) -> None:
        """存储记忆到 ReMe"""
        if self.client is None:
            logger.warning("ReMe client not available, skipping memory storage")
            return

        try:
            # ReMe 特定的存储逻辑
            # result = self.client.store(content, metadata=metadata)
            logger.info(f"ReMe memory storage placeholder for agent {agent.name}")

        except Exception as e:
            logger.error(f"Error storing ReMe memory: {e}")
            raise

    def retrieve_memory(self, agent: "AgentBase", query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """从 ReMe 检索记忆"""
        if self.client is None:
            logger.warning("ReMe client not available, returning empty results")
            return []

        try:
            # ReMe 特定的检索逻辑
            # results = self.client.retrieve(query, top_k=top_k)
            logger.info(f"ReMe memory retrieval placeholder for agent {agent.name}")
            return []

        except Exception as e:
            logger.error(f"Error retrieving ReMe memory: {e}")
            return []

    def update_memory(self, memory_id: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """更新 ReMe 中的记忆"""
        if self.client is None:
            return False

        try:
            # ReMe 特定的更新逻辑
            logger.info(f"ReMe memory update placeholder for {memory_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating ReMe memory {memory_id}: {e}")
            return False

    def delete_memory(self, memory_id: str) -> bool:
        """删除 ReMe 中的记忆"""
        if self.client is None:
            return False

        try:
            # ReMe 特定的删除逻辑
            logger.info(f"ReMe memory deletion placeholder for {memory_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting ReMe memory {memory_id}: {e}")
            return False


class AgentControlledLongTermMemory(Mem0LongTermMemory):
    """智能体控制的长期记忆模式"""

    def __init__(self, **kwargs):
        super().__init__(memory_type="agent_control", **kwargs)

    def store_memory(self, agent: "AgentBase", content: str, metadata: Dict[str, Any] = None) -> None:
        """智能体决定是否存储记忆"""
        # 在 agent_control 模式下，智能体可以自主决定存储什么
        # 这里可以添加智能判断逻辑
        should_store = self._should_store_memory(agent, content, metadata)

        if should_store:
            super().store_memory(agent, content, metadata)
            logger.info(f"Agent {agent.name} chose to store memory")
        else:
            logger.debug(f"Agent {agent.name} chose not to store memory")

    def _should_store_memory(self, agent: "AgentBase", content: str, metadata: Dict[str, Any] = None) -> bool:
        """判断是否应该存储记忆"""
        # 简单的判断逻辑，可以根据内容重要性、重复性等因素
        content_length = len(content.strip())

        # 跳过太短的内容
        if content_length < 10:
            return False

        # 跳过纯指令性内容
        instruction_keywords = ["请", "帮我", "我想", "需要", "希望"]
        if any(keyword in content for keyword in instruction_keywords):
            return False

        # 可以在这里添加更复杂的判断逻辑
        return True


class StaticLongTermMemory(Mem0LongTermMemory):
    """静态控制的长期记忆模式"""

    def __init__(self, **kwargs):
        super().__init__(memory_type="static_control", enable_static_memory=True, **kwargs)

    def store_memory(self, agent: "AgentBase", content: str, metadata: Dict[str, Any] = None) -> None:
        """静态规则控制的记忆存储"""
        # 在 static_control 模式下，使用预定义规则存储记忆
        # 所有重要的交互都会被存储
        super().store_memory(agent, content, metadata)


class LongTermMemoryManager:
    """长期记忆管理器"""

    def __init__(self):
        self.memories: Dict[str, LongTermMemoryBase] = {}

    def create_memory(
        self,
        memory_id: str,
        memory_type: str = "mem0_agent_control",
        **kwargs
    ) -> LongTermMemoryBase:
        """创建长期记忆实例"""

        if memory_type == "mem0_agent_control":
            memory = AgentControlledLongTermMemory(**kwargs)
        elif memory_type == "mem0_static":
            memory = StaticLongTermMemory(**kwargs)
        elif memory_type == "reme_personal":
            memory = ReMePersonalLongTermMemory(**kwargs)
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")

        self.memories[memory_id] = memory
        logger.info(f"Created long-term memory {memory_id} of type {memory_type}")
        return memory

    def get_memory(self, memory_id: str) -> Optional[LongTermMemoryBase]:
        """获取长期记忆实例"""
        return self.memories.get(memory_id)

    def delete_memory(self, memory_id: str) -> bool:
        """删除长期记忆实例"""
        if memory_id in self.memories:
            del self.memories[memory_id]
            logger.info(f"Deleted long-term memory {memory_id}")
            return True
        return False

    def list_memories(self) -> List[str]:
        """列出所有记忆实例"""
        return list(self.memories.keys())


# 全局记忆管理器实例
_memory_manager = None

def get_long_term_memory_manager() -> LongTermMemoryManager:
    """获取全局长期记忆管理器实例"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = LongTermMemoryManager()
    return _memory_manager

def create_long_term_memory(
    memory_id: str,
    memory_type: str = "mem0_agent_control",
    **kwargs
) -> LongTermMemoryBase:
    """创建长期记忆的便捷函数"""
    manager = get_long_term_memory_manager()
    return manager.create_memory(memory_id, memory_type, **kwargs)

def get_long_term_memory(memory_id: str) -> Optional[LongTermMemoryBase]:
    """获取长期记忆的便捷函数"""
    manager = get_long_term_memory_manager()
    return manager.get_memory(memory_id)
