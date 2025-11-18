"""
Zhipu LLM provider implementation.
Based on the Zhipu AI documentation from z_rule.txt
Supports various GLM models including vision and reasoning capabilities.
"""

import aiohttp
import asyncio
import base64
from typing import Dict, List, Optional, Any, AsyncGenerator
import json
import logging

from src.core.llm.base_llm import BaseLLM, APIError, ConfigurationError

logger = logging.getLogger(__name__)


class ZhipuLLM(BaseLLM):
    """
    Zhipu AI LLM provider.
    Supports GLM series models including text, vision, and reasoning models.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://open.bigmodel.cn/api/paas/v4", **kwargs):
        """
        Initialize Zhipu LLM provider.

        Args:
            api_key: Zhipu AI API key (from BIGMODEL_API_KEY env var)
            base_url: Zhipu API base URL (default: https://open.bigmodel.cn/api/paas/v4)
            **kwargs: Additional configuration parameters
        """
        self.base_url = base_url.rstrip('/')
        super().__init__(api_key, **kwargs)

    def get_api_key_env_name(self) -> str:
        """Get environment variable name for Zhipu API key."""
        return "BIGMODEL_API_KEY"
    
    def validate_config(self) -> None:
        """
        Validate Zhipu configuration.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.api_key:
            raise ConfigurationError("Zhipu API key is required. Set BIGMODEL_API_KEY environment variable.")
        
        if not self.base_url:
            raise ConfigurationError("Zhipu base_url is required")
        
        if not self.base_url.startswith("https://"):
            raise ConfigurationError(f"Invalid Zhipu base_url: {self.base_url}. Must start with https://")

    def _setup_client(self) -> None:
        """Setup aiohttp client for Zhipu API."""
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to Zhipu API.
        
        Args:
            endpoint: API endpoint (e.g., 'chat/completions')
            data: Request payload
            
        Returns:
            Response JSON
            
        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}/{endpoint}"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.post(url, json=data) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        raise APIError(
                            f"Zhipu API error: {response_text}",
                            status_code=response.status,
                            response=response_text
                        )

                    return json.loads(response_text)
        except aiohttp.ClientError as e:
            raise APIError(f"Zhipu connection error: {str(e)}", status_code=None, response=None)
        except asyncio.TimeoutError:
            raise APIError("Zhipu request timeout", status_code=408, response=None)

    async def _stream_request(self, endpoint: str, data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a request to Zhipu API.
        
        Args:
            endpoint: API endpoint
            data: Request payload
            
        Yields:
            Response chunks as JSON objects
            
        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}/{endpoint}"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise APIError(
                            f"Zhipu API error: {error_text}",
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
            raise APIError(f"Zhipu connection error: {str(e)}", status_code=None, response=None)
        except asyncio.TimeoutError:
            raise APIError("Zhipu request timeout", status_code=408, response=None)

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
        Create a chat completion using Zhipu's chat completions endpoint.
        """
        data = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature
        }

        if max_tokens is not None:
            data["max_tokens"] = max_tokens

        # Handle Zhipu-specific parameters
        if "top_p" in kwargs:
            data["top_p"] = kwargs["top_p"]
        if "tools" in kwargs:
            data["tools"] = kwargs["tools"]
        if "tool_choice" in kwargs:
            data["tool_choice"] = kwargs["tool_choice"]
        if "response_format" in kwargs:
            data["response_format"] = kwargs["response_format"]
        if "stop" in kwargs:
            data["stop"] = kwargs["stop"]

        response = await self._make_request("chat/completions", data)

        # Handle function calling results
        if "choices" in response and len(response["choices"]) > 0:
            choice = response["choices"][0]
            if "tool_calls" in choice.get("message", {}):
                logger.info(f"Function calls returned: {choice['message']['tool_calls']}")

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
        Create a streaming chat completion using Zhipu's chat completions endpoint.
        """
        data = {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": temperature
        }

        if max_tokens is not None:
            data["max_tokens"] = max_tokens

        # Handle Zhipu-specific parameters
        if "top_p" in kwargs:
            data["top_p"] = kwargs["top_p"]
        if "tools" in kwargs:
            data["tools"] = kwargs["tools"]
        if "tool_choice" in kwargs:
            data["tool_choice"] = kwargs["tool_choice"]
        if "response_format" in kwargs:
            data["response_format"] = kwargs["response_format"]
        if "stop" in kwargs:
            data["stop"] = kwargs["stop"]

        async for chunk in self._stream_request("chat/completions", data):
            if "choices" in chunk and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0].get("delta", {})
                if "content" in delta:
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
        model: str = "glm-4",
        temperature: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform function calling using Zhipu's function calling capabilities.
        """
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

    async def vision_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str = "glm-4v",
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a vision-aware chat completion.
        Supports images in base64 format or URLs.
        """
        # Process image content in messages
        processed_messages = []
        for message in messages:
            if isinstance(message.get("content"), list):
                # Handle multimodal content
                processed_content = []
                for content_item in message["content"]:
                    if content_item.get("type") == "image" and "image" in content_item:
                        # Process image data
                        image_data = content_item["image"]
                        if isinstance(image_data, str) and image_data.startswith("data:image/"):
                            # Base64 encoded image
                            processed_content.append({
                                "type": "image_url",
                                "image_url": {"url": image_data}
                            })
                        else:
                            # Assume it's a URL
                            processed_content.append({
                                "type": "image_url",
                                "image_url": {"url": image_data}
                            })
                    else:
                        processed_content.append(content_item)

                message["content"] = processed_content

            processed_messages.append(message)

        return await self.chat_completion(
            messages=processed_messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    async def embedding(
        self,
        input_text: str,
        model: str = "embedding-2",
        **kwargs
    ) -> List[float]:
        """
        Generate embeddings using Zhipu's embedding endpoint.
        """
        data = {
            "model": model,
            "input": input_text
        }

        try:
            response = await self._make_request("embeddings", data)
            if "data" in response and len(response["data"]) > 0:
                return response["data"][0].get("embedding", [])
            return []
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return []

    def get_available_models(self) -> List[str]:
        """
        Get list of available models for Zhipu AI.
        """
        return [
            # Text models
            "glm-4.6",           # High-performance flagship model
            "glm-4.5",           # Super performance model
            "glm-4.5-air",       # High cost-performance model
            "glm-4.5-flash",     # Free model

            # Vision models
            "glm-4.1v-thinking-flash",  # Free vision reasoning model

            # Image generation
            "cogview-3-flash",   # Free image generation model

            # Video generation
            "cogvideox-flash",   # Free video generation model
        ]

    def validate_model(self, model: str) -> bool:
        """
        Validate if the model is supported by Zhipu AI.
        """
        available_models = self.get_available_models()
        return model in available_models

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model.
        """
        model_info = {
            "glm-4.6": {
                "positioning": "High-performance flagship",
                "features": ["Strongest performance", "Advanced coding", "Powerful reasoning", "Tool calling"],
                "context_length": 200000,
                "max_output": 128000
            },
            "glm-4.5": {
                "positioning": "Super performance",
                "features": ["Excellent performance", "Strong reasoning", "Code generation", "Tool calling"],
                "context_length": 128000,
                "max_output": 96000
            },
            "glm-4.5-air": {
                "positioning": "High cost-performance",
                "features": ["Best performance in same parameter size", "Strong reasoning and coding"],
                "context_length": 128000,
                "max_output": 96000
            },
            "glm-4.5-flash": {
                "positioning": "Free model",
                "features": ["Latest base model version", "Multi-language support", "External tool calling"],
                "context_length": 128000,
                "max_output": 16000
            },
            "glm-4.1v-thinking-flash": {
                "positioning": "Free model",
                "features": ["Vision reasoning", "Complex scene understanding", "Multi-step analysis"],
                "context_length": 64000,
                "max_output": 16000
            },
            "cogview-3-flash": {
                "positioning": "Free model",
                "features": ["Rich creativity", "Fast inference speed"],
                "multi_resolution": True
            },
            "cogvideox-flash": {
                "positioning": "Free model",
                "features": ["Immersive AI sound effects", "4K HD quality", "10s video duration", "60fps output"],
                "input_formats": ["image", "text"]
            }
        }

        return model_info.get(model, {})

    async def web_search(
        self,
        search_query: str,
        search_engine: str = "search_pro",
        count: int = 10,
        search_domain_filter: Optional[str] = None,
        search_recency_filter: str = "noLimit",
        content_size: str = "medium",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform web search using Zhipu's web search capabilities.
        Note: This requires the zai-sdk package and proper setup.
        """
        # This is a placeholder implementation
        # In practice, this would use the zai-sdk package as shown in the documentation
        logger.warning("Web search requires zai-sdk package. This is a placeholder implementation.")

        return {
            "search_query": search_query,
            "search_engine": search_engine,
            "count": count,
            "message": "Web search functionality requires zai-sdk package installation",
            "setup_instructions": "Install with: pip install zai-sdk"
        }

    def get_function_calling_models(self) -> List[str]:
        """
        Get models that support function calling.
        """
        return [
            "glm-4.6",
            "glm-4.5-air",
        ]

    def get_vision_models(self) -> List[str]:
        """
        Get models that support vision/image understanding.
        """
        return [
            "glm-4.1v-thinking-flash"
        ]

    def supports_tool_calling(self, model: str) -> bool:
        """
        Check if a model supports tool calling.
        """
        return model in self.get_function_calling_models()

    def supports_vision(self, model: str) -> bool:
        """
        Check if a model supports vision capabilities.
        """
        return model in self.get_vision_models()