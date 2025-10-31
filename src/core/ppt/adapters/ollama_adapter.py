# -*- coding: utf-8 -*-
"""
Ollama适配器：适配本地Ollama服务，支持REST API调用。

遵循ollama-rule.txt规范，使用Ollama的原生API接口。
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
import aiohttp

logger = logging.getLogger(__name__)


class OllamaAdapter:
    """Ollama本地服务适配器"""

    def __init__(self):
        """初始化Ollama适配器"""
        self.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.default_model = os.getenv("OLLAMA_PPT_MODEL", "llama3.2:3b")
        self.timeout = 120  # Ollama通常需要更长时间

        logger.info(f"Ollama适配器初始化完成，基础URL: {self.base_url}")

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        生成文本响应（使用/generate端点）

        参数:
            prompt: 输入提示词
            model: 模型名称，默认使用环境变量配置的模型
            max_tokens: 最大token数（Ollama使用num_predict参数）
            temperature: 温度参数
            **kwargs: 其他参数

        返回:
            生成的文本内容
        """
        model = model or self.default_model

        # 构造请求体（遵循Ollama API规范）
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                **kwargs.get("options", {})
            },
            **kwargs
        }

        # 移除options中的重复项
        if "options" in payload:
            payload["options"].pop("temperature", None)
            payload["options"].pop("num_predict", None)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
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

                    content = result.get("response", "")

                    # 记录统计信息
                    if "eval_count" in result:
                        logger.info(f"Ollama生成统计: {result['eval_count']} tokens")

                    return content

        except aiohttp.ClientError as e:
            logger.error(f"Ollama网络错误: {str(e)}")
            raise Exception(f"Ollama网络错误: {str(e)}")
        except Exception as e:
            logger.error(f"Ollama适配器错误: {str(e)}")
            raise

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        生成聊天响应（使用/chat端点，更符合OpenAI风格）

        参数:
            messages: 消息历史列表，格式如[{"role": "user", "content": "..."}]
            model: 模型名称
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数

        返回:
            生成的文本内容
        """
        model = model or self.default_model

        # 构造请求体
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                **kwargs.get("options", {})
            },
            **kwargs
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
                        logger.error(f"Ollama Chat API错误: {response.status}, {error_text}")
                        raise Exception(f"Ollama Chat API调用失败: {response.status}")

                    result = await response.json()

                    if "error" in result:
                        logger.error(f"Ollama聊天模型错误: {result['error']}")
                        raise Exception(f"Ollama聊天模型错误: {result['error']}")

                    content = result.get("message", {}).get("content", "")

                    # 记录统计信息
                    if "eval_count" in result:
                        logger.info(f"Ollama聊天生成统计: {result['eval_count']} tokens")

                    return content

        except Exception as e:
            logger.error(f"Ollama聊天适配器错误: {str(e)}")
            raise

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        获取可用模型列表

        返回:
            模型信息列表
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"Ollama列出模型失败: {response.status}")
                        return []

                    result = await response.json()
                    return result.get("models", [])

        except Exception as e:
            logger.error(f"Ollama列出模型错误: {str(e)}")
            return []

    async def health_check(self) -> tuple[bool, str]:
        """
        健康检查

        返回:
            (是否健康, 状态消息)
        """
        try:
            models = await self.list_models()
            if not models:
                return False, "无法获取模型列表，Ollama服务可能未运行"

            # 检查默认模型是否存在
            model_names = [model["name"] for model in models]
            if self.default_model not in model_names:
                logger.warning(f"默认模型 {self.default_model} 未找到，可用模型: {model_names}")

            return True, f"正常，可用模型数量: {len(models)}"

        except Exception as e:
            return False, f"健康检查失败: {str(e)}"

    def get_available_models(self) -> List[str]:
        """
        获取可用模型名称列表（同步版本）

        返回:
            可用模型名称列表
        """
        try:
            # 这里使用同步方式，因为这是辅助方法
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code != 200:
                return []

            result = response.json()
            return [model["name"] for model in result.get("models", [])]

        except Exception as e:
            logger.error(f"获取Ollama模型列表错误: {str(e)}")
            return []

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = None
    ) -> float:
        """
        估算成本（Ollama本地运行，成本为0）

        参数:
            input_tokens: 输入token数
            output_tokens: 输出token数
            model: 模型名称（忽略）

        返回:
            估算成本（始终为0）
        """
        return 0.0  # Ollama本地运行，无API费用


