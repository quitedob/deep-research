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
from src.llms.providers.zhipuai_llm import ZhipuAIProvider

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
                "general": ["ollama", "zhipuai", "doubao", "deepseek", "kimi"],
                "research": ["zhipuai", "doubao", "kimi", "deepseek", "ollama"],
                "analysis": ["zhipuai", "doubao", "deepseek", "kimi", "ollama"],
                "creative": ["zhipuai", "doubao", "deepseek", "ollama", "kimi"],
                "coding": ["deepseek", "zhipuai", "ollama", "doubao", "kimi"],
                "reasoning": ["zhipuai", "deepseek", "ollama", "doubao", "kimi"],  # ZhipuAI GLM-4.6 擅长推理
                "vision": ["zhipuai", "doubao", "ollama", "deepseek"],  # ZhipuAI GLM-4.1V 支持视觉
                "search": ["zhipuai", "doubao", "kimi", "deepseek", "ollama"],  # 搜索能力优先
                "triage": ["ollama", "doubao", "zhipuai", "deepseek"],  # 路由分类本地优先
                "simple_chat": ["ollama", "zhipuai", "doubao", "deepseek"]  # 简单聊天本地优先
            },
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "OLLAMA_SMALL_MODEL": "qwen2.5:7b",
            "OLLAMA_LARGE_MODEL": "qwen2.5:14b",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1",
            "DEEPSEEK_MODELS": {"chat": "deepseek-chat", "coder": "deepseek-coder"},
            "KIMI_BASE_URL": os.getenv("MOONSHOT_API_BASE", "https://api.moonshot.ai/v1"),
            "KIMI_MODEL": "moonshot-v1-8k",
            "ZHIPUAI_BASE_URL": "https://open.bigmodel.cn/api/paas/v4",
            "ZHIPUAI_MODELS": {
                "chat": "glm-4.5-air",        # 默认聊天模型（高性价比）
                "reasoning": "glm-4.6",        # 推理模型（旗舰）
                "vision": "glm-4.1v-thinking-flash",  # 视觉模型（免费）
                "search": "glm-4.5-flash",     # 搜索模型（免费）
                "free": "glm-4.5-flash",      # 免费模型
                "premium": "glm-4.6",          # 旗舰模型
                "cost_effective": "glm-4.5-air"  # 高性价比模型
            },
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

        # ZhipuAI / 智谱AI（需要 API Key）
        zhipuai_models = self.conf.get("ZHIPUAI_MODELS", {})
        self.providers["zhipuai"] = ZhipuAIProvider(
            model_name=zhipuai_models.get("chat", "glm-4.5-air"),
            api_key=os.getenv("ZHIPUAI_API_KEY", ""),
            base_url=self.conf.get("ZHIPUAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
        )

    def _init_model_capabilities(self) -> None:
        """初始化模型能力信息"""
        self.model_capabilities = {
            "ollama:qwen2.5:7b": ModelCapability(
                name="qwen2.5:7b", provider="ollama", context_window=32768,
                input_cost_per_1k=0.0, output_cost_per_1k=0.0,  # 本地模型免费
                max_tokens_per_minute=100000, max_requests_per_minute=100,
                quality_score=0.7, speed_score=0.8,
                supports_function_calling=True,  # qwen2.5 支持函数调用
                supports_vision=False
            ),
            "ollama:qwen2.5:14b": ModelCapability(
                name="qwen2.5:14b", provider="ollama", context_window=32768,
                input_cost_per_1k=0.0, output_cost_per_1k=0.0,
                max_tokens_per_minute=80000, max_requests_per_minute=80,
                quality_score=0.8, speed_score=0.6,
                supports_function_calling=True,  # qwen2.5 支持函数调用
                supports_vision=False
            ),
            "deepseek:deepseek-chat": ModelCapability(
                name="deepseek-chat", provider="deepseek", context_window=32768,
                input_cost_per_1k=0.00014, output_cost_per_1k=0.00028,
                max_tokens_per_minute=200000, max_requests_per_minute=100,
                quality_score=0.85, speed_score=0.9,
                supports_function_calling=True  # 支持函数调用
            ),
            "deepseek:deepseek-reasoner": ModelCapability(
                name="deepseek-reasoner", provider="deepseek", context_window=32768,
                input_cost_per_1k=0.00014, output_cost_per_1k=0.00028,
                max_tokens_per_minute=200000, max_requests_per_minute=100,
                quality_score=0.95, speed_score=0.7,
                supports_function_calling=False  # 不支持函数调用（重要！）
            ),
            "deepseek:deepseek-coder": ModelCapability(
                name="deepseek-coder", provider="deepseek", context_window=16384,
                input_cost_per_1k=0.00014, output_cost_per_1k=0.00028,
                max_tokens_per_minute=200000, max_requests_per_minute=100,
                quality_score=0.9, speed_score=0.85,
                supports_function_calling=True  # 支持函数调用
            ),
            "kimi:moonshot-v1-8k": ModelCapability(
                name="moonshot-v1-8k", provider="kimi", context_window=8192,
                input_cost_per_1k=0.012, output_cost_per_1k=0.012,
                max_tokens_per_minute=120000, max_requests_per_minute=60,
                quality_score=0.9, speed_score=0.8,
                supports_function_calling=True,  # Kimi 支持函数调用
                supports_vision=False
            ),
            "kimi:moonshot-v1-32k": ModelCapability(
                name="moonshot-v1-32k", provider="kimi", context_window=32768,
                input_cost_per_1k=0.024, output_cost_per_1k=0.024,
                max_tokens_per_minute=80000, max_requests_per_minute=40,
                quality_score=0.95, speed_score=0.7,
                supports_function_calling=True,  # Kimi 支持函数调用
                supports_vision=False
            ),
            "doubao:doubao-seed-1-6-flash-250615": ModelCapability(
                name="doubao-seed-1-6-flash-250615", provider="doubao", context_window=32768,
                input_cost_per_1k=0.0003, output_cost_per_1k=0.0006,  # 估算价格
                max_tokens_per_minute=200000, max_requests_per_minute=100,
                quality_score=0.88, speed_score=0.95,  # 快速响应
                supports_function_calling=True,  # Doubao 支持函数调用
                supports_vision=False
            ),
            "doubao:doubao-1-5-vision-pro-250328": ModelCapability(
                name="doubao-1-5-vision-pro-250328", provider="doubao", context_window=32768,
                input_cost_per_1k=0.0005, output_cost_per_1k=0.001,  # 估算价格
                max_tokens_per_minute=150000, max_requests_per_minute=80,
                quality_score=0.92, speed_score=0.85,  # 视觉理解模型
                supports_function_calling=True,  # Doubao 支持函数调用
                supports_vision=True  # 视觉理解能力
            ),
            # ZhipuAI (智谱AI) 模型能力
            "zhipuai:glm-4.6": ModelCapability(
                name="glm-4.6", provider="zhipuai", context_window=200000,
                input_cost_per_1k=0.02, output_cost_per_1k=0.06,  # 估算价格
                max_tokens_per_minute=200000, max_requests_per_minute=100,
                quality_score=0.98, speed_score=0.85,  # 旗舰模型，最强性能
                supports_function_calling=True,  # GLM-4.6 支持函数调用
                supports_vision=False
            ),
            "zhipuai:glm-4.5": ModelCapability(
                name="glm-4.5", provider="zhipuai", context_window=128000,
                input_cost_per_1k=0.015, output_cost_per_1k=0.045,  # 估算价格
                max_tokens_per_minute=200000, max_requests_per_minute=100,
                quality_score=0.95, speed_score=0.88,  # 超强性能
                supports_function_calling=True,  # GLM-4.5 支持函数调用
                supports_vision=False
            ),
            "zhipuai:glm-4.5-air": ModelCapability(
                name="glm-4.5-air", provider="zhipuai", context_window=128000,
                input_cost_per_1k=0.008, output_cost_per_1k=0.024,  # 估算价格
                max_tokens_per_minute=200000, max_requests_per_minute=100,
                quality_score=0.92, speed_score=0.90,  # 高性价比
                supports_function_calling=True,  # GLM-4.5-Air 支持函数调用
                supports_vision=False
            ),
            "zhipuai:glm-4.5-flash": ModelCapability(
                name="glm-4.5-flash", provider="zhipuai", context_window=128000,
                input_cost_per_1k=0.0, output_cost_per_1k=0.0,  # 免费模型
                max_tokens_per_minute=200000, max_requests_per_minute=100,
                quality_score=0.88, speed_score=0.95,  # 免费快速响应
                supports_function_calling=True,  # GLM-4.5-Flash 支持函数调用
                supports_vision=False
            ),
            "zhipuai:glm-4.1v-thinking-flash": ModelCapability(
                name="glm-4.1v-thinking-flash", provider="zhipuai", context_window=64000,
                input_cost_per_1k=0.0, output_cost_per_1k=0.0,  # 免费视觉模型
                max_tokens_per_minute=150000, max_requests_per_minute=80,
                quality_score=0.90, speed_score=0.85,  # 免费视觉推理模型
                supports_function_calling=True,  # GLM-4.1V 支持函数调用
                supports_vision=True  # 视觉推理能力
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
        speed_requirement: float = 0.5,
        requires_function_calling: bool = False,
        requires_vision: bool = False
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
            requires_function_calling: 是否需要函数调用能力
            requires_vision: 是否需要视觉理解能力
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

                # 检查模型能力是否满足任务需求
                if requires_function_calling and not capability.supports_function_calling:
                    logger.debug(f"模型 {model_key} 不支持函数调用，跳过")
                    continue

                if requires_vision and not capability.supports_vision:
                    logger.debug(f"模型 {model_key} 不支持视觉理解，跳过")
                    continue

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
                            capability, estimated_cost, score, task_type,
                            requires_function_calling, requires_vision
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
        task_type: str,
        requires_function_calling: bool = False,
        requires_vision: bool = False
    ) -> str:
        """生成路由决策的推理说明"""
        capabilities = []
        if requires_function_calling and capability.supports_function_calling:
            capabilities.append("支持函数调用")
        elif requires_function_calling and not capability.supports_function_calling:
            capabilities.append("不支持函数调用（不匹配）")

        if requires_vision and capability.supports_vision:
            capabilities.append("支持视觉理解")
        elif requires_vision and not capability.supports_vision:
            capabilities.append("不支持视觉理解（不匹配）")

        capability_info = f", 能力: {', '.join(capabilities)}" if capabilities else ""

        return f"选择 {capability.provider}:{capability.name} 处理 {task_type} 任务。预估成本: ${estimated_cost:.4f}, 综合评分: {score:.2f}{capability_info}"

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
        speed_requirement: float = 0.5,
        requires_function_calling: bool = False,
        requires_vision: bool = False
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
            speed_requirement=speed_requirement,
            requires_function_calling=requires_function_calling,
            requires_vision=requires_vision
        )

        logger.info(f"路由决策: {decision.provider_name}:{decision.model_name}, 原因: {decision.reasoning}")

        # 检查是否存在能力不匹配的情况并发出警告
        if requires_function_calling:
            model_key = f"{decision.provider_name}:{decision.model_name}"
            capability = self.model_capabilities.get(model_key)
            if capability and not capability.supports_function_calling:
                logger.warning(
                    f"能力不匹配：任务需要函数调用，但选择的模型 {decision.model_name} 不支持函数调用。"
                    f"根据DeepSeek规则，请求将被自动降级到deepseek-chat模型处理。"
                )

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

    def detect_task_requirements(self, task_type: str, messages: List[LLMMessage] = None) -> Dict[str, bool]:
        """
        根据任务类型和消息内容检测任务需求 (基于 tech.txt 策略一：思维链提示)

        Returns:
            Dict包含:
            - requires_function_calling: 是否需要函数调用
            - requires_vision: 是否需要视觉理解
            - estimated_complexity: 预估任务复杂度
            - reasoning_depth: 推理深度要求
        """
        requirements = {
            "requires_function_calling": False,
            "requires_vision": False,
            "estimated_complexity": "medium",
            "reasoning_depth": "standard"
        }

        # 基于任务类型的默认需求 (增强版)
        function_calling_tasks = {"research", "analysis", "coding", "reasoning"}
        vision_tasks = {"vision", "image_analysis", "table_extraction"}
        complex_tasks = {"research", "analysis", "planning", "creative"}

        if task_type in function_calling_tasks:
            requirements["requires_function_calling"] = True

        if task_type in vision_tasks:
            requirements["requires_vision"] = True

        if task_type in complex_tasks:
            requirements["estimated_complexity"] = "high"
            requirements["reasoning_depth"] = "deep"

        # 基于消息内容的智能检测 (使用思维链分析)
        if messages:
            message_content = " ".join([m.content for m in messages]).lower()

            # 思维链分析步骤：
            # 1. 理解任务意图
            # 2. 识别关键需求
            # 3. 评估复杂程度
            # 4. 确定能力要求

            # 检测是否包含工具调用相关关键词
            tool_keywords = [
                "search", "查找", "分析", "calculate", "计算", "执行", "run",
                "function", "函数", "api", "工具", "tool", "调用", "搜索",
                "fetch", "获取", "数据库", "database", "外部", "external"
            ]
            if any(keyword in message_content for keyword in tool_keywords):
                requirements["requires_function_calling"] = True

            # 检测是否包含图像相关关键词
            vision_keywords = [
                "image", "图片", "图像", "视觉", "vision", "表格", "table",
                "chart", "图表", "screenshot", "截图", "photo", "照片",
                "ocr", "文字识别", "图片分析", "图像处理"
            ]
            if any(keyword in message_content for keyword in vision_keywords):
                requirements["requires_vision"] = True

            # 检测任务复杂度指标
            complexity_indicators = {
                "high": [
                    "研究", "分析", "设计", "开发", "创建", "综合", "深入",
                    "research", "analyze", "design", "develop", "comprehensive",
                    "multiple", "various", "complex", "detailed"
                ],
                "medium": [
                    "比较", "总结", "规划", "评估", "compare", "summarize",
                    "plan", "evaluate", "moderate"
                ]
            }

            high_complexity_count = sum(1 for indicator in complexity_indicators["high"] if indicator in message_content)
            medium_complexity_count = sum(1 for indicator in complexity_indicators["medium"] if indicator in message_content)

            if high_complexity_count > 0:
                requirements["estimated_complexity"] = "high"
                requirements["reasoning_depth"] = "deep"
            elif medium_complexity_count > 0:
                requirements["estimated_complexity"] = "medium"
                requirements["reasoning_depth"] = "standard"
            else:
                requirements["estimated_complexity"] = "low"
                requirements["reasoning_depth"] = "basic"

            # 检测推理深度要求
            reasoning_keywords = [
                "推理", "逻辑", "步骤", "详细", "explain", "reasoning",
                "logic", "steps", "detailed", "why", "how", "process"
            ]
            if any(keyword in message_content for keyword in reasoning_keywords):
                requirements["reasoning_depth"] = "deep"

        return requirements

    def create_enhanced_routing_prompt(
        self,
        task_type: str,
        task_description: str = "",
        requirements: Dict = None,
        available_providers: List[str] = None
    ) -> str:
        """
        创建增强的路由提示词 (基于 tech.txt 策略)

        Args:
            task_type: 任务类型
            task_description: 任务描述
            requirements: 任务需求
            available_providers: 可用提供商列表

        Returns:
            格式化的路由提示词
        """
        requirements = requirements or {}
        available_providers = available_providers or list(self.providers.keys())

        # 使用分隔符标示不同部分 (策略一)
        prompt_parts = [
            "# 智能路由决策提示",
            "",
            "## 任务分析",
            f"任务类型: {task_type}",
            f"任务描述: {task_description}",
            "",
            "## 需求分析 (基于 tech.txt 策略)",
            f"- 函数调用需求: {'是' if requirements.get('requires_function_calling', False) else '否'}",
            f"- 视觉理解需求: {'是' if requirements.get('requires_vision', False) else '否'}",
            f"- 预估复杂度: {requirements.get('estimated_complexity', 'medium')}",
            f"- 推理深度: {requirements.get('reasoning_depth', 'standard')}",
            "",
            "## 模型能力映射",
            "### 推荐模型选择策略:",
            "",
            "#### 1. 函数调用任务优先级:",
            "- DeepSeek Chat (高质量函数调用)",
            "- ZhipuAI GLM-4.6 (强大推理 + 函数调用)",
            "- ZhipuAI GLM-4.5-Air (高性价比函数调用)",
            "- Kimi (长上下文 + 函数调用)",
            "- Doubao (快速函数调用)",
            "- Ollama (本地函数调用)",
            "",
            "#### 2. 视觉理解任务优先级:",
            "- ZhipuAI GLM-4.1V-Thinking-Flash (免费视觉模型)",
            "- Doubao Vision Pro (专业视觉理解)",
            "- DeepSeek (基础视觉支持)",
            "",
            "#### 3. 复杂推理任务优先级:",
            "- ZhipuAI GLM-4.6 (旗舰推理模型)",
            "- DeepSeek Reasoner (专用推理模型，注意：不支持函数调用)",
            "- DeepSeek Chat (推理 + 函数调用平衡)",
            "",
            "#### 4. 成本效益优先级:",
            "- Ollama (本地免费)",
            "- ZhipuAI GLM-4.5-Flash (免费模型)",
            "- ZhipuAI GLM-4.1V-Thinking-Flash (免费视觉)",
            "- DeepSeek (低成本高性能)",
            "- ZhipuAI GLM-4.5-Air (高性价比)",
            "",
            "#### 5. 速度优先级:",
            "- Ollama (本地快速)",
            "- Doubao (云端快速)",
            "- ZhipuAI GLM-4.5-Flash (免费快速)",
            "- DeepSeek Chat (高速响应)",
            "",
            "## 决策逻辑 (思维链推理)",
            "请按照以下步骤进行路由决策:",
            "",
            "步骤1: [理解需求] - 分析任务的核心需求和约束条件",
            "步骤2: [能力匹配] - 根据需求筛选具备相应能力的模型",
            "步骤3: [质量评估] - 评估模型质量是否满足任务要求",
            "步骤4: [成本考量] - 检查预估成本是否在预算范围内",
            "步骤5: [性能权衡] - 在质量、成本、速度之间找到最佳平衡",
            "步骤6: [最终决策] - 选择最适合的模型并说明决策理由",
            "",
            "## 输出格式",
            "请以JSON格式返回路由决策:",
            '{',
            '  "selected_provider": "提供商名称",',
            '  "selected_model": "模型名称",',
            '  "reasoning": "详细的推理过程，包含上述6个步骤",',
            '  "confidence_score": 0.9,',
            '  "estimated_cost": 0.001,',
            '  "fallback_options": ["备选提供商1", "备选提供商2"],',
            '  "special_considerations": "特殊考虑事项"',
            '}',
            "",
            "## 重要约束条件",
            "1. DeepSeek Reasoner 不支持函数调用，如需函数调用请选择 DeepSeek Chat",
            "2. 视觉任务必须选择支持视觉理解的模型",
            "3. 复杂推理任务优先选择 GLM-4.6 或 DeepSeek Reasoner",
            "4. 简单任务可优先考虑成本效益",
            "5. 函数调用 + 视觉需求需要寻找同时支持两种能力的模型",
            "",
            f"## 当前可用提供商",
            ", ".join(available_providers),
            "",
            "---",
            "",
            "请基于以上信息，为当前任务做出最优的路由决策。"
        ]

        return "\n".join(prompt_parts)

    def analyze_task_for_routing(
        self,
        task_type: str,
        messages: List[LLMMessage] = None,
        task_description: str = ""
    ) -> Dict[str, Any]:
        """
        深度分析任务用于路由决策 (基于 tech.txt 策略一：思维链推理)
        """
        # 检测任务需求
        requirements = self.detect_task_requirements(task_type, messages)

        # 分析消息内容以获取更多信息
        content_analysis = {
            "message_count": len(messages) if messages else 0,
            "total_length": sum(len(m.content) for m in messages) if messages else 0,
            "has_code_blocks": False,
            "has_references": False,
            "has_questions": False,
            "urgency_level": "normal"
        }

        if messages:
            message_content = " ".join([m.content for m in messages])

            # 检测代码块
            if "```" in message_content or "def " in message_content or "function" in message_content:
                content_analysis["has_code_blocks"] = True
                requirements["requires_function_calling"] = True

            # 检测引用和参考资料
            if any(ref in message_content.lower() for ref in ["引用", "参考", "reference", "cite", "source"]):
                content_analysis["has_references"] = True

            # 检测问题
            if any(q in message_content for q in ["？", "?", "如何", "怎样", "how", "what"]):
                content_analysis["has_questions"] = True

            # 检测紧急性
            urgent_keywords = ["urgent", "紧急", "立即", "马上", "asap", "immediately"]
            if any(keyword in message_content.lower() for keyword in urgent_keywords):
                content_analysis["urgency_level"] = "high"
                requirements["reasoning_depth"] = "quick"

        # 生成路由提示
        routing_prompt = self.create_enhanced_routing_prompt(
            task_type=task_type,
            task_description=task_description,
            requirements=requirements,
            available_providers=list(self.providers.keys())
        )

        return {
            "requirements": requirements,
            "content_analysis": content_analysis,
            "routing_prompt": routing_prompt,
            "task_complexity_score": self._calculate_complexity_score(requirements, content_analysis)
        }

    def _calculate_complexity_score(self, requirements: Dict, content_analysis: Dict) -> float:
        """计算任务复杂度分数 (0-1)"""
        score = 0.5  # 基础分数

        # 需求复杂度因素
        if requirements.get("requires_function_calling", False):
            score += 0.15
        if requirements.get("requires_vision", False):
            score += 0.2
        if requirements.get("estimated_complexity") == "high":
            score += 0.2
        elif requirements.get("estimated_complexity") == "medium":
            score += 0.1

        # 内容复杂度因素
        if content_analysis.get("has_code_blocks", False):
            score += 0.1
        if content_analysis.get("has_references", False):
            score += 0.1
        if content_analysis.get("has_questions", False):
            score += 0.05

        # 长度复杂度
        if content_analysis.get("total_length", 0) > 2000:
            score += 0.1
        elif content_analysis.get("total_length", 0) > 1000:
            score += 0.05

        return min(score, 1.0)

    async def route_and_chat_auto(
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
        增强智能路由并执行聊天请求（基于 tech.txt 策略：思维链推理）

        这个方法会使用思维链推理深度分析任务需求，然后选择最适合的模型。

        返回格式:
        {
            "content": "响应内容",
            "model": "使用的模型",
            "provider": "使用的提供商",
            "routing_decision": RoutingDecision对象,
            "task_analysis": 任务分析结果,
            "routing_prompt": 使用的路由提示词,
            "actual_cost": 实际成本,
            "tokens_used": 使用的token数,
            "processing_time": 处理时间
        }
        """
        # 深度分析任务需求 (基于 tech.txt 策略一：思维链推理)
        task_analysis = self.analyze_task_for_routing(
            task_type=task_type,
            messages=messages,
            task_description=messages[0].content if messages else ""
        )

        requirements = task_analysis["requirements"]
        content_analysis = task_analysis["content_analysis"]
        routing_prompt = task_analysis["routing_prompt"]
        complexity_score = task_analysis["task_complexity_score"]

        logger.info(f"增强任务分析完成:")
        logger.info(f"  函数调用需求: {requirements['requires_function_calling']}")
        logger.info(f"  视觉理解需求: {requirements['requires_vision']}")
        logger.info(f"  预估复杂度: {requirements['estimated_complexity']}")
        logger.info(f"  推理深度: {requirements['reasoning_depth']}")
        logger.info(f"  复杂度分数: {complexity_score:.2f}")
        logger.info(f"  内容分析: 消息数={content_analysis['message_count']}, "
                   f"总长度={content_analysis['total_length']}, "
                   f"包含代码块={content_analysis['has_code_blocks']}, "
                   f"包含引用={content_analysis['has_references']}")

        # 根据分析结果调整参数
        if requirements["estimated_complexity"] == "high":
            quality_requirement = max(quality_requirement, 0.8)
            if requirements["reasoning_depth"] == "deep":
                estimated_output_tokens = max(estimated_output_tokens, 2000)
        elif requirements["estimated_complexity"] == "low":
            speed_requirement = max(speed_requirement, 0.7)
            if requirements["reasoning_depth"] == "quick":
                estimated_output_tokens = min(estimated_output_tokens, 500)

        # 调用标准路由方法
        result = await self.route_and_chat(
            task_type=task_type,
            messages=messages,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            temperature=temperature,
            max_tokens=max_tokens,
            quality_requirement=quality_requirement,
            cost_budget=cost_budget,
            speed_requirement=speed_requirement,
            requires_function_calling=requirements["requires_function_calling"],
            requires_vision=requirements["requires_vision"]
        )

        # 添加分析结果到返回值
        result.update({
            "task_analysis": task_analysis,
            "routing_prompt": routing_prompt,
            "complexity_score": complexity_score
        })

        return result

    async def route_with_llm_assistance(
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
        使用 LLM 辅助的智能路由决策 (基于 tech.txt 策略二：提供参考资料)

        当路由决策复杂时，使用 LLM 进行智能分析并做出路由决策。
        """
        # 首先进行基础任务分析
        task_analysis = self.analyze_task_for_routing(
            task_type=task_type,
            messages=messages,
            task_description=messages[0].content if messages else ""
        )

        # 如果复杂度分数较低，使用传统路由
        if task_analysis["task_complexity_score"] < 0.7:
            return await self.route_and_chat_auto(
                task_type=task_type,
                messages=messages,
                estimated_input_tokens=estimated_input_tokens,
                estimated_output_tokens=estimated_output_tokens,
                temperature=temperature,
                max_tokens=max_tokens,
                quality_requirement=quality_requirement,
                cost_budget=cost_budget,
                speed_requirement=speed_requirement
            )

        # 对于复杂任务，使用 LLM 进行路由决策
        logger.info("任务复杂度高，使用 LLM 辅助路由决策")

        try:
            # 使用轻量级模型进行路由决策
            routing_messages = [
                {"role": "system", "content": "你是一个专业的路由决策专家，擅长分析任务需求并选择最适合的 AI 模型。"},
                {"role": "user", "content": task_analysis["routing_prompt"]}
            ]

            # 选择一个轻量级模型用于路由决策
            routing_decision = await self.route_and_chat(
                task_type="triage",
                messages=routing_messages,
                estimated_input_tokens=len(task_analysis["routing_prompt"]),
                estimated_output_tokens=500,
                temperature=0.1,  # 低温度确保决策稳定
                max_tokens=500,
                quality_requirement=0.6,  # 路由决策不需要最高质量
                cost_budget=0.01,  # 控制路由决策成本
                speed_requirement=0.8  # 路由决策需要快速
            )

            # 解析 LLM 的路由决策
            try:
                import json
                decision_data = json.loads(routing_decision["content"])

                # 验证决策的合理性
                selected_provider = decision_data.get("selected_provider")
                selected_model = decision_data.get("selected_model")

                if selected_provider in self.providers:
                    # 使用 LLM 的决策执行请求
                    final_result = await self.route_and_chat(
                        task_type=task_type,
                        messages=messages,
                        estimated_input_tokens=estimated_input_tokens,
                        estimated_output_tokens=estimated_output_tokens,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        quality_requirement=quality_requirement,
                        cost_budget=cost_budget,
                        speed_requirement=speed_requirement,
                        requires_function_calling=task_analysis["requirements"]["requires_function_calling"],
                        requires_vision=task_analysis["requirements"]["requires_vision"]
                    )

                    # 添加 LLM 路由决策信息
                    final_result.update({
                        "llm_routing_decision": decision_data,
                        "routing_method": "llm_assisted"
                    })

                    return final_result
                else:
                    logger.warning(f"LLM 选择了不可用的提供商: {selected_provider}")

            except json.JSONDecodeError:
                logger.error("无法解析 LLM 路由决策，回退到传统路由")

        except Exception as e:
            logger.error(f"LLM 辅助路由失败: {e}")

        # 回退到传统自动路由
        logger.info("回退到传统自动路由")
        fallback_result = await self.route_and_chat_auto(
            task_type=task_type,
            messages=messages,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            temperature=temperature,
            max_tokens=max_tokens,
            quality_requirement=quality_requirement,
            cost_budget=cost_budget,
            speed_requirement=speed_requirement
        )

        fallback_result.update({
            "routing_method": "traditional_fallback",
            "routing_error": str(e) if 'e' in locals() else "LLM routing failed"
        })

        return fallback_result

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

    async def chat(self, task: str, size: str, messages: List[LLMMessage], temperature: float = 0.7, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        兼容性聊天接口，映射到route_and_chat方法

        Args:
            task: 任务类型
            size: 模型大小 ('small', 'medium', 'large')
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            聊天响应结果
        """
        # 根据size调整token估计
        size_to_tokens = {
            "small": (500, 1000),
            "medium": (1000, 2000),
            "large": (2000, 4000)
        }

        input_tokens, output_tokens = size_to_tokens.get(size, size_to_tokens["medium"])

        # 根据task类型调整质量要求
        task_quality_requirements = {
            "triage": 0.5,
            "simple_chat": 0.6,
            "code": 0.8,
            "reasoning": 0.9,
            "research": 0.85,
            "creative": 0.8,
            "general": 0.7
        }

        quality_requirement = task_quality_requirements.get(task, 0.7)

        # 调用智能路由
        return await self.route_and_chat(
            task_type=task,
            messages=messages,
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens,
            temperature=temperature,
            max_tokens=max_tokens,
            quality_requirement=quality_requirement,
            cost_budget=None,  # 使用默认预算
            speed_requirement=0.5
        )

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


