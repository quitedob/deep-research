"""
Ollama LLM provider implementation.
Based on the Ollama API documentation from ollama-rule.txt
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
import json
import logging

from src.core.llm.base_llm import BaseLLM, APIError, ConfigurationError

logger = logging.getLogger(__name__)


class OllamaLLM(BaseLLM):
    """
    Ollama LLM provider for local models.
    Supports both /api/generate and /api/chat endpoints.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = "http://localhost:11434", **kwargs):
        """
        Initialize Ollama LLM provider.

        Args:
            api_key: Not required for Ollama (kept for interface consistency)
            base_url: Ollama server URL (default: http://localhost:11434)
            **kwargs: Additional configuration parameters
        """
        self.base_url = base_url.rstrip('/')
        # Store base_url before calling super().__init__() so validate_config can use it
        super().__init__(api_key, **kwargs)

    def get_api_key_env_name(self) -> str:
        """Ollama doesn't require an API key."""
        return "OLLAMA_API_KEY"
    
    def validate_config(self) -> None:
        """
        Validate Ollama configuration.
        Ollama doesn't require an API key, but needs a valid base URL.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.base_url:
            raise ConfigurationError("Ollama base_url is required")
        
        if not self.base_url.startswith(("http://", "https://")):
            raise ConfigurationError(f"Invalid Ollama base_url: {self.base_url}. Must start with http:// or https://")

    def _setup_client(self) -> None:
        """Setup aiohttp client for Ollama API."""
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes timeout

    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to Ollama API.
        
        Args:
            endpoint: API endpoint (e.g., 'chat', 'generate')
            data: Request payload
            
        Returns:
            Response JSON
            
        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}/api/{endpoint}"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise APIError(
                            f"Ollama API error: {error_text}",
                            status_code=response.status,
                            response=error_text
                        )

                    return await response.json()
        except aiohttp.ClientError as e:
            raise APIError(f"Ollama connection error: {str(e)}", status_code=None, response=None)
        except asyncio.TimeoutError:
            raise APIError("Ollama request timeout", status_code=408, response=None)

    async def _stream_request(self, endpoint: str, data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a request to Ollama API.
        
        Args:
            endpoint: API endpoint
            data: Request payload
            
        Yields:
            Response chunks as JSON objects
            
        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}/api/{endpoint}"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise APIError(
                            f"Ollama API error: {error_text}",
                            status_code=response.status,
                            response=error_text
                        )

                    async for line in response.content:
                        if line:
                            try:
                                yield json.loads(line.decode('utf-8').strip())
                            except json.JSONDecodeError:
                                continue
        except aiohttp.ClientError as e:
            raise APIError(f"Ollama connection error: {str(e)}", status_code=None, response=None)
        except asyncio.TimeoutError:
            raise APIError("Ollama request timeout", status_code=408, response=None)

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
        Create a chat completion using Ollama's /api/chat endpoint.
        """
        data = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                **kwargs.get("options", {})
            }
        }

        if max_tokens:
            data["options"]["num_predict"] = max_tokens

        # Handle additional parameters
        if "format" in kwargs:
            data["format"] = kwargs["format"]
        if "keep_alive" in kwargs:
            data["keep_alive"] = kwargs["keep_alive"]

        response = await self._make_request("chat", data)

        # Convert to standard format
        # Handle created_at timestamp safely
        created_at = response.get("created_at", "")
        try:
            # Try to parse ISO timestamp to unix timestamp
            from datetime import datetime
            if created_at:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_timestamp = int(dt.timestamp())
            else:
                created_timestamp = 0
        except (ValueError, AttributeError):
            created_timestamp = 0
        
        return {
            "id": created_at,
            "object": "chat.completion",
            "created": created_timestamp,
            "model": response.get("model", model),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response.get("message", {}).get("content", "")
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": response.get("prompt_eval_count", 0),
                "completion_tokens": response.get("eval_count", 0),
                "total_tokens": response.get("prompt_eval_count", 0) + response.get("eval_count", 0)
            }
        }

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Create a streaming chat completion using Ollama's /api/chat endpoint.
        """
        data = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                **kwargs.get("options", {})
            }
        }

        if max_tokens:
            data["options"]["num_predict"] = max_tokens

        # Handle additional parameters
        if "format" in kwargs:
            data["format"] = kwargs["format"]
        if "keep_alive" in kwargs:
            data["keep_alive"] = kwargs["keep_alive"]

        async for chunk in self._stream_request("chat", data):
            if chunk.get("done"):
                break

            message = chunk.get("message", {})
            content = message.get("content", "")
            if content:
                yield content
    
    async def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate text from a prompt using Ollama's /api/generate endpoint.
        This is the required method from BaseLLM interface.
        
        Args:
            prompt: Input prompt text
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional parameters (system, template, format, etc.)
            
        Returns:
            Generated text string
        """
        response = await self.generate_completion(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            **kwargs
        )
        
        # Extract text from response
        return response.get("choices", [{}])[0].get("text", "")

    async def generate_completion(
        self,
        prompt: str,
        model: str,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate completion using Ollama's /api/generate endpoint.
        """
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                **kwargs.get("options", {})
            }
        }

        if max_tokens:
            data["options"]["num_predict"] = max_tokens

        # Handle additional parameters
        if "system" in kwargs:
            data["system"] = kwargs["system"]
        if "template" in kwargs:
            data["template"] = kwargs["template"]
        if "context" in kwargs:
            data["context"] = kwargs["context"]
        if "suffix" in kwargs:
            data["suffix"] = kwargs["suffix"]
        if "raw" in kwargs:
            data["raw"] = kwargs["raw"]
        if "format" in kwargs:
            data["format"] = kwargs["format"]
        if "keep_alive" in kwargs:
            data["keep_alive"] = kwargs["keep_alive"]

        response = await self._make_request("generate", data)

        # Handle created_at timestamp safely
        created_at = response.get("created_at", "")
        try:
            from datetime import datetime
            if created_at:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_timestamp = int(dt.timestamp())
            else:
                created_timestamp = 0
        except (ValueError, AttributeError):
            created_timestamp = 0

        return {
            "id": created_at,
            "object": "text.completion",
            "created": created_timestamp,
            "model": response.get("model", model),
            "choices": [
                {
                    "index": 0,
                    "text": response.get("response", ""),
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": response.get("prompt_eval_count", 0),
                "completion_tokens": response.get("eval_count", 0),
                "total_tokens": response.get("prompt_eval_count", 0) + response.get("eval_count", 0)
            }
        }

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models using Ollama's /api/tags endpoint.
        """
        try:
            response = await self._make_request("tags", {})
            return response.get("models", [])
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    def get_available_models(self) -> List[str]:
        """
        Get list of available models for Ollama.
        Note: This is a synchronous version for interface compatibility.
        In async context, use list_models() instead.
        """
        # Common Ollama models - user should update this list based on installed models
        return [
            "gemma3:4b",
            "gemma3:12b"
        ]

    def validate_model(self, model: str) -> bool:
        """
        Validate if the model is supported.
        For Ollama, most models can be pulled if they don't exist.
        """
        # Basic validation - check if model name is not empty
        return bool(model and isinstance(model, str))

    async def pull_model(self, model: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Pull a model from Ollama library.

        Args:
            model: Model name to pull

        Yields:
            Status updates during the pull process
        """
        data = {"name": model}

        async for chunk in self._stream_request("pull", data):
            yield chunk

    async def show_model_info(self, model: str) -> Dict[str, Any]:
        """
        Show detailed information about a model.
        """
        data = {"name": model}

        try:
            response = await self._make_request("show", data)
            return response
        except Exception as e:
            logger.error(f"Failed to show model info for {model}: {e}")
            return {}

    async def delete_model(self, model: str) -> bool:
        """
        Delete a model from Ollama.
        """
        data = {"name": model}

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.delete(f"{self.base_url}/api/delete", json=data) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Failed to delete model {model}: {e}")
            return False

    async def embeddings(
        self,
        input_text: str,
        model: str,
        truncate: bool = True,
        **kwargs
    ) -> List[float]:
        """
        Generate embeddings using Ollama's /api/embed endpoint.
        """
        data = {
            "model": model,
            "input": input_text,
            "truncate": truncate
        }

        if "options" in kwargs:
            data["options"] = kwargs["options"]
        if "keep_alive" in kwargs:
            data["keep_alive"] = kwargs["keep_alive"]

        try:
            response = await self._make_request("embed", data)
            # Ollama returns "embeddings" (plural) as an array of arrays
            # For single input, we return the first embedding
            embeddings = response.get("embeddings", [])
            if embeddings and len(embeddings) > 0:
                return embeddings[0]  # Return first embedding for single input
            return []
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return []