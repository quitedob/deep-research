# -*- coding: utf-8 -*-
"""
用户 Agent - 参考 AgentScope 的 UserAgent
"""
import logging
from typing import Any

from .base_agent import AgentBase, AgentConfig
from ..message import Msg, TextBlock

logger = logging.getLogger(__name__)


class UserAgent(AgentBase):
    """用户交互 Agent"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        logger.info(f"User Agent {self.name} initialized")
    
    async def reply(self, msg: Msg | None = None, **kwargs) -> Msg:
        """接收用户输入并生成回复消息"""
        # 如果提供了消息，直接返回
        if msg:
            return msg
        
        # 否则等待用户输入
        user_input = input(f"{self.name}: ")
        
        reply_msg = Msg(
            name=self.name,
            content=user_input,
            role="user",
            metadata={}
        )
        
        return reply_msg
    
    async def observe(self, msg: Msg | list[Msg] | None) -> None:
        """观察消息"""
        await super().observe(msg)
