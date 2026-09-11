"""
Base LLM abstraction for all large language model providers.
Provides a unified interface for different LLM services.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator
import os
import asyncio
import time
import json
import weakref
import aiohttp
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

    _instances = weakref.WeakSet()

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the LLM provider.

        Args:
            api_key: API key for authentication. If None, will try to get from environment.
            **kwargs: Additional configuration parameters specific to each provider.
        """
        self.api_key = api_key or os.getenv(self.get_api_key_env_name())
        self.config = kwargs
        self.model = kwargs.get("model", kwargs.get("model_name"))
        self._session = None
        self.validate_config()
        self._setup_client()
        self._instances.add(self)

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=float(self.config.get("timeout", 60))),
                headers=getattr(self, "headers", None),
            )
        return self._session

    async def close(self):
        if self._session is not None and not self._session.closed:
            await self._session.close()

    @classmethod
    async def close_all(cls):
        await asyncio.gather(*(instance.close() for instance in list(cls._instances)))

    def _can_retry(self, error, attempt):
        return attempt < int(self.config.get("max_retries", 3)) and (
            isinstance(error, (aiohttp.ClientError, asyncio.TimeoutError))
            or isinstance(error, APIError) and (
                error.status_code in (None, 408, 429)
                or error.status_code >= 500
            )
        )

    async def _request_json(self, url, data, method="POST"):
        attempt = 0
        while True:
            try:
                session = await self._get_session()
                request = getattr(session, method.lower())
                async with request(url, **({"json": data} if data is not None else {})) as response:
                    if response.status >= 400:
                        try:
                            detail = await response.json()
                        except (ValueError, aiohttp.ClientError):
                            detail = None
                        raise APIError("Provider request failed", response.status, detail)
                    if getattr(response, "content_length", None) == 0:
                        return {}
                    return await response.json()
            except (aiohttp.ClientError, asyncio.TimeoutError, APIError) as error:
                if not self._can_retry(error, attempt):
                    raise APIError("Provider request failed", getattr(error, "status_code", None), getattr(error, "response", None)) from error
                await asyncio.sleep(float(self.config.get("retry_delay", 1)) * 2 ** attempt)
                attempt += 1

    async def _request_stream(self, url, data, *, sse=True):
        attempt = 0
        emitted = False
        finished = False
        while True:
            try:
                session = await self._get_session()
                async with session.post(url, json=data) as response:
                    if response.status >= 400:
                        raise APIError("Provider request failed", response.status)
                    async for line in response.content:
                        line = line.decode("utf-8").strip()
                        if not line:
                            continue
                        if sse:
                            if not line.startswith("data:"):
                                continue
                            line = line[5:].strip()
                            if line == "[DONE]":
                                return
                        payload = json.loads(line)
                        if "error" in payload:
                            raise APIError("Provider stream failed")
                        if any(choice.get("finish_reason") is not None for choice in payload.get("choices", [])):
                            finished = True
                        emitted = True
                        yield payload
                    if sse and not finished:
                        raise APIError("Provider stream ended before its terminal frame")
                    return
            except (aiohttp.ClientError, asyncio.TimeoutError, APIError) as error:
                # Replaying an already visible completion would duplicate text and tool calls.
                if emitted or not self._can_retry(error, attempt):
                    raise APIError("Provider stream failed", getattr(error, "status_code", None)) from error
                await asyncio.sleep(float(self.config.get("retry_delay", 1)) * 2 ** attempt)
                attempt += 1

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
