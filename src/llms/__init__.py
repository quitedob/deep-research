# -*- coding: utf-8 -*-
"""
LLM模块
提供统一的大语言模型接口和智能路由功能
"""

# 基础类
from .base_llm import (
    BaseLLMProvider,
    LLMMessage,
    LLMResponse,
    LLMRole,
    MockLLMProvider
)

# 具体提供者
from .providers.deepseek_llm import DeepSeekProvider
from .providers.ollama_llm import OllamaProvider
from .providers.doubao_llm import DoubaoProvider
from .providers.kimi_llm import KimiProvider

# 智能路由
from .router import (
    SmartModelRouter,
    ModelRouter,
    LLMMessage as RouterLLMMessage,
    ModelCapability,
    RoutingDecision
)

# 嵌入模型
from .embeddings import (
    BaseEmbeddingProvider,
    EmbeddingResult,
    OllamaEmbeddingProvider,
    SentenceTransformersProvider,
    OpenAIEmbeddingProvider,
    MockEmbeddingProvider,
    EmbeddingService,
    get_embedding_service
)

# 兼容性函数（如果需要的话可以在这里实现）
def get_llm_by_type(llm_type: str):
    """获取指定类型的LLM（兼容性函数）"""
    # 这里可以根据需要实现具体逻辑
    pass

def get_configured_llm_models():
    """获取配置的LLM模型列表（兼容性函数）"""
    # 这里可以根据需要实现具体逻辑
    return []

__all__ = [
    # 基础类
    "BaseLLMProvider",
    "LLMMessage", 
    "LLMResponse",
    "LLMRole",
    "MockLLMProvider",
    
    # LLM提供者
    "DeepSeekProvider",
    "OllamaProvider",
    "DoubaoProvider",
    "KimiProvider",
    
    # 路由相关
    "SmartModelRouter",
    "ModelRouter",
    "RouterLLMMessage",
    "ModelCapability",
    "RoutingDecision",
    
    # 嵌入相关
    "BaseEmbeddingProvider",
    "EmbeddingResult",
    "OllamaEmbeddingProvider",
    "SentenceTransformersProvider", 
    "OpenAIEmbeddingProvider",
    "MockEmbeddingProvider",
    "EmbeddingService",
    "get_embedding_service",
    
    # 兼容性
    "get_llm_by_type",
    "get_configured_llm_models"
] 