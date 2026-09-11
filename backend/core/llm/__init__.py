"""
LLM abstraction layer package.
Provides unified interface for multiple LLM providers.
"""

from backend.core.llm.base_llm import (
    BaseLLM,
    LLMError,
    ConfigurationError,
    APIError,
)
from backend.core.llm.factory import LLMFactory
from backend.core.llm.ollama_llm import OllamaLLM
from backend.core.llm.deepseek_llm import DeepSeekLLM
from backend.core.llm.zhipu_llm import ZhipuLLM
from backend.core.llm.utils import (
    LLMLogger,
    RateLimitDetector,
    RetryHandler,
    TokenCounter,
    with_retry,
    with_logging,
)

__all__ = [
    "BaseLLM",
    "LLMError",
    "ConfigurationError",
    "APIError",
    "LLMFactory",
    "OllamaLLM",
    "DeepSeekLLM",
    "ZhipuLLM",
    "LLMLogger",
    "RateLimitDetector",
    "RetryHandler",
    "TokenCounter",
    "with_retry",
    "with_logging",
]
