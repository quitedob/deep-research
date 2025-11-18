"""
DeepSeek LLM provider implementation.
Based on the DeepSeek API documentation from deepseek-rule.txt
Compatible with OpenAI API format.
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
import json
import logging

from src.core.llm.base_llm import BaseLLM, APIError, ConfigurationError

logger = logging.getLogger(__name__)


class DeepSeekLLM(BaseLLM):
    """
    DeepSeek LLM provider.
    Uses OpenAI-compatible API with base_url: https://api.deepseek.com
    Supports deepseek-chat and deepseek-reasoner models.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.deepseek.com", **kwargs):
        """
        Initialize DeepSeek LLM provider.

        Args:
            api_key: DeepSeek API key
            base_url: DeepSeek API base URL (default: https://api.deepseek.com)
            **kwargs: Additional configuration parameters
        """
        self.base_url = base_url.rstrip('/')
        super().__init__(api_key, **kwargs)

    def get_api_key_env_name(self) -> str:
        """Get environment variable name for DeepSeek API key."""
        return "DEEPSEEK_API_KEY"
    
    def validate_config(self) -> None:
        """
        Validate DeepSeek configuration.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.api_key:
            raise ConfigurationError("DeepSeek API key is required. Set DEEPSEEK_API_KEY environment variable.")
        
        if not self.base_url:
            raise ConfigurationError("DeepSeek base_url is required")
        
        if not self.base_url.startswith("https://"):
            raise ConfigurationError(f"Invalid DeepSeek base_url: {self.base_url}. Must start with https://")

    def _setup_client(self) -> None:
        """Setup aiohttp client for DeepSeek API."""
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to DeepSeek API.
        
        Args:
            endpoint: API endpoint (e.g., 'chat/completions')
            data: Request payload
            
        Returns:
            Response JSON
            
        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}/v1/{endpoint}"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.post(url, json=data) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        raise APIError(
                            f"DeepSeek API error: {response_text}",
                            status_code=response.status,
                            response=response_text
                        )

                    return json.loads(response_text)
        except aiohttp.ClientError as e:
            raise APIError(f"DeepSeek connection error: {str(e)}", status_code=None, response=None)
        except asyncio.TimeoutError:
            raise APIError("DeepSeek request timeout", status_code=408, response=None)

    async def _stream_request(self, endpoint: str, data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a request to DeepSeek API.
        
        Args:
            endpoint: API endpoint
            data: Request payload
            
        Yields:
            Response chunks as JSON objects
            
        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}/v1/{endpoint}"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise APIError(
                            f"DeepSeek API error: {error_text}",
                            status_code=response.status,
                            response=error_text
                        )

                    async for line in response.content:
                        if line:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                try:
                                    data_str = line_str[6:]  # Remove 'data: ' prefix
                                    if data_str != '[DONE]':
                                        yield json.loads(data_str)
                                except json.JSONDecodeError:
                                    continue
        except aiohttp.ClientError as e:
            raise APIError(f"DeepSeek connection error: {str(e)}", status_code=None, response=None)
        except asyncio.TimeoutError:
            raise APIError("DeepSeek request timeout", status_code=408, response=None)

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
        Create a chat completion using DeepSeek's chat completions endpoint.
        """
        data = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature
        }

        if max_tokens is not None:
            data["max_tokens"] = max_tokens

        # Handle DeepSeek-specific parameters
        if "top_p" in kwargs:
            data["top_p"] = kwargs["top_p"]
        if "frequency_penalty" in kwargs:
            data["frequency_penalty"] = kwargs["frequency_penalty"]
        if "presence_penalty" in kwargs:
            data["presence_penalty"] = kwargs["presence_penalty"]
        if "stop" in kwargs:
            data["stop"] = kwargs["stop"]
        if "response_format" in kwargs:
            data["response_format"] = kwargs["response_format"]

        response = await self._make_request("chat/completions", data)

        # Handle reasoning content for deepseek-reasoner model
        if model == "deepseek-reasoner" and "choices" in response:
            message = response["choices"][0].get("message", {})
            reasoning_content = message.get("reasoning_content")
            content = message.get("content")

            if reasoning_content:
                # Store reasoning content for potential use
                response["reasoning_content"] = reasoning_content

        return response

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Create a streaming chat completion using DeepSeek's chat completions endpoint.
        """
        data = {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": temperature
        }

        if max_tokens is not None:
            data["max_tokens"] = max_tokens

        # Handle DeepSeek-specific parameters
        if "top_p" in kwargs:
            data["top_p"] = kwargs["top_p"]
        if "frequency_penalty" in kwargs:
            data["frequency_penalty"] = kwargs["frequency_penalty"]
        if "presence_penalty" in kwargs:
            data["presence_penalty"] = kwargs["presence_penalty"]
        if "stop" in kwargs:
            data["stop"] = kwargs["stop"]
        if "response_format" in kwargs:
            data["response_format"] = kwargs["response_format"]

        reasoning_content = ""
        content = ""

        async for chunk in self._stream_request("chat/completions", data):
            if "choices" in chunk and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0].get("delta", {})

                # Handle reasoning content for deepseek-reasoner model
                if model == "deepseek-reasoner" and "reasoning_content" in delta:
                    reasoning_content += delta["reasoning_content"]

                if "content" in delta:
                    content += delta["content"]
                    yield delta["content"]
    
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
        This is the required method from BaseLLM interface.
        
        Args:
            prompt: Input prompt text
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Generated text string
        """
        # Convert prompt to messages format
        messages = [{"role": "user", "content": prompt}]
        
        # Add system message if provided
        if "system" in kwargs:
            messages.insert(0, {"role": "system", "content": kwargs.pop("system")})
        
        response = await self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            **kwargs
        )
        
        # Extract content from response
        return response.get("choices", [{}])[0].get("message", {}).get("content", "")

    async def function_calling(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        model: str = "deepseek-chat",
        temperature: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform function calling using DeepSeek's function calling capabilities.
        Only deepseek-chat supports function calling.
        """
        if model == "deepseek-reasoner":
            logger.warning("Function calling is not supported by deepseek-reasoner. Using deepseek-chat instead.")
            model = "deepseek-chat"

        data = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "temperature": temperature,
            "stream": False
        }

        if "tool_choice" in kwargs:
            data["tool_choice"] = kwargs["tool_choice"]

        return await self._make_request("chat/completions", data)

    async def json_mode_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = "deepseek-chat",
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion with JSON output mode.
        """
        # Ensure system or user prompt mentions "json"
        system_mention = False
        for message in messages:
            if message.get("role") == "system" or message.get("role") == "user":
                if "json" in message.get("content", "").lower():
                    system_mention = True
                    break

        if not system_mention:
            logger.warning("System or user prompt should contain 'json' to guide model for JSON output")

        data = {
            "model": model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": temperature,
            "stream": False
        }

        if max_tokens is not None:
            data["max_tokens"] = max_tokens

        return await self._make_request("chat/completions", data)

    async def prefix_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = "deepseek-chat",
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform conversation prefix completion.
        Requires base_url to be set to https://api.deepseek.com/beta
        """
        if self.base_url != "https://api.deepseek.com/beta":
            logger.warning("Prefix completion requires beta endpoint. Consider updating base_url.")

        # Ensure last message has role 'assistant' and prefix=True
        if messages and messages[-1].get("role") == "assistant":
            messages[-1]["prefix"] = True

        data = {
            "model": model,
            "messages": messages,
            "stream": False
        }

        if stop:
            data["stop"] = stop

        return await self._make_request("chat/completions", data)

    def get_available_models(self) -> List[str]:
        """
        Get list of available models for DeepSeek.
        """
        return [
            "deepseek-chat",      # DeepSeek-V3.2-Exp (non-reasoning mode)
            "deepseek-reasoner"   # DeepSeek-V3.2-Exp (reasoning mode)
        ]

    def validate_model(self, model: str) -> bool:
        """
        Validate if the model is supported by DeepSeek.
        """
        available_models = self.get_available_models()
        return model in available_models

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model.
        """
        model_info = {
            "deepseek-chat": {
                "model_version": "DeepSeek-V3.2-Exp (non-reasoning mode)",
                "context_length": 128000,
                "max_output": 8000,
                "features": ["Json Output", "Function Calling", "Conversation Prefix Continuation (Beta)", "FIM Completion (Beta)"],
                "pricing": {
                    "input_tokens_cache_hit": "0.2 yuan per million tokens",
                    "input_tokens_cache_miss": "2 yuan per million tokens",
                    "output_tokens": "3 yuan per million tokens"
                }
            },
            "deepseek-reasoner": {
                "model_version": "DeepSeek-V3.2-Exp (reasoning mode)",
                "context_length": 128000,
                "max_output": 64000,
                "features": ["Json Output", "Conversation Prefix Continuation (Beta)"],
                "not_supported": ["Function Calling", "FIM Completion (Beta)"],
                "not_supported_params": ["temperature", "top_p", "presence_penalty", "frequency_penalty", "logprobs", "top_logprobs"],
                "pricing": {
                    "input_tokens_cache_hit": "0.2 yuan per million tokens",
                    "input_tokens_cache_miss": "2 yuan per million tokens",
                    "output_tokens": "3 yuan per million tokens"
                }
            }
        }

        return model_info.get(model, {})

    def get_temperature_suggestions(self) -> Dict[str, float]:
        """
        Get temperature suggestions for different use cases.
        """
        return {
            "code_generation_math": 0.0,
            "data_extraction_analysis": 1.0,
            "general_conversation": 1.3,
            "translation": 1.3,
            "creative_writing": 1.5
        }

    def get_rate_limits(self) -> Dict[str, Any]:
        """
        Get rate limit information.
        """
        return {
            "concurrent_requests": "Unlimited",
            "note": "Server may delay responses under high traffic. Requests will be kept alive for up to 30 minutes before timeout."
        }