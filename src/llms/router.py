from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import os
import yaml
import time
import logging

from src.llms.providers.ollama_llm import OllamaProvider
from src.llms.providers.deepseek_llm import DeepSeekProvider
from src.llms.providers.kimi_llm import KimiProvider
from src.llms.providers.doubao_llm import DoubaoProvider

logger = logging.getLogger(__name__)


@dataclass
class LLMMessage:
    role: str
    content: str


@dataclass
class ModelCapability:
    """模型能力描述"""
    name: str
    provider: str
    context_window: int
    input_cost_per_1k: float  # 输入成本（每1K tokens）
    output_cost_per_1k: float  # 输出成本（每1K tokens）
    max_tokens_per_minute: int
    max_requests_per_minute: int
    supports_function_calling: bool = False
    supports_vision: bool = False
    quality_score: float = 0.5  # 质量评分 (0-1)
    speed_score: float = 0.5    # 速度评分 (0-1)


@dataclass
class RoutingDecision:
    """路由决策结果"""
    provider_name: str
    model_name: str
    reasoning: str
    estimated_cost: float
    estimated_tokens: int
    confidence_score: float
    fallback_options: List[str]


class SmartModelRouter:
    """智能模型路由器：基于任务类型、预算、置信度阈值等因素进行智能决策"""

    def __init__(self, conf: Dict[str, Any]):
        self.conf = conf
        self.providers: Dict[str, Any] = {}
        self.model_capabilities: Dict[str, ModelCapability] = {}
        self.usage_stats: Dict[str, Dict[str, Any]] = {}
        self._init_providers()
        self._init_model_capabilities()
        self._init_usage_stats()

    @classmethod
    def from_conf(cls, path: Path) -> "SmartModelRouter":
        if path.exists():
            conf = yaml.safe_load(path.read_text(encoding="utf-8"))
        else:
            conf = cls._get_default_config()
        return cls(conf)

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "PROVIDER_PRIORITY": {
                "general": ["ollama", "deepseek", "kimi"],
                "research": ["deepseek", "kimi", "ollama"],
                "analysis": ["kimi", "deepseek", "ollama"],
                "creative": ["kimi", "deepseek", "ollama"],
                "coding": ["deepseek", "kimi", "ollama"]
            },
            "OLLAMA_BASE_URL": "http://localhost:11434/v1",
            "OLLAMA_SMALL_MODEL": "qwen2.5:7b",
            "OLLAMA_LARGE_MODEL": "qwen2.5:14b",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1",
            "DEEPSEEK_MODELS": {"chat": "deepseek-chat", "coder": "deepseek-coder"},
            "KIMI_BASE_URL": os.getenv("MOONSHOT_API_BASE", "https://api.moonshot.ai/v1"),
            "KIMI_MODEL": "moonshot-v1-8k",
            # 路由配置
            "ROUTING": {
                "cost_budget_per_request": 0.1,  # 每请求最大预算（美元）
                "quality_threshold": 0.7,        # 质量阈值
                "speed_priority": 0.3,           # 速度优先级权重
                "cost_priority": 0.4,            # 成本优先级权重
                "quality_priority": 0.3,         # 质量优先级权重
                "enable_fallback": True,         # 启用降级策略
                "rate_limit_buffer": 0.8         # 速率限制缓冲（使用80%配额）
            }
        }

    def _init_providers(self) -> None:
        """初始化提供商"""
        # Ollama（本地）
        self.providers["ollama"] = OllamaProvider(
            model_name=self.conf.get("OLLAMA_SMALL_MODEL", "qwen2.5:7b"),
            base_url=self.conf.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        )

        # DeepSeek（需要 API Key）
        self.providers["deepseek"] = DeepSeekProvider(
            model_name=(self.conf.get("DEEPSEEK_MODELS", {}) or {}).get("chat", "deepseek-chat"),
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url=self.conf.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        )

        # Kimi / Moonshot（需要 API Key）
        self.providers["kimi"] = KimiProvider(
            model_name=self.conf.get("KIMI_MODEL", "moonshot-v1-8k"),
            api_key=os.getenv("MOONSHOT_API_KEY", ""),
            base_url=os.getenv("MOONSHOT_API_BASE", self.conf.get("KIMI_BASE_URL", "https://api.moonshot.ai/v1")),
        )
        
        # Doubao / 豆包（需要 API Key）
        self.providers["doubao"] = DoubaoProvider(
            model_name=self.conf.get("DOUBAO_MODEL", "doubao-seed-1-6-flash-250615"),
            api_key=os.getenv("DOUBAO_API_KEY", ""),
            base_url=self.conf.get("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
        )

    def _init_model_capabilities(self) -> None:
        """初始化模型能力信息"""
        self.model_capabilities = {
            "ollama:qwen2.5:7b": ModelCapability(
                name="qwen2.5:7b", provider="ollama", context_window=32768,
                input_cost_per_1k=0.0, output_cost_per_1k=0.0,  # 本地模型免费
                max_tokens_per_minute=100000, max_requests_per_minute=100,
                quality_score=0.7, speed_score=0.8
            ),
            "ollama:qwen2.5:14b": ModelCapability(
                name="qwen2.5:14b", provider="ollama", context_window=32768,
                input_cost_per_1k=0.0, output_cost_per_1k=0.0,
                max_tokens_per_minute=80000, max_requests_per_minute=80,
                quality_score=0.8, speed_score=0.6
            ),
            "deepseek:deepseek-chat": ModelCapability(
                name="deepseek-chat", provider="deepseek", context_window=32768,
                input_cost_per_1k=0.00014, output_cost_per_1k=0.00028,
                max_tokens_per_minute=200000, max_requests_per_minute=100,
                quality_score=0.85, speed_score=0.9
            ),
            "deepseek:deepseek-coder": ModelCapability(
                name="deepseek-coder", provider="deepseek", context_window=16384,
                input_cost_per_1k=0.00014, output_cost_per_1k=0.00028,
                max_tokens_per_minute=200000, max_requests_per_minute=100,
                quality_score=0.9, speed_score=0.85
            ),
            "kimi:moonshot-v1-8k": ModelCapability(
                name="moonshot-v1-8k", provider="kimi", context_window=8192,
                input_cost_per_1k=0.012, output_cost_per_1k=0.012,
                max_tokens_per_minute=120000, max_requests_per_minute=60,
                quality_score=0.9, speed_score=0.8
            ),
            "kimi:moonshot-v1-32k": ModelCapability(
                name="moonshot-v1-32k", provider="kimi", context_window=32768,
                input_cost_per_1k=0.024, output_cost_per_1k=0.024,
                max_tokens_per_minute=80000, max_requests_per_minute=40,
                quality_score=0.95, speed_score=0.7
            ),
            "doubao:doubao-seed-1-6-flash-250615": ModelCapability(
                name="doubao-seed-1-6-flash-250615", provider="doubao", context_window=32768,
                input_cost_per_1k=0.0003, output_cost_per_1k=0.0006,  # 估算价格
                max_tokens_per_minute=200000, max_requests_per_minute=100,
                quality_score=0.88, speed_score=0.95  # 快速响应
            ),
            "doubao:doubao-1-5-vision-pro-250328": ModelCapability(
                name="doubao-1-5-vision-pro-250328", provider="doubao", context_window=32768,
                input_cost_per_1k=0.0005, output_cost_per_1k=0.001,  # 估算价格
                max_tokens_per_minute=150000, max_requests_per_minute=80,
                quality_score=0.92, speed_score=0.85  # 视觉理解模型
            )
        }

    def _init_usage_stats(self) -> None:
        """初始化使用统计"""
        for provider_name in self.providers.keys():
            self.usage_stats[provider_name] = {
                "requests_last_minute": 0,
                "tokens_last_minute": 0,
                "total_cost_today": 0.0,
                "last_reset": datetime.utcnow()
            }

    def _make_routing_decision(
        self,
        task_type: str,
        estimated_input_tokens: int,
        estimated_output_tokens: int,
        quality_requirement: float = 0.7,
        cost_budget: Optional[float] = None,
        speed_requirement: float = 0.5
    ) -> RoutingDecision:
        """
        基于多因素进行路由决策

        Args:
            task_type: 任务类型 ('research', 'analysis', 'creative', 'coding', 'general')
            estimated_input_tokens: 预估输入token数
            estimated_output_tokens: 预估输出token数
            quality_requirement: 质量要求 (0-1)
            cost_budget: 成本预算（美元）
            speed_requirement: 速度要求 (0-1)
        """

        routing_config = self.conf.get("ROUTING", {})
        if cost_budget is None:
            cost_budget = routing_config.get("cost_budget_per_request", 0.1)

        # 获取候选提供商
        priority_list = (self.conf.get("PROVIDER_PRIORITY", {}).get(task_type)
                        or self.conf.get("PROVIDER_PRIORITY", {}).get("general")
                        or ["ollama", "deepseek", "kimi"])

        best_decision = None
        best_score = -1
        fallback_options = []

        for provider_name in priority_list:
            if provider_name not in self.providers:
                continue

            # 检查提供商健康状态
            if not self._is_provider_healthy(provider_name):
                fallback_options.append(provider_name)
                continue

            # 获取可用模型
            available_models = self._get_available_models(provider_name)

            for model_key in available_models:
                if model_key not in self.model_capabilities:
                    continue

                capability = self.model_capabilities[model_key]

                # 检查速率限制
                if self._is_rate_limited(capability):
                    continue

                # 计算预估成本
                estimated_cost = self._calculate_cost(
                    capability, estimated_input_tokens, estimated_output_tokens
                )

                # 检查预算限制
                if estimated_cost > cost_budget:
                    continue

                # 计算综合评分
                score = self._calculate_routing_score(
                    capability, estimated_cost, cost_budget,
                    quality_requirement, speed_requirement
                )

                if score > best_score:
                    best_score = score
                    best_decision = RoutingDecision(
                        provider_name=provider_name,
                        model_name=capability.name,
                        reasoning=self._generate_reasoning(
                            capability, estimated_cost, score, task_type
                        ),
                        estimated_cost=estimated_cost,
                        estimated_tokens=estimated_input_tokens + estimated_output_tokens,
                        confidence_score=min(score, 1.0),
                        fallback_options=fallback_options.copy()
                    )

            if best_decision:
                fallback_options.append(provider_name)

        # 如果没有找到合适的模型，使用默认降级策略
        if not best_decision:
            best_decision = self._get_fallback_decision(
                priority_list[0], estimated_input_tokens, estimated_output_tokens
            )

        return best_decision

    def _calculate_routing_score(
        self,
        capability: ModelCapability,
        estimated_cost: float,
        cost_budget: float,
        quality_req: float,
        speed_req: float
    ) -> float:
        """计算路由评分"""
        routing_config = self.conf.get("ROUTING", {})

        # 质量评分
        quality_score = min(capability.quality_score / quality_req, 1.0)

        # 成本评分（成本越低评分越高）
        cost_ratio = estimated_cost / cost_budget if cost_budget > 0 else 1.0
        cost_score = max(0, 1.0 - cost_ratio)

        # 速度评分
        speed_score = capability.speed_score

        # 加权综合评分
        weights = routing_config
        final_score = (
            quality_score * weights.get("quality_priority", 0.4) +
            cost_score * weights.get("cost_priority", 0.3) +
            speed_score * weights.get("speed_priority", 0.3)
        )

        return final_score

    def _calculate_cost(
        self,
        capability: ModelCapability,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """计算预估成本"""
        input_cost = (input_tokens / 1000) * capability.input_cost_per_1k
        output_cost = (output_tokens / 1000) * capability.output_cost_per_1k
        return input_cost + output_cost

    def _is_provider_healthy(self, provider_name: str) -> bool:
        """检查提供商健康状态"""
        try:
            provider = self.providers[provider_name]
            # 这里可以实现更复杂的健康检查逻辑
            return True
        except Exception:
            return False

    def _is_rate_limited(self, capability: ModelCapability) -> bool:
        """检查是否达到速率限制"""
        routing_config = self.conf.get("ROUTING", {})
        buffer_ratio = routing_config.get("rate_limit_buffer", 0.8)

        stats = self.usage_stats.get(capability.provider, {})
        current_usage = stats.get("requests_last_minute", 0)

        return current_usage >= (capability.max_requests_per_minute * buffer_ratio)

    def _get_available_models(self, provider_name: str) -> List[str]:
        """获取提供商的可用模型"""
        # 这里可以根据提供商返回不同的模型列表
        model_keys = [k for k in self.model_capabilities.keys()
                     if k.startswith(f"{provider_name}:")]
        return model_keys

    def _generate_reasoning(
        self,
        capability: ModelCapability,
        estimated_cost: float,
        score: float,
        task_type: str
    ) -> str:
        """生成路由决策的推理说明"""
        return f"选择 {capability.provider}:{capability.name} 处理 {task_type} 任务。预估成本: ${estimated_cost:.4f}, 综合评分: {score:.2f}"

    def _get_fallback_decision(
        self,
        provider_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> RoutingDecision:
        """获取降级决策"""
        return RoutingDecision(
            provider_name=provider_name,
            model_name=self.providers[provider_name].model_name,
            reasoning=f"降级到默认提供商 {provider_name}",
            estimated_cost=0.0,
            estimated_tokens=input_tokens + output_tokens,
            confidence_score=0.5,
            fallback_options=[]
        )

    async def route_and_chat(
        self,
        task_type: str,
        messages: List[LLMMessage],
        estimated_input_tokens: int = 1000,
        estimated_output_tokens: int = 1000,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        quality_requirement: float = 0.7,
        cost_budget: Optional[float] = None,
        speed_requirement: float = 0.5
    ) -> Dict[str, Any]:
        """
        智能路由并执行聊天请求

        返回格式:
        {
            "content": "响应内容",
            "model": "使用的模型",
            "provider": "使用的提供商",
            "routing_decision": RoutingDecision对象,
            "actual_cost": 实际成本,
            "tokens_used": 使用的token数,
            "processing_time": 处理时间
        }
        """

        start_time = time.time()

        # 进行路由决策
        decision = self._make_routing_decision(
            task_type=task_type,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            quality_requirement=quality_requirement,
            cost_budget=cost_budget,
            speed_requirement=speed_requirement
        )

        logger.info(f"路由决策: {decision.provider_name}:{decision.model_name}, 原因: {decision.reasoning}")

        # 执行请求
        provider = self.providers[decision.provider_name]

        # 更新使用统计
        self._update_usage_stats(decision.provider_name, 1, estimated_input_tokens)

        try:
            result = await provider.generate(
                messages=[{"role": m.role, "content": m.content} for m in messages],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            processing_time = time.time() - start_time

            # 计算实际成本（这里需要根据实际token使用情况计算）
            actual_tokens = getattr(result, 'usage', {}).get('total_tokens', estimated_input_tokens + estimated_output_tokens)
            actual_cost = self._calculate_cost(
                self.model_capabilities.get(f"{decision.provider_name}:{decision.model_name}"),
                actual_tokens // 2,  # 粗略估算输入输出比例
                actual_tokens // 2
            )

            return {
                "content": result.content,
                "model": result.model,
                "provider": decision.provider_name,
                "routing_decision": decision,
                "actual_cost": actual_cost,
                "tokens_used": actual_tokens,
                "processing_time": processing_time
            }

        except Exception as e:
            logger.error(f"模型调用失败: {decision.provider_name}:{decision.model_name}, 错误: {str(e)}")

            # 如果启用降级且有备用选项，尝试降级
            if self.conf.get("ROUTING", {}).get("enable_fallback", True) and decision.fallback_options:
                return await self._fallback_chat(
                    decision.fallback_options[0], messages, temperature, max_tokens
                )

            raise e

    async def _fallback_chat(
        self,
        provider_name: str,
        messages: List[LLMMessage],
        temperature: float,
        max_tokens: Optional[int]
    ) -> Dict[str, Any]:
        """降级到备用提供商"""
        logger.info(f"降级到备用提供商: {provider_name}")

        provider = self.providers[provider_name]
        result = await provider.generate(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return {
            "content": result.content,
            "model": result.model,
            "provider": provider_name,
            "routing_decision": None,
            "actual_cost": 0.0,
            "tokens_used": 0,
            "processing_time": 0.0
        }

    def _update_usage_stats(self, provider_name: str, requests: int, tokens: int):
        """更新使用统计"""
        if provider_name not in self.usage_stats:
            self.usage_stats[provider_name] = {
                "requests_last_minute": 0,
                "tokens_last_minute": 0,
                "total_cost_today": 0.0,
                "last_reset": datetime.utcnow()
            }

        stats = self.usage_stats[provider_name]
        stats["requests_last_minute"] += requests
        stats["tokens_last_minute"] += tokens

    async def get_routing_stats(self) -> Dict[str, Any]:
        """获取路由统计信息"""
        return {
            "usage_stats": self.usage_stats,
            "model_capabilities": {
                k: {
                    "provider": v.provider,
                    "quality_score": v.quality_score,
                    "speed_score": v.speed_score,
                    "input_cost_per_1k": v.input_cost_per_1k,
                    "output_cost_per_1k": v.output_cost_per_1k
                }
                for k, v in self.model_capabilities.items()
            },
            "routing_config": self.conf.get("ROUTING", {})
        }

    async def health(self) -> Dict[str, Any]:
        """健康检查"""
        results = {}
        for name, provider in self.providers.items():
            try:
                ok, message = await provider.health_check()
            except Exception as e:
                ok, message = False, str(e)
            results[name] = {"ok": ok, "message": message}

        return {
            "providers": results,
            "provider_priority": self.conf.get("PROVIDER_PRIORITY", {}),
            "routing_config": self.conf.get("ROUTING", {}),
            "usage_stats": self.usage_stats
        }


# 为了向后兼容，保留原来的ModelRouter类名
ModelRouter = SmartModelRouter


