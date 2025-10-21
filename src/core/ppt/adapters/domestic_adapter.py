# -*- coding: utf-8 -*-
"""
国内厂商适配器骨架

统一封装阿里云、百度、腾讯、讯飞等国内LLM厂商的API调用。
"""

import os
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class DomesticAdapter:
    """国内厂商统一适配器"""

    def __init__(self):
        """初始化国内厂商适配器"""
        self.providers = {
            "aliyun": self._init_aliyun(),
            "baidu": self._init_baidu(),
            "tencent": self._init_tencent(),
            "xfyun": self._init_xfyun()
        }

        self.default_provider = "aliyun"
        logger.info("国内厂商适配器初始化完成")

    def _init_aliyun(self) -> Dict[str, Any]:
        """初始化阿里云配置"""
        return {
            "enabled": bool(os.getenv("ALIYUN_API_KEY")),
            "api_key": os.getenv("ALIYUN_API_KEY", ""),
            "model": os.getenv("ALIYUN_MODEL", "qwen-plus"),
            "base_url": "https://dashscope.aliyuncs.com/api/v1"
        }

    def _init_baidu(self) -> Dict[str, Any]:
        """初始化百度配置"""
        return {
            "enabled": bool(os.getenv("BAIDU_API_KEY")),
            "api_key": os.getenv("BAIDU_API_KEY", ""),
            "secret_key": os.getenv("BAIDU_SECRET_KEY", ""),
            "model": os.getenv("BAIDU_MODEL", "ernie-bot"),
            "base_url": "https://aip.baidubce.com"
        }

    def _init_tencent(self) -> Dict[str, Any]:
        """初始化腾讯配置"""
        return {
            "enabled": bool(os.getenv("TENCENT_SECRET_ID")),
            "secret_id": os.getenv("TENCENT_SECRET_ID", ""),
            "secret_key": os.getenv("TENCENT_SECRET_KEY", ""),
            "model": os.getenv("TENCENT_MODEL", "hunyuan-lite"),
            "region": os.getenv("TENCENT_REGION", "ap-guangzhou")
        }

    def _init_xfyun(self) -> Dict[str, Any]:
        """初始化讯飞配置"""
        return {
            "enabled": bool(os.getenv("XFYUN_APP_ID")),
            "app_id": os.getenv("XFYUN_APP_ID", ""),
            "api_key": os.getenv("XFYUN_API_KEY", ""),
            "api_secret": os.getenv("XFYUN_API_SECRET", ""),
            "model": os.getenv("XFYUN_MODEL", "spark-3.5")
        }

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        生成文本响应

        参数:
            prompt: 输入提示词
            model: 模型名称
            provider: 指定provider（aliyun/baidu/tencent/xfyun）
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数

        返回:
            生成的文本内容
        """
        provider = provider or self.default_provider

        if provider not in self.providers:
            raise ValueError(f"不支持的provider: {provider}")

        provider_config = self.providers[provider]
        if not provider_config.get("enabled"):
            raise Exception(f"Provider {provider} 未配置或未启用")

        # 根据不同provider调用相应的方法
        if provider == "aliyun":
            return await self._generate_aliyun(prompt, model, max_tokens, temperature, **kwargs)
        elif provider == "baidu":
            return await self._generate_baidu(prompt, model, max_tokens, temperature, **kwargs)
        elif provider == "tencent":
            return await self._generate_tencent(prompt, model, max_tokens, temperature, **kwargs)
        elif provider == "xfyun":
            return await self._generate_xfyun(prompt, model, max_tokens, temperature, **kwargs)
        else:
            raise ValueError(f"未实现的provider: {provider}")

    async def _generate_aliyun(
        self,
        prompt: str,
        model: Optional[str],
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> str:
        """阿里云生成（待实现）"""
        logger.warning("阿里云API调用暂未实现")
        raise NotImplementedError("阿里云API调用暂未实现，请配置API密钥并实现相关逻辑")

    async def _generate_baidu(
        self,
        prompt: str,
        model: Optional[str],
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> str:
        """百度生成（待实现）"""
        logger.warning("百度API调用暂未实现")
        raise NotImplementedError("百度API调用暂未实现，请配置API密钥并实现相关逻辑")

    async def _generate_tencent(
        self,
        prompt: str,
        model: Optional[str],
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> str:
        """腾讯生成（待实现）"""
        logger.warning("腾讯API调用暂未实现")
        raise NotImplementedError("腾讯API调用暂未实现，请配置API密钥并实现相关逻辑")

    async def _generate_xfyun(
        self,
        prompt: str,
        model: Optional[str],
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> str:
        """讯飞生成（待实现）"""
        logger.warning("讯飞API调用暂未实现")
        raise NotImplementedError("讯飞API调用暂未实现，请配置API密钥并实现相关逻辑")

    async def health_check(self, provider: Optional[str] = None) -> tuple[bool, str]:
        """
        健康检查

        参数:
            provider: 指定provider，None表示检查所有

        返回:
            (是否健康, 状态消息)
        """
        if provider:
            if provider not in self.providers:
                return False, f"未知的provider: {provider}"

            config = self.providers[provider]
            if not config.get("enabled"):
                return False, f"Provider {provider} 未配置"

            return True, f"Provider {provider} 配置正常"

        # 检查所有provider
        enabled_providers = [
            name for name, config in self.providers.items()
            if config.get("enabled")
        ]

        if not enabled_providers:
            return False, "没有启用的国内厂商provider"

        return True, f"已启用的providers: {', '.join(enabled_providers)}"

    def get_available_providers(self) -> List[str]:
        """
        获取可用的provider列表

        返回:
            可用provider名称列表
        """
        return [
            name for name, config in self.providers.items()
            if config.get("enabled")
        ]

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        provider: str = "aliyun",
        model: str = None
    ) -> float:
        """
        估算成本

        参数:
            input_tokens: 输入token数
            output_tokens: 输出token数
            provider: provider名称
            model: 模型名称

        返回:
            估算成本（人民币）
        """
        # 这里是示例价格，实际应根据各厂商官方定价
        prices = {
            "aliyun": {
                "qwen-plus": {"input": 0.8, "output": 2.0},  # 每百万tokens
                "qwen-turbo": {"input": 0.3, "output": 0.6}
            },
            "baidu": {
                "ernie-bot": {"input": 1.2, "output": 1.2}
            },
            "tencent": {
                "hunyuan-lite": {"input": 0.0, "output": 0.0}  # 免费
            },
            "xfyun": {
                "spark-3.5": {"input": 1.0, "output": 1.0}
            }
        }

        if provider not in prices:
            return 0.0

        provider_prices = prices[provider]
        if model and model in provider_prices:
            price_info = provider_prices[model]
        else:
            # 使用第一个模型的价格
            price_info = list(provider_prices.values())[0]

        input_cost = (input_tokens / 1_000_000) * price_info["input"]
        output_cost = (output_tokens / 1_000_000) * price_info["output"]

        return input_cost + output_cost


# 全局实例
_domestic_adapter: Optional[DomesticAdapter] = None


def get_domestic_adapter() -> DomesticAdapter:
    """获取国内厂商适配器实例（单例模式）"""
    global _domestic_adapter
    if _domestic_adapter is None:
        _domestic_adapter = DomesticAdapter()
    return _domestic_adapter

