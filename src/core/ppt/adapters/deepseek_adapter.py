# -*- coding: utf-8 -*-
"""
DeepSeek适配器：适配DeepSeek API，支持OpenAI兼容接口。

遵循ollama-rule.txt和deepseek-rule.txt的调用规范，使用OpenAI兼容的API格式。
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
import aiohttp

logger = logging.getLogger(__name__)


class DeepSeekAdapter:
    """DeepSeek API适配器，遵循OpenAI兼容接口规范"""

    def __init__(self):
        """初始化DeepSeek适配器"""
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.default_model = "deepseek-chat"
        self.timeout = 60

        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY未配置，DeepSeek适配器将无法正常工作")

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        生成文本响应

        参数:
            prompt: 输入提示词
            model: 模型名称，默认使用deepseek-chat
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数

        返回:
            生成的文本内容
        """
        model = model or self.default_model

        # 构造请求消息（遵循OpenAI格式）
        messages = [{"role": "user", "content": prompt}]

        # 构造请求体
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
            **kwargs
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"DeepSeek API错误: {response.status}, {error_text}")
                        raise Exception(f"DeepSeek API调用失败: {response.status}")

                    result = await response.json()
                    content = result["choices"][0]["message"]["content"]

                    # 记录使用统计
                    if "usage" in result:
                        usage = result["usage"]
                        logger.info(f"DeepSeek API使用统计: 输入{usage.get('prompt_tokens', 0)} tokens, 输出{usage.get('completion_tokens', 0)} tokens")

                    return content

        except aiohttp.ClientError as e:
            logger.error(f"DeepSeek API网络错误: {str(e)}")
            raise Exception(f"DeepSeek API网络错误: {str(e)}")
        except Exception as e:
            logger.error(f"DeepSeek适配器错误: {str(e)}")
            raise

    async def generate_with_reasoning(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, str]:
        """
        生成带推理过程的响应（使用deepseek-reasoner模型）

        参数:
            prompt: 输入提示词
            model: 模型名称，默认使用deepseek-reasoner
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数

        返回:
            包含推理过程和最终答案的字典
        """
        model = model or "deepseek-reasoner"

        # 构造请求消息
        messages = [{"role": "user", "content": prompt}]

        # 构造请求体
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
            **kwargs
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"DeepSeek Reasoner API错误: {response.status}, {error_text}")
                        raise Exception(f"DeepSeek Reasoner API调用失败: {response.status}")

                    result = await response.json()
                    message = result["choices"][0]["message"]

                    reasoning = ""
                    content = ""

                    # 提取推理过程和最终答案
                    if "reasoning" in message:
                        reasoning = message["reasoning"]
                    if "content" in message:
                        content = message["content"]

                    return {
                        "reasoning": reasoning,
                        "content": content,
                        "model": model
                    }

        except Exception as e:
            logger.error(f"DeepSeek推理模式适配器错误: {str(e)}")
            raise

    async def health_check(self) -> tuple[bool, str]:
        """
        健康检查

        返回:
            (是否健康, 状态消息)
        """
        if not self.api_key:
            return False, "API密钥未配置"

        try:
            # 使用一个简单的测试请求检查健康状态
            test_prompt = "Hello"
            await self.generate(test_prompt, max_tokens=10)
            return True, "正常"
        except Exception as e:
            return False, f"健康检查失败: {str(e)}"

    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表

        返回:
            可用模型名称列表
        """
        return [
            "deepseek-chat",
            "deepseek-coder",
            "deepseek-reasoner"
        ]

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "deepseek-chat"
    ) -> float:
        """
        估算成本（按照DeepSeek官方价格）

        参数:
            input_tokens: 输入token数
            output_tokens: 输出token数
            model: 模型名称

        返回:
            估算成本（人民币）
        """
        # DeepSeek价格（每百万tokens）
        prices = {
            "deepseek-chat": {
                "input": 2.0,    # 每百万tokens输入价格
                "output": 3.0    # 每百万tokens输出价格
            },
            "deepseek-coder": {
                "input": 2.0,
                "output": 3.0
            },
            "deepseek-reasoner": {
                "input": 2.0,
                "output": 3.0
            }
        }

        if model not in prices:
            model = "deepseek-chat"

        price_info = prices[model]
        input_cost = (input_tokens / 1_000_000) * price_info["input"]
        output_cost = (output_tokens / 1_000_000) * price_info["output"]

        return input_cost + output_cost
