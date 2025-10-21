from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import aiohttp
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class _Resp:
    content: str
    model: str


class OllamaProvider:
    """Ollama Provider（使用原生API接口）。"""

    def __init__(self, model_name: str, base_url: str):
        self.model_name = model_name
        # 确保base_url格式正确（去掉/v1后缀）
        if base_url.endswith('/v1'):
            self.base_url = base_url[:-3]
        else:
            self.base_url = base_url.rstrip('/')
        self.timeout = 120

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> _Resp:
        """
        使用Ollama原生API生成响应
        """
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens or 2000,
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama API错误: {response.status}, {error_text}")
                        raise Exception(f"Ollama API调用失败: {response.status}")

                    result = await response.json()

                    if "error" in result:
                        logger.error(f"Ollama模型错误: {result['error']}")
                        raise Exception(f"Ollama模型错误: {result['error']}")

                    content = result.get("message", {}).get("content", "")
                    return _Resp(content=content, model=self.model_name)

        except aiohttp.ClientError as e:
            logger.error(f"Ollama网络错误: {str(e)}")
            raise Exception(f"Ollama网络错误: {str(e)}")
        except Exception as e:
            logger.error(f"Ollama生成错误: {str(e)}")
            raise

    async def health_check(self):
        """健康检查 - 使用Ollama原生API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=30
                ) as response:
                    if response.status == 200:
                        return True, "ok"
                    else:
                        return False, f"HTTP {response.status}"
        except Exception as e:
            return False, str(e)


