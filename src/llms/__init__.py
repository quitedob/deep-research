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
from .deepseek_provider import DeepSeekProvider
from .ollama_provider import OllamaProvider

# 智能路由
from .router import (
    LLMRouter,
    TaskType,
    ModelTier,
    RoutingRule,
    ModelCandidate,
    get_llm_router
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

# 保持原有导入的兼容性
from .llm import get_llm_by_type, get_configured_llm_models

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
    
    # 路由相关
    "LLMRouter",
    "TaskType",
    "ModelTier", 
    "RoutingRule",
    "ModelCandidate",
    "get_llm_router",
    
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