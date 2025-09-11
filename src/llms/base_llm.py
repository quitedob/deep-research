# -*- coding: utf-8 -*-
"""
基础LLM提供者抽象类
定义所有LLM提供者的统一接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass
from enum import Enum
import time
import logging
import asyncio

logger = logging.getLogger(__name__)

class LLMRole(Enum):
    """LLM消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"

@dataclass
class LLMMessage:
    """LLM消息数据类"""
    role: str
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "role": self.role,
            "content": self.content
        }
        if self.name:
            result["name"] = self.name
        if self.function_call:
            result["function_call"] = self.function_call
        return result

@dataclass
class LLMResponse:
    """LLM响应数据类"""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "finish_reason": self.finish_reason
        }

class BaseLLMProvider(ABC):
    """基础LLM提供者抽象类"""
    
    def __init__(self, model_name: str, api_key: str = None, base_url: str = None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs
        self.is_initialized = False
        
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化提供者"""
        pass
    
    @abstractmethod
    async def generate(
        self, 
        messages: List[LLMMessage], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """生成文本"""
        pass
    
    @abstractmethod
    async def stream(
        self, 
        messages: List[LLMMessage], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """流式生成文本"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        pass
    
    async def cleanup(self) -> None:
        """清理资源（默认实现）"""
        logger.info(f"{self.__class__.__name__} cleaned up")
    
    def supports_function_calling(self) -> bool:
        """是否支持函数调用（默认不支持）"""
        return False
    
    def supports_vision(self) -> bool:
        """是否支持视觉输入（默认不支持）"""
        return False
    
    def get_context_length(self) -> int:
        """获取上下文长度限制（默认4K）"""
        return 4096

class MockLLMProvider(BaseLLMProvider):
    """模拟LLM提供者，用于测试"""
    
    async def initialize(self) -> bool:
        """初始化模拟提供者"""
        self.is_initialized = True
        logger.info("MockLLMProvider initialized")
        return True
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """生成模拟响应"""
        # 简单的模拟响应逻辑
        last_message = messages[-1] if messages else LLMMessage(role="user", content="")
        mock_content = f"Mock response to: {last_message.content[:50]}..."
        
        return LLMResponse(
            content=mock_content,
            model=self.model_name,
            usage={"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50},
            finish_reason="stop"
        )
    
    async def stream(
        self, 
        messages: List[LLMMessage], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """流式生成模拟响应"""
        mock_words = ["Mock", " streaming", " response", " for", " testing", "."]
        for word in mock_words:
            yield word
            await asyncio.sleep(0.1)  # 模拟延迟
    
    async def health_check(self) -> Dict[str, Any]:
        """模拟健康检查"""
        return {
            "status": "healthy",
            "model": self.model_name,
            "provider": "mock",
            "latency_ms": 10
        }
