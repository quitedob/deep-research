# -*- coding: utf-8 -*-
"""
Agent 基础类 - 参考 AgentScope 的 AgentBase
"""
import asyncio
import logging
import shortuuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import OrderedDict

from ..message import Msg
from ..memory.conversation_buffer import ConversationBuffer

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Agent 配置类"""
    name: str
    role: str
    system_prompt: str
    model_name: str = "kimi"
    max_tokens: int = 4000
    temperature: float = 0.7
    capabilities: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    memory_type: str = "conversation"
    max_memory_size: int = 100


class AgentBase(ABC):
    """Agent 基础类 - 参考 AgentScope 设计"""
    
    supported_hook_types: list[str] = [
        "pre_reply",
        "post_reply",
        "pre_observe",
        "post_observe",
    ]
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.id = shortuuid.uuid()
        self.name = config.name
        self.role = config.role
        
        # 初始化记忆系统
        self.memory = ConversationBuffer(max_messages=config.max_memory_size)
        
        # Hook 系统
        self._instance_pre_reply_hooks: Dict[str, Callable] = OrderedDict()
        self._instance_post_reply_hooks: Dict[str, Callable] = OrderedDict()
        self._instance_pre_observe_hooks: Dict[str, Callable] = OrderedDict()
        self._instance_post_observe_hooks: Dict[str, Callable] = OrderedDict()
        
        # 状态管理
        self._is_active = True
        self._last_activity = datetime.now()
        self._disable_console_output = False
        
        logger.info(f"Agent {self.name} ({self.id}) initialized")
    
    @abstractmethod
    async def reply(self, msg: Msg, **kwargs) -> Msg:
        """生成回复"""
        pass
    
    async def observe(self, msg: Msg | list[Msg] | None) -> None:
        """观察消息"""
        # 执行 pre-observe hooks
        for hook in self._instance_pre_observe_hooks.values():
            try:
                await hook(self, msg)
            except Exception as e:
                logger.error(f"Pre-observe hook error: {e}")
        
        # 添加到记忆
        if isinstance(msg, list):
            for m in msg:
                await self.memory.add_message(m.role, m.content)
        elif msg:
            await self.memory.add_message(msg.role, msg.content)
        
        self._last_activity = datetime.now()
        
        # 执行 post-observe hooks
        for hook in self._instance_post_observe_hooks.values():
            try:
                await hook(self, msg)
            except Exception as e:
                logger.error(f"Post-observe hook error: {e}")
    
    async def __call__(self, msg: Msg, **kwargs) -> Msg:
        """调用 Agent"""
        # 执行 pre-reply hooks
        for hook in self._instance_pre_reply_hooks.values():
            try:
                msg = await hook(self, msg) or msg
            except Exception as e:
                logger.error(f"Pre-reply hook error: {e}")
        
        # 观察输入消息
        await self.observe(msg)
        
        # 生成回复
        reply_msg = await self.reply(msg, **kwargs)
        
        # 执行 post-reply hooks
        for hook in self._instance_post_reply_hooks.values():
            try:
                reply_msg = await hook(self, reply_msg) or reply_msg
            except Exception as e:
                logger.error(f"Post-reply hook error: {e}")
        
        # 观察回复消息
        await self.observe(reply_msg)
        
        return reply_msg
    
    def register_hook(self, hook_type: str, name: str, hook: Callable):
        """注册 Hook"""
        if hook_type not in self.supported_hook_types:
            raise ValueError(f"Invalid hook type: {hook_type}")
        
        hook_dict = getattr(self, f"_instance_{hook_type}_hooks")
        hook_dict[name] = hook
        logger.info(f"Registered {hook_type} hook: {name}")
    
    def remove_hook(self, hook_type: str, name: str):
        """移除 Hook"""
        hook_dict = getattr(self, f"_instance_{hook_type}_hooks")
        if name in hook_dict:
            del hook_dict[name]
            logger.info(f"Removed {hook_type} hook: {name}")
    
    def get_memory_summary(self) -> str:
        """获取记忆摘要"""
        return self.memory.get_conversation_text()
    
    def clear_memory(self):
        """清空记忆"""
        self.memory.clear()
        logger.info(f"Cleared memory for agent {self.name}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取 Agent 状态"""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "is_active": self._is_active,
            "last_activity": self._last_activity.isoformat(),
            "memory_size": self.memory.get_message_count(),
            "capabilities": self.config.capabilities,
            "tools": self.config.tools
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "config": {
                "name": self.config.name,
                "role": self.config.role,
                "system_prompt": self.config.system_prompt,
                "model_name": self.config.model_name,
                "capabilities": self.config.capabilities,
                "tools": self.config.tools
            },
            "status": self.get_status()
        }
    
    def set_console_output_enabled(self, enabled: bool) -> None:
        """启用或禁用控制台输出"""
        self._disable_console_output = not enabled
