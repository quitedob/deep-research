# -*- coding: utf-8 -*-
"""
ZhipuAI Provider Implementation
智谱AI provider implementation based on z_rule.txt specifications

Supports:
- GLM-4.6: Flagship model (200K context, 128K output)
- GLM-4.5: High performance (128K context, 96K output)
- GLM-4.5-Air: Cost-effective (128K context, 96K output)
- GLM-4.5-Flash: Free model (128K context, 16K output)
- GLM-4.1V-Thinking-Flash: Free vision model (64K context, 16K output)
- Web Search API integration
- Function calling capabilities
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
import os
import json
import logging
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


@dataclass
class _Resp:
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None


class ZhipuAIProvider:
    """ZhipuAI Provider（智谱AI）。

    基于z_rule.txt规范的智谱AIprovider实现，支持多种模型和搜索功能。
    """

    def __init__(self, model_name: str, api_key: str, base_url: str = "https://open.bigmodel.cn/api/paas/v4"):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        # 模型能力映射
        self.model_capabilities = {
            "glm-4.6": {
                "context_window": 200000,
                "max_output": 128000,
                "supports_function_calling": True,
                "supports_vision": False,
                "is_free": False
            },
            "glm-4.5": {
                "context_window": 128000,
                "max_output": 96000,
                "supports_function_calling": True,
                "supports_vision": False,
                "is_free": False
            },
            "glm-4.5-air": {
                "context_window": 128000,
                "max_output": 96000,
                "supports_function_calling": True,
                "supports_vision": False,
                "is_free": False
            },
            "glm-4.5-flash": {
                "context_window": 128000,
                "max_output": 16000,
                "supports_function_calling": True,
                "supports_vision": False,
                "is_free": True
            },
            "glm-4.1v-thinking-flash": {
                "context_window": 64000,
                "max_output": 16000,
                "supports_function_calling": True,
                "supports_vision": True,
                "is_free": True
            }
        }

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> _Resp:
        """生成响应"""
        try:
            # 构建请求参数
            params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                params["max_tokens"] = max_tokens

            if tools:
                params["tools"] = tools

            # 调用API
            resp = await self.client.chat.completions.create(**params)

            return _Resp(
                content=resp.choices[0].message.content or "",
                model=resp.model,
                usage=resp.usage.model_dump() if resp.usage else None
            )

        except Exception as e:
            logger.error(f"ZhipuAI API调用失败: {str(e)}")
            raise

    async def generate_with_web_search(
        self,
        messages: List[Dict[str, Any]],
        search_config: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> _Resp:
        """使用网络搜索生成响应

        Args:
            messages: 对话消息
            search_config: 搜索配置
                - search_engine: 搜索引擎 (search_pro, search_pro_sogou, search_pro_quark)
                - count: 返回结果数量 (1-50)
                - search_domain_filter: 域名过滤
                - search_recency_filter: 时间过滤
                - content_size: 内容大小 (low, medium, high)
            temperature: 温度参数
            max_tokens: 最大token数
        """
        try:
            # 默认搜索配置
            default_search_config = {
                "enable": "True",
                "search_engine": "search_pro",
                "search_result": "True",
                "search_prompt": "你是一位研究分析师。请用简洁的语言总结网络搜索结果中的关键信息，按重要性排序并引用来源。",
                "count": "5",
                "search_domain_filter": "",
                "search_recency_filter": "noLimit",
                "content_size": "medium"
            }

            # 合并搜索配置
            final_search_config = {**default_search_config, **(search_config or {})}

            # 构建工具参数
            tools = [{
                "type": "web_search",
                "web_search": final_search_config
            }]

            return await self.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                **kwargs
            )

        except Exception as e:
            logger.error(f"ZhipuAI网络搜索失败: {str(e)}")
            # 降级到普通生成
            return await self.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

    async def web_search_only(
        self,
        search_query: str,
        search_engine: str = "search_pro",
        count: int = 10,
        search_domain_filter: str = "",
        search_recency_filter: str = "noLimit",
        content_size: str = "medium"
    ) -> Dict[str, Any]:
        """仅执行网络搜索

        Args:
            search_query: 搜索查询
            search_engine: 搜索引擎
            count: 返回结果数量
            search_domain_filter: 域名过滤
            search_recency_filter: 时间过滤
            content_size: 内容大小
        """
        try:
            # 如果安装了zai-sdk，使用官方SDK
            try:
                from zai import ZhipuAiClient
                client = ZhipuAiClient(api_key=self.api_key)

                response = client.web_search.web_search(
                    search_engine=search_engine,
                    search_query=search_query,
                    count=count,
                    search_domain_filter=search_domain_filter,
                    search_recency_filter=search_recency_filter,
                    content_size=content_size
                )
                return response

            except ImportError:
                # 如果没有安装zai-sdk，使用OpenAI兼容接口
                logger.warning("未安装zai-sdk，使用OpenAI兼容接口进行搜索")

                tools = [{
                    "type": "web_search",
                    "web_search": {
                        "enable": "True",
                        "search_engine": search_engine,
                        "search_result": "True",
                        "count": str(count),
                        "search_domain_filter": search_domain_filter,
                        "search_recency_filter": search_recency_filter,
                        "content_size": content_size
                    }
                }]

                messages = [{"role": "user", "content": search_query}]

                resp = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=tools
                )

                return {
                    "query": search_query,
                    "response": resp.choices[0].message.content,
                    "model": resp.model
                }

        except Exception as e:
            logger.error(f"网络搜索失败: {str(e)}")
            raise

    async def health_check(self) -> tuple[bool, str]:
        """健康检查"""
        try:
            # 尝试获取模型列表
            await self.client.models.list()
            return True, "ok"
        except Exception as e:
            return False, str(e)

    def get_model_info(self, model_name: str = None) -> Dict[str, Any]:
        """获取模型信息"""
        model = model_name or self.model_name
        return self.model_capabilities.get(model, {})

    def supports_function_calling(self, model_name: str = None) -> bool:
        """检查模型是否支持函数调用"""
        model = model_name or self.model_name
        return self.model_capabilities.get(model, {}).get("supports_function_calling", False)

    def supports_vision(self, model_name: str = None) -> bool:
        """检查模型是否支持视觉理解"""
        model = model_name or self.model_name
        return self.model_capabilities.get(model, {}).get("supports_vision", False)

    def is_free_model(self, model_name: str = None) -> bool:
        """检查模型是否免费"""
        model = model_name or self.model_name
        return self.model_capabilities.get(model, {}).get("is_free", False)

    def get_context_window(self, model_name: str = None) -> int:
        """获取模型上下文窗口大小"""
        model = model_name or self.model_name
        return self.model_capabilities.get(model, {}).get("context_window", 0)

    def get_max_output(self, model_name: str = None) -> int:
        """获取模型最大输出长度"""
        model = model_name or self.model_name
        return self.model_capabilities.get(model, {}).get("max_output", 0)

    @staticmethod
    def get_available_models() -> List[str]:
        """获取可用模型列表"""
        return [
            "glm-4.6",
            "glm-4.5",
            "glm-4.5-air",
            "glm-4.5-flash",
            "glm-4.1v-thinking-flash"
        ]

    @staticmethod
    def get_search_engines() -> List[str]:
        """获取支持的搜索引擎"""
        return [
            "search_std",      # 基础版（智谱AI自研）
            "search_pro",      # 高级版（智谱AI自研）
            "search_pro_sogou", # 搜狗
            "search_pro_quark"  # 夸克
        ]