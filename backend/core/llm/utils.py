"""
Logging and error handling utilities for LLM operations.
Provides structured logging, API key sanitization, rate limit detection, and retry logic.
"""

import logging
import time
import re
from typing import Dict, Any, Optional, Callable, TypeVar, List
from functools import wraps
import asyncio
from datetime import datetime

# Type variable for generic function return types
T = TypeVar('T')

# Configure logger
logger = logging.getLogger(__name__)


class LLMLogger:
    """
    Structured logger for LLM API calls with API key sanitization.
    """

    @staticmethod
    def sanitize_api_key(text: str, api_key: Optional[str] = None) -> str:
        """
        Sanitize API keys from text to prevent exposure in logs.
        
        Args:
            text: Text that may contain API keys
            api_key: Specific API key to sanitize (optional)
            
        Returns:
            Text with API keys replaced by masked values
        """
        if not text:
            return text
        
        # Sanitize specific API key if provided
        if api_key and api_key in text:
            # Show first 4 and last 4 characters
            if len(api_key) > 8:
                masked = f"{api_key[:4]}...{api_key[-4:]}"
            else:
                masked = "****"
            text = text.replace(api_key, masked)
        
        # Sanitize common API key patterns
        # Pattern: Bearer <token>
        text = re.sub(
            r'Bearer\s+([A-Za-z0-9_\-]{20,})',
            lambda m: f"Bearer {m.group(1)[:4]}...{m.group(1)[-4:]}",
            text
        )
        
        # Pattern: api_key=<token> or apiKey=<token>
        text = re.sub(
            r'api[_-]?key["\']?\s*[:=]\s*["\']?([A-Za-z0-9_\-]{20,})["\']?',
            lambda m: f"api_key={m.group(1)[:4]}...{m.group(1)[-4:]}",
            text,
            flags=re.IGNORECASE
        )
        
        # Pattern: Authorization: <token>
        text = re.sub(
            r'Authorization["\']?\s*:\s*["\']?([A-Za-z0-9_\-]{20,})["\']?',
            lambda m: f"Authorization: {m.group(1)[:4]}...{m.group(1)[-4:]}",
            text,
            flags=re.IGNORECASE
        )
        
        return text

    @staticmethod
    def sanitize_dict(data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Sanitize API keys from dictionary data.
        
        Args:
            data: Dictionary that may contain API keys
            api_key: Specific API key to sanitize (optional)
            
        Returns:
            Dictionary with API keys sanitized
        """
        if not data:
            return data
        
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = LLMLogger.sanitize_api_key(value, api_key)
            elif isinstance(value, dict):
                sanitized[key] = LLMLogger.sanitize_dict(value, api_key)
            elif isinstance(value, list):
                sanitized[key] = [
                    LLMLogger.sanitize_dict(item, api_key) if isinstance(item, dict)
                    else LLMLogger.sanitize_api_key(item, api_key) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized

    @staticmethod
    def log_request(
        provider: str,
        endpoint: str,
        request_data: Dict[str, Any],
        api_key: Optional[str] = None
    ) -> None:
        """
        Log LLM API request with sanitized data.
        
        Args:
            provider: LLM provider name (e.g., 'ollama', 'deepseek', 'zhipu')
            endpoint: API endpoint being called
            request_data: Request payload
            api_key: API key to sanitize from logs
        """
        sanitized_data = LLMLogger.sanitize_dict(request_data, api_key)
        
        logger.info(
            f"LLM Request | Provider: {provider} | Endpoint: {endpoint}",
            extra={
                "provider": provider,
                "endpoint": endpoint,
                "request_data": sanitized_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    @staticmethod
    def log_response(
        provider: str,
        endpoint: str,
        response_data: Dict[str, Any],
        duration_ms: float,
        api_key: Optional[str] = None
    ) -> None:
        """
        Log LLM API response with sanitized data.
        
        Args:
            provider: LLM provider name
            endpoint: API endpoint that was called
            response_data: Response payload
            duration_ms: Request duration in milliseconds
            api_key: API key to sanitize from logs
        """
        sanitized_data = LLMLogger.sanitize_dict(response_data, api_key)
        
        # Extract usage information if available
        usage = response_data.get("usage", {})
        
        logger.info(
            f"LLM Response | Provider: {provider} | Endpoint: {endpoint} | Duration: {duration_ms:.2f}ms",
            extra={
                "provider": provider,
                "endpoint": endpoint,
                "duration_ms": duration_ms,
                "usage": usage,
                "response_data": sanitized_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    @staticmethod
    def log_error(
        provider: str,
        endpoint: str,
        error: Exception,
        request_data: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None
    ) -> None:
        """
        Log LLM API error with sanitized data.
        
        Args:
            provider: LLM provider name
            endpoint: API endpoint that failed
            error: Exception that occurred
            request_data: Request payload (optional)
            api_key: API key to sanitize from logs
        """
        error_message = LLMLogger.sanitize_api_key(str(error), api_key)
        
        extra_data = {
            "provider": provider,
            "endpoint": endpoint,
            "error_type": type(error).__name__,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if request_data:
            extra_data["request_data"] = LLMLogger.sanitize_dict(request_data, api_key)
        
        logger.error(
            f"LLM Error | Provider: {provider} | Endpoint: {endpoint} | Error: {error_message}",
            extra=extra_data,
            exc_info=True
        )


class RateLimitDetector:
    """
    Detect and handle rate limiting from LLM providers.
    """

    # Common rate limit status codes
    RATE_LIMIT_STATUS_CODES = {429, 503}
    
    # Common rate limit error messages
    RATE_LIMIT_PATTERNS = [
        r'rate\s*limit',
        r'too\s*many\s*requests',
        r'quota\s*exceeded',
        r'throttle',
        r'429',
    ]

    @staticmethod
    def is_rate_limit_error(status_code: Optional[int] = None, error_message: Optional[str] = None) -> bool:
        """
        Detect if an error is due to rate limiting.
        
        Args:
            status_code: HTTP status code
            error_message: Error message text
            
        Returns:
            True if error is rate limit related, False otherwise
        """
        # Check status code
        if status_code and status_code in RateLimitDetector.RATE_LIMIT_STATUS_CODES:
            return True
        
        # Check error message
        if error_message:
            error_lower = error_message.lower()
            for pattern in RateLimitDetector.RATE_LIMIT_PATTERNS:
                if re.search(pattern, error_lower):
                    return True
        
        return False

    @staticmethod
    def get_retry_after(response_headers: Optional[Dict[str, str]] = None) -> Optional[float]:
        """
        Extract retry-after duration from response headers.
        
        Args:
            response_headers: HTTP response headers
            
        Returns:
            Retry-after duration in seconds, or None if not specified
        """
        if not response_headers:
            return None
        
        # Check for Retry-After header (case-insensitive)
        for key, value in response_headers.items():
            if key.lower() == 'retry-after':
                try:
                    # Try to parse as integer (seconds)
                    return float(value)
                except ValueError:
                    # Could be HTTP date format, but we'll just return None
                    return None
        
        return None


class RetryHandler:
    """
    Handle retries for transient failures with exponential backoff.
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0
    ):
        """
        Initialize retry handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry
            backoff_factor: Multiplier for delay between retries
            max_delay: Maximum delay in seconds between retries
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay

    def calculate_delay(self, attempt: int, retry_after: Optional[float] = None) -> float:
        """
        Calculate delay for a retry attempt.
        
        Args:
            attempt: Current attempt number (0-indexed)
            retry_after: Suggested retry-after duration from server
            
        Returns:
            Delay in seconds
        """
        if retry_after is not None:
            return min(retry_after, self.max_delay)
        
        delay = self.initial_delay * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay)

    def should_retry(
        self,
        attempt: int,
        error: Exception,
        status_code: Optional[int] = None
    ) -> bool:
        """
        Determine if an operation should be retried.
        
        Args:
            attempt: Current attempt number (0-indexed)
            error: Exception that occurred
            status_code: HTTP status code (if applicable)
            
        Returns:
            True if should retry, False otherwise
        """
        # Don't retry if max attempts reached
        if attempt >= self.max_retries:
            return False
        
        # Always retry rate limit errors
        if RateLimitDetector.is_rate_limit_error(status_code, str(error)):
            return True
        
        # Retry on 5xx server errors
        if status_code and 500 <= status_code < 600:
            return True
        
        # Retry on timeout errors
        if isinstance(error, (asyncio.TimeoutError, TimeoutError)):
            return True
        
        # Retry on connection errors
        error_str = str(error).lower()
        transient_patterns = [
            'connection',
            'timeout',
            'temporary',
            'unavailable',
            'network',
        ]
        
        for pattern in transient_patterns:
            if pattern in error_str:
                return True
        
        return False

    async def execute_with_retry_async(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        Execute an async function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Extract status code if it's an APIError
                status_code = getattr(e, 'status_code', None)
                
                if not self.should_retry(attempt, e, status_code):
                    raise
                
                # Calculate delay
                retry_after = None
                if hasattr(e, 'response_headers'):
                    retry_after = RateLimitDetector.get_retry_after(e.response_headers)
                
                delay = self.calculate_delay(attempt, retry_after)
                
                logger.warning(
                    f"Retry attempt {attempt + 1}/{self.max_retries} after {delay:.2f}s due to: {str(e)}"
                )
                
                await asyncio.sleep(delay)
        
        if last_exception:
            raise last_exception

    def execute_with_retry_sync(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        Execute a sync function with retry logic.
        
        Args:
            func: Sync function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Extract status code if it's an APIError
                status_code = getattr(e, 'status_code', None)
                
                if not self.should_retry(attempt, e, status_code):
                    raise
                
                # Calculate delay
                retry_after = None
                if hasattr(e, 'response_headers'):
                    retry_after = RateLimitDetector.get_retry_after(e.response_headers)
                
                delay = self.calculate_delay(attempt, retry_after)
                
                logger.warning(
                    f"Retry attempt {attempt + 1}/{self.max_retries} after {delay:.2f}s due to: {str(e)}"
                )
                
                time.sleep(delay)
        
        if last_exception:
            raise last_exception


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0
):
    """
    Decorator to add retry logic to functions.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiplier for delay between retries
        max_delay: Maximum delay in seconds between retries
        
    Returns:
        Decorated function with retry logic
    """
    handler = RetryHandler(max_retries, initial_delay, backoff_factor, max_delay)
    
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await handler.execute_with_retry_async(func, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return handler.execute_with_retry_sync(func, *args, **kwargs)
            return sync_wrapper
    
    return decorator



def with_logging(provider: str, endpoint: str):
    """
    Decorator to add structured logging to LLM API calls.
    
    Args:
        provider: LLM provider name
        endpoint: API endpoint being called
        
    Returns:
        Decorated function with logging
    """
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Extract request data from kwargs
                request_data = kwargs.copy()
                api_key = request_data.pop('api_key', None)
                
                # Log request
                LLMLogger.log_request(provider, endpoint, request_data, api_key)
                
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Log response
                    if isinstance(result, dict):
                        LLMLogger.log_response(provider, endpoint, result, duration_ms, api_key)
                    
                    return result
                except Exception as e:
                    # Log error
                    LLMLogger.log_error(provider, endpoint, e, request_data, api_key)
                    raise
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Extract request data from kwargs
                request_data = kwargs.copy()
                api_key = request_data.pop('api_key', None)
                
                # Log request
                LLMLogger.log_request(provider, endpoint, request_data, api_key)
                
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Log response
                    if isinstance(result, dict):
                        LLMLogger.log_response(provider, endpoint, result, duration_ms, api_key)
                    
                    return result
                except Exception as e:
                    # Log error
                    LLMLogger.log_error(provider, endpoint, e, request_data, api_key)
                    raise
            
            return sync_wrapper
    
    return decorator


class TokenCounter:
    """
    Utility for tracking token usage across LLM calls.
    """

    def __init__(self):
        """Initialize token counter."""
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.call_count = 0

    def add_usage(self, usage: Dict[str, int]) -> None:
        """
        Add token usage from an LLM response.
        
        Args:
            usage: Usage dictionary from LLM response
        """
        self.total_prompt_tokens += usage.get('prompt_tokens', 0)
        self.total_completion_tokens += usage.get('completion_tokens', 0)
        self.total_tokens += usage.get('total_tokens', 0)
        self.call_count += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Get token usage statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        return {
            'total_prompt_tokens': self.total_prompt_tokens,
            'total_completion_tokens': self.total_completion_tokens,
            'total_tokens': self.total_tokens,
            'call_count': self.call_count,
            'avg_prompt_tokens': self.total_prompt_tokens / self.call_count if self.call_count > 0 else 0,
            'avg_completion_tokens': self.total_completion_tokens / self.call_count if self.call_count > 0 else 0,
            'avg_total_tokens': self.total_tokens / self.call_count if self.call_count > 0 else 0,
        }

    def reset(self) -> None:
        """Reset all counters."""
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.call_count = 0
