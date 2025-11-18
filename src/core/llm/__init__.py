"""
LLM abstraction layer package.
Provides unified interface for multiple LLM providers.
"""

from src.core.llm.base_llm import (
    BaseLLM,
    LLMError,
    ConfigurationError,
    APIError,
)
from src.core.llm.factory import LLMFactory
from src.core.llm.ollama_llm import OllamaLLM
from src.core.llm.deepseek_llm import DeepSeekLLM
from src.core.llm.zhipu_llm import ZhipuLLM
from src.core.llm.utils import (
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
