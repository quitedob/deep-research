# -*- coding: utf-8 -*-
"""
对话缓冲区
管理对话历史和上下文记忆
"""

import time
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)

class MessageRole(Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"

@dataclass
class ChatMessage:
    """聊天消息数据类"""
    role: str
    content: str
    timestamp: float = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """从字典创建实例"""
        return cls(**data)

class ConversationBuffer:
    """基础对话缓冲区"""
    
    def __init__(self, max_messages: int = 100):
        self.max_messages = max_messages
        self.messages: List[ChatMessage] = []
        
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """添加消息"""
        message = ChatMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        
        # 保持消息数量在限制内
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def add_user_message(self, content: str, metadata: Dict[str, Any] = None) -> None:
        """添加用户消息"""
        self.add_message(MessageRole.USER.value, content, metadata)
    
    def add_assistant_message(self, content: str, metadata: Dict[str, Any] = None) -> None:
        """添加助手消息"""
        self.add_message(MessageRole.ASSISTANT.value, content, metadata)
    
    def add_system_message(self, content: str, metadata: Dict[str, Any] = None) -> None:
        """添加系统消息"""
        self.add_message(MessageRole.SYSTEM.value, content, metadata)
    
    def get_messages(self, limit: Optional[int] = None) -> List[ChatMessage]:
        """获取消息列表"""
        if limit is None:
            return self.messages.copy()
        return self.messages[-limit:] if limit > 0 else []
    
    def get_messages_as_dicts(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取消息字典列表"""
        messages = self.get_messages(limit)
        return [msg.to_dict() for msg in messages]
    
    def get_conversation_text(self, limit: Optional[int] = None) -> str:
        """获取对话文本"""
        messages = self.get_messages(limit)
        text_parts = []
        
        for msg in messages:
            role_text = msg.role.title()
            text_parts.append(f"{role_text}: {msg.content}")
        
        return "\n".join(text_parts)
    
    def clear(self) -> None:
        """清空对话"""
        self.messages.clear()
    
    def get_message_count(self) -> int:
        """获取消息数量"""
        return len(self.messages)
    
    def get_last_message(self) -> Optional[ChatMessage]:
        """获取最后一条消息"""
        return self.messages[-1] if self.messages else None
    
    def get_last_user_message(self) -> Optional[ChatMessage]:
        """获取最后一条用户消息"""
        for msg in reversed(self.messages):
            if msg.role == MessageRole.USER.value:
                return msg
        return None
    
    def get_last_assistant_message(self) -> Optional[ChatMessage]:
        """获取最后一条助手消息"""
        for msg in reversed(self.messages):
            if msg.role == MessageRole.ASSISTANT.value:
                return msg
        return None

class SummaryConversationBuffer(ConversationBuffer):
    """带摘要的对话缓冲区"""
    
    def __init__(self, max_messages: int = 50, summary_threshold: int = 20):
        super().__init__(max_messages)
        self.summary_threshold = summary_threshold
        self.conversation_summary = ""
        self.summarized_message_count = 0
        
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """添加消息，自动摘要"""
        super().add_message(role, content, metadata)
        
        # 检查是否需要摘要
        if (len(self.messages) - self.summarized_message_count) >= self.summary_threshold:
            self._create_summary()
    
    def _create_summary(self) -> None:
        """创建对话摘要"""
        try:
            # 获取需要摘要的消息
            messages_to_summarize = self.messages[self.summarized_message_count:-10]  # 保留最后10条
            
            if not messages_to_summarize:
                return
            
            # 简单的摘要逻辑（实际应用中可能需要调用LLM）
            conversation_text = ""
            for msg in messages_to_summarize:
                conversation_text += f"{msg.role}: {msg.content}\n"
            
            # 这里可以调用LLM进行摘要，暂时使用简单逻辑
            new_summary = f"对话摘要（{len(messages_to_summarize)}条消息）：讨论了多个话题。"
            
            if self.conversation_summary:
                self.conversation_summary += f"\n{new_summary}"
            else:
                self.conversation_summary = new_summary
            
            self.summarized_message_count = len(self.messages) - 10
            
            logger.info(f"Created conversation summary for {len(messages_to_summarize)} messages")
            
        except Exception as e:
            logger.error(f"Error creating conversation summary: {e}")
    
    def get_context(self, include_summary: bool = True) -> str:
        """获取上下文（摘要+最近消息）"""
        context_parts = []
        
        if include_summary and self.conversation_summary:
            context_parts.append(f"以前的对话摘要：\n{self.conversation_summary}")
        
        recent_messages = self.get_conversation_text(10)  # 最近10条消息
        if recent_messages:
            context_parts.append(f"最近的对话：\n{recent_messages}")
        
        return "\n\n".join(context_parts)
    
    def get_summary(self) -> str:
        """获取对话摘要"""
        return self.conversation_summary

class TokenLimitConversationBuffer(ConversationBuffer):
    """基于Token限制的对话缓冲区"""
    
    def __init__(self, max_tokens: int = 4000):
        super().__init__(max_messages=1000)  # 设置较大的消息限制
        self.max_tokens = max_tokens
        
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """添加消息，保持Token限制"""
        super().add_message(role, content, metadata)
        self._trim_to_token_limit()
    
    def _estimate_tokens(self, text: str) -> int:
        """估算token数量（简单实现）"""
        # 简单估算：1个token约等于0.7个英文字符
        return len(text) // 4
    
    def _get_total_tokens(self) -> int:
        """获取总token数"""
        total = 0
        for msg in self.messages:
            total += self._estimate_tokens(msg.content)
        return total
    
    def _trim_to_token_limit(self) -> None:
        """修剪消息以保持token限制"""
        while len(self.messages) > 1 and self._get_total_tokens() > self.max_tokens:
            # 移除最早的非系统消息
            for i, msg in enumerate(self.messages):
                if msg.role != MessageRole.SYSTEM.value:
                    self.messages.pop(i)
                    break
            else:
                # 如果只有系统消息，移除最早的
                self.messages.pop(0)

class PersistentConversationBuffer(ConversationBuffer):
    """持久化对话缓冲区"""
    
    def __init__(self, max_messages: int = 100, storage_path: str = None):
        super().__init__(max_messages)
        self.storage_path = storage_path
        
        if self.storage_path:
            self._load_messages()
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """添加消息并持久化"""
        super().add_message(role, content, metadata)
        
        if self.storage_path:
            self._save_messages()
    
    def _save_messages(self) -> None:
        """保存消息到文件"""
        try:
            if not self.storage_path:
                return
            
            data = {
                "messages": [msg.to_dict() for msg in self.messages],
                "timestamp": time.time()
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving messages: {e}")
    
    def _load_messages(self) -> None:
        """从文件加载消息"""
        try:
            if not self.storage_path:
                return
            
            import os
            if not os.path.exists(self.storage_path):
                return
            
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            messages_data = data.get("messages", [])
            self.messages = [ChatMessage.from_dict(msg_data) for msg_data in messages_data]
            
            logger.info(f"Loaded {len(self.messages)} messages from {self.storage_path}")
            
        except Exception as e:
            logger.error(f"Error loading messages: {e}")
            self.messages = []

class ConversationBufferManager:
    """对话缓冲区管理器"""
    
    def __init__(self):
        self.buffers: Dict[str, ConversationBuffer] = {}
        self.default_buffer_type = "basic"
        
    def create_buffer(
        self,
        session_id: str,
        buffer_type: str = "basic",
        **kwargs
    ) -> ConversationBuffer:
        """创建对话缓冲区"""
        if buffer_type == "basic":
            buffer = ConversationBuffer(**kwargs)
        elif buffer_type == "summary":
            buffer = SummaryConversationBuffer(**kwargs)
        elif buffer_type == "token_limit":
            buffer = TokenLimitConversationBuffer(**kwargs)
        elif buffer_type == "persistent":
            buffer = PersistentConversationBuffer(**kwargs)
        else:
            raise ValueError(f"Unknown buffer type: {buffer_type}")
        
        self.buffers[session_id] = buffer
        return buffer
    
    def get_buffer(self, session_id: str) -> Optional[ConversationBuffer]:
        """获取对话缓冲区"""
        return self.buffers.get(session_id)
    
    def get_or_create_buffer(
        self,
        session_id: str,
        buffer_type: str = None,
        **kwargs
    ) -> ConversationBuffer:
        """获取或创建对话缓冲区"""
        buffer = self.get_buffer(session_id)
        if buffer is None:
            buffer_type = buffer_type or self.default_buffer_type
            buffer = self.create_buffer(session_id, buffer_type, **kwargs)
        return buffer
    
    def delete_buffer(self, session_id: str) -> bool:
        """删除对话缓冲区"""
        if session_id in self.buffers:
            del self.buffers[session_id]
            return True
        return False
    
    def list_sessions(self) -> List[str]:
        """列出所有会话"""
        return list(self.buffers.keys())
    
    def clear_all_buffers(self) -> None:
        """清空所有缓冲区"""
        for buffer in self.buffers.values():
            buffer.clear()

# 全局缓冲区管理器实例
_buffer_manager = None

def get_conversation_buffer_manager() -> ConversationBufferManager:
    """获取全局缓冲区管理器实例"""
    global _buffer_manager
    if _buffer_manager is None:
        _buffer_manager = ConversationBufferManager()
    return _buffer_manager

# 便捷函数
def get_conversation_buffer(session_id: str, buffer_type: str = "basic", **kwargs) -> ConversationBuffer:
    """便捷的获取对话缓冲区函数"""
    manager = get_conversation_buffer_manager()
    return manager.get_or_create_buffer(session_id, buffer_type, **kwargs)
