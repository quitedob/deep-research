# -*- coding: utf-8 -*-
"""
PPT模块配置管理

从conf.yaml读取配置，管理provider优先级、超时、重试策略等。
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class PPTConfig:
    """PPT模块配置类"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化配置

        参数:
            config_path: 配置文件路径，默认为项目根目录的conf.yaml
        """
        if config_path is None:
            # 默认配置文件路径
            config_path = Path(__file__).parent.parent.parent.parent / "conf.yaml"

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if not self.config_path.exists():
                logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                return self._get_default_config()

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"成功加载配置文件: {self.config_path}")
                return config

        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}，使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "PRIMARY_LLM_BACKEND": "OLLAMA",
            "FALLBACK_LLM_BACKEND": "DEEPSEEK",
            "OLLAMA_BASE_URL": "http://localhost:11434/v1",
            "OLLAMA_SMALL_MODEL": "gemma3:4b",
            "OLLAMA_LARGE_MODEL": "qwen3:32b",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1",
            "DEEPSEEK_MODELS": {
                "chat": "deepseek-chat",
                "reasoner": "deepseek-reasoner"
            },
            "PROVIDER_PRIORITY": {
                "ppt_outline": ["deepseek", "ollama"],
                "ppt_content": ["deepseek", "ollama"],
                "ppt_simple": ["ollama", "deepseek"]
            },
            "WORKFLOWS": {
                "ppt": {
                    "default_template": "modern",
                    "max_slides": 20,
                    "enable_charts": True
                }
            },
            "MAX_CONCURRENT_REQUESTS": 10,
            "REQUEST_TIMEOUT": 300,
            "ENABLE_CACHING": True,
            "CACHE_TTL": 1800
        }

    def get_provider_priority(self, task_type: str = "ppt_content") -> List[str]:
        """
        获取指定任务类型的provider优先级

        参数:
            task_type: 任务类型，如ppt_outline, ppt_content等

        返回:
            provider名称列表，按优先级排序
        """
        priority = self.config.get("PROVIDER_PRIORITY", {})
        return priority.get(task_type, ["deepseek", "ollama"])

    def get_deepseek_config(self) -> Dict[str, Any]:
        """获取DeepSeek配置"""
        return {
            "base_url": os.getenv("DEEPSEEK_BASE_URL", self.config.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")),
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "models": self.config.get("DEEPSEEK_MODELS", {
                "chat": "deepseek-chat",
                "reasoner": "deepseek-reasoner"
            }),
            "temperature_map": self.config.get("DEEPSEEK_TEMPERATURE_MAP", {
                "code": 0.0,
                "analysis": 1.0,
                "chat": 1.3,
                "creative": 1.5
            })
        }

    def get_ollama_config(self) -> Dict[str, Any]:
        """获取Ollama配置"""
        return {
            "base_url": os.getenv("OLLAMA_HOST", self.config.get("OLLAMA_BASE_URL", "http://localhost:11434")),
            "small_model": self.config.get("OLLAMA_SMALL_MODEL", "gemma3:4b"),
            "large_model": self.config.get("OLLAMA_LARGE_MODEL", "qwen3:32b"),
            "timeout": self.config.get("OLLAMA_CONNECTION_TIMEOUT", 30.0),
            "retry_attempts": self.config.get("OLLAMA_RETRY_ATTEMPTS", 3)
        }

    def get_ppt_workflow_config(self) -> Dict[str, Any]:
        """获取PPT工作流配置"""
        workflows = self.config.get("WORKFLOWS", {})
        ppt_config = workflows.get("ppt", {})

        return {
            "default_template": ppt_config.get("default_template", "modern"),
            "max_slides": ppt_config.get("max_slides", 20),
            "enable_charts": ppt_config.get("enable_charts", True),
            "default_language": "Chinese",
            "default_tone": "professional"
        }

    def get_timeout_config(self) -> Dict[str, int]:
        """获取超时配置"""
        return {
            "request_timeout": self.config.get("REQUEST_TIMEOUT", 300),
            "health_check_timeout": self.config.get("HEALTH_CHECK_TIMEOUT", 10),
            "cache_ttl": self.config.get("CACHE_TTL", 1800)
        }

    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能配置"""
        return {
            "max_concurrent_requests": self.config.get("MAX_CONCURRENT_REQUESTS", 10),
            "enable_caching": self.config.get("ENABLE_CACHING", True),
            "cache_ttl": self.config.get("CACHE_TTL", 1800)
        }

    def is_provider_enabled(self, provider_name: str) -> bool:
        """
        检查provider是否启用

        参数:
            provider_name: provider名称

        返回:
            是否启用
        """
        if provider_name == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY", "")
            return bool(api_key)
        elif provider_name == "ollama":
            # Ollama本地服务，默认启用
            return True
        else:
            # 其他provider根据配置判断
            return True

    def get_cost_limits(self) -> Dict[str, float]:
        """
        获取成本限制配置

        返回:
            成本限制字典
        """
        return {
            "max_cost_per_request": 1.0,  # 单次请求最大成本（人民币）
            "daily_budget": 100.0,         # 每日预算
            "enable_cost_tracking": True   # 是否启用成本追踪
        }


# 全局配置实例
_ppt_config: Optional[PPTConfig] = None


def get_ppt_config() -> PPTConfig:
    """获取PPT配置实例（单例模式）"""
    global _ppt_config
    if _ppt_config is None:
        _ppt_config = PPTConfig()
    return _ppt_config


