"""
Base LLM abstraction for all large language model providers.
Provides a unified interface for different LLM services.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator
import os
import asyncio
import time
from functools import wraps


# Error handling base classes
class LLMError(Exception):
    """Base exception for all LLM-related errors."""
    pass


class ConfigurationError(LLMError):
    """Exception raised for configuration-related errors."""
    pass


class APIError(LLMError):
    """Exception raised for API call failures."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class BaseLLM(ABC):
    """
    Abstract base class for all LLM providers.
    Defines the common interface that all LLM implementations must follow.
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the LLM provider.

        Args:
            api_key: API key for authentication. If None, will try to get from environment.
            **kwargs: Additional configuration parameters specific to each provider.
        """
        self.api_key = api_key or os.getenv(self.get_api_key_env_name())
        self.config = kwargs
        self.validate_config()
        self._setup_client()

    @abstractmethod
    def get_api_key_env_name(self) -> str:
        """
        Get the environment variable name for the API key.

        Returns:
            Environment variable name (e.g., 'OPENAI_API_KEY', 'DEEPSEEK_API_KEY')
        """
        pass

    @abstractmethod
    def _setup_client(self) -> None:
        """
        Setup the client for the specific LLM provider.
        This method should initialize any required clients or connections.
        """
        pass

    def validate_config(self) -> None:
        """
        Validate the configuration parameters.
        Can be overridden by subclasses for provider-specific validation.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.api_key:
            raise ConfigurationError("API key is required")
    
    def _retry_with_backoff(self, max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0):
        """
        Decorator for retrying operations with exponential backoff.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry
            backoff_factor: Multiplier for delay between retries
            
        Returns:
            Decorated function with retry logic
        """
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                delay = initial_delay
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except APIError as e:
                        last_exception = e
                        if attempt < max_retries:
                            # Retry on 5xx errors or rate limiting
                            if e.status_code and (e.status_code >= 500 or e.status_code == 429):
                                await asyncio.sleep(delay)
                                delay *= backoff_factor
                                continue
                        raise
                    except Exception as e:
                        last_exception = e
                        if attempt < max_retries:
                            await asyncio.sleep(delay)
                            delay *= backoff_factor
                            continue
                        raise
                
                if last_exception:
                    raise last_exception
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                delay = initial_delay
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except APIError as e:
                        last_exception = e
                        if attempt < max_retries:
                            if e.status_code and (e.status_code >= 500 or e.status_code == 429):
                                time.sleep(delay)
                                delay *= backoff_factor
                                continue
                        raise
                    except Exception as e:
                        last_exception = e
                        if attempt < max_retries:
                            time.sleep(delay)
                            delay *= backoff_factor
                            continue
                        raise
                
                if last_exception:
                    raise last_exception
            
            # Return appropriate wrapper based on whether function is async
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion.

        Args:
            messages: List of messages in the conversation
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters specific to the provider

        Returns:
            Dictionary containing the response
        """
        pass

    @abstractmethod
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Create a streaming chat completion.

        Args:
            messages: List of messages in the conversation
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional parameters specific to the provider

        Yields:
            Chunks of the response text
        """
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: Input prompt text
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional parameters specific to the provider

        Returns:
            Generated text string
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models for this provider.

        Returns:
            List of model names/identifiers
        """
        pass

    @abstractmethod
    def validate_model(self, model: str) -> bool:
        """
        Validate if the model is supported by this provider.

        Args:
            model: Model name to validate

        Returns:
            True if model is supported, False otherwise
        """
        pass

    def get_provider_name(self) -> str:
        """
        Get the name of the LLM provider.

        Returns:
            Provider name (e.g., 'openai', 'deepseek', 'zhipu', 'ollama')
        """
        return self.__class__.__name__.lower().replace('llm', '')

    async def __call__(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make the LLM callable directly.

        Args:
            messages: List of messages in the conversation
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters specific to the provider

        Returns:
            Dictionary containing the response
        """
        if not self.validate_model(model):
            raise ValueError(f"Model '{model}' is not supported by {self.get_provider_name()}")

        if stream:
            return await self.chat_completion_stream(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        else:
            return await self.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )