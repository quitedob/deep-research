#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgentScope研究配置管理
管理研究功能的各种配置选项
"""

import os
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class ResearchType(str, Enum):
    """研究类型枚举"""
    COMPREHENSIVE = "comprehensive"
    ACADEMIC = "academic"
    NEWS = "news"
    ANALYSIS = "analysis"
    COMPARISON = "comparison"


class LLMProvider(str, Enum):
    """LLM提供商枚举"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class SourceType(str, Enum):
    """信息源类型枚举"""
    WEB = "web"
    WIKIPEDIA = "wikipedia"
    ARXIV = "arxiv"
    IMAGE = "image"
    LOCAL = "local"


class LLMConfig(BaseModel):
    """LLM配置模型"""
    provider: LLMProvider = LLMProvider.DEEPSEEK
    model_name: str = Field(..., description="模型名称")
    api_key: Optional[str] = Field(None, description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    max_tokens: int = Field(default=4096, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    stream: bool = Field(default=True)
    timeout: int = Field(default=120, ge=30, le=600)

    class Config:
        extra = "allow"


class MultimodalLLMConfig(BaseModel):
    """多模态LLM配置模型"""
    provider: LLMProvider = LLMProvider.OLLAMA
    model_name: str = Field(default="gemma3:4b", description="多模态模型名称")
    host: str = Field(default="http://localhost:11434", description="Ollama服务地址")
    timeout: int = Field(default=300, ge=60, le=600)
    max_image_size: int = Field(default=5242880, ge=1048576)  # 5MB
    supported_formats: List[str] = Field(
        default=["jpg", "jpeg", "png", "gif", "bmp", "webp"],
        description="支持的图像格式"
    )

    class Config:
        extra = "allow"


class ToolConfig(BaseModel):
    """工具配置模型"""
    name: str
    enabled: bool = Field(default=True)
    timeout: int = Field(default=60, ge=10, le=300)
    max_retries: int = Field(default=3, ge=1, le=5)
    custom_params: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"


class ResearchConfig(BaseModel):
    """研究配置模型"""
    research_type: ResearchType = ResearchType.COMPREHENSIVE
    max_iterations: int = Field(default=10, ge=1, le=50)
    parallel_tool_calls: bool = Field(default=True)
    enable_long_term_memory: bool = Field(default=True)
    auto_save_progress: bool = Field(default=True)
    enable_interruption: bool = Field(default=True)
    export_formats: List[str] = Field(
        default=["markdown", "json", "pdf"],
        description="支持的导出格式"
    )
    session_timeout: int = Field(default=3600, ge=300, le=86400)  # 1小时默认
    max_sources: int = Field(default=20, ge=5, le=100)
    relevance_threshold: float = Field(default=0.5, ge=0.0, le=1.0)

    class Config:
        extra = "allow"


class MemoryConfig(BaseModel):
    """记忆配置模型"""
    short_term_memory_size: int = Field(default=100, ge=50, le=500)
    long_term_memory_enabled: bool = Field(default=True)
    memory_cleanup_interval: int = Field(default=3600, ge=1800, le=7200)  # 1小时
    max_memory_age_days: int = Field(default=30, ge=7, le=365)
    compression_enabled: bool = Field(default=True)
    compression_ratio: float = Field(default=0.7, ge=0.3, le=1.0)

    class Config:
        extra = "allow"


class SecurityConfig(BaseModel):
    """安全配置模型"""
    max_session_per_user: int = Field(default=10, ge=1, le=100)
    rate_limit_requests: int = Field(default=100, ge=10, le=1000)
    rate_limit_window: int = Field(default=60, ge=30, le=300)  # 秒
    enable_content_filtering: bool = Field(default=True)
    blocked_domains: List[str] = Field(default_factory=list)
    allowed_file_types: List[str] = Field(
        default=["jpg", "jpeg", "png", "gif", "pdf", "txt", "md"],
        description="允许上传的文件类型"
    )
    max_file_size: int = Field(default=10485760, ge=1048576)  # 10MB

    class Config:
        extra = "allow"


class ExportConfig(BaseModel):
    """导出配置模型"""
    default_format: str = Field(default="markdown")
    max_export_size: int = Field(default=52428800, ge=1048576)  # 50MB
    export_expiry_days: int = Field(default=7, ge=1, le=30)
    include_metadata: bool = Field(default=True)
    template_dir: Optional[str] = Field(None, description="模板目录")
    custom_watermark: Optional[str] = Field(None, description="自定义水印")

    class Config:
        extra = "allow"


class MonitoringConfig(BaseModel):
    """监控配置模型"""
    enable_metrics: bool = Field(default=True)
    metrics_retention_days: int = Field(default=30, ge=7, le=365)
    enable_logging: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    enable_performance_tracking: bool = Field(default=True)
    alert_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "error_rate": 0.05,  # 5%错误率阈值
            "response_time": 30.0,  # 30秒响应时间阈值
            "memory_usage": 0.8  # 80%内存使用阈值
        }
    )

    class Config:
        extra = "allow"


class AgentScopeConfig(BaseModel):
    """AgentScope研究功能总配置"""
    llm: LLMConfig
    multimodal_llm: MultimodalLLMConfig
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    # 工具配置
    tools: Dict[str, ToolConfig] = Field(default_factory=dict)

    # 环境配置
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    class Config:
        extra = "allow"


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file or os.getenv("AGENTSCOPE_CONFIG_FILE", "agentscope_config.json")
        self._config: Optional[AgentScopeConfig] = None

    def load_config(self) -> AgentScopeConfig:
        """
        加载配置

        Returns:
            配置对象
        """
        if self._config:
            return self._config

        # 尝试从文件加载
        if os.path.exists(self.config_file):
            self._config = self._load_from_file()
        else:
            # 使用默认配置
            self._config = self._create_default_config()
            # 保存默认配置到文件
            self.save_config()

        # 应用环境变量覆盖
        self._apply_env_overrides()

        return self._config

    def save_config(self) -> None:
        """
        保存配置到文件
        """
        if not self._config:
            raise ValueError("没有配置可保存")

        import json
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self._config.dict(), f, indent=2, ensure_ascii=False)

    def _load_from_file(self) -> AgentScopeConfig:
        """
        从文件加载配置

        Returns:
            配置对象
        """
        import json
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        return AgentScopeConfig(**config_data)

    def _create_default_config(self) -> AgentScopeConfig:
        """
        创建默认配置

        Returns:
            默认配置对象
        """
        return AgentScopeConfig(
            llm=LLMConfig(
                provider=LLMProvider.DEEPSEEK,
                model_name="deepseek-chat",
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com"
            ),
            multimodal_llm=MultimodalLLMConfig(
                provider=LLMProvider.OLLAMA,
                model_name="gemma3:4b",
                host="http://localhost:11434"
            )
        )

    def _apply_env_overrides(self) -> None:
        """
        应用环境变量覆盖
        """
        if not self._config:
            return

        # LLM配置覆盖
        if os.getenv("DEEPSEEK_API_KEY"):
            self._config.llm.api_key = os.getenv("DEEPSEEK_API_KEY")
        if os.getenv("DEEPSEEK_BASE_URL"):
            self._config.llm.base_url = os.getenv("DEEPSEEK_BASE_URL")
        if os.getenv("BIGMODEL_API_KEY"):
            # 设置网络搜索API密钥
            self._config.tools["web_search"] = ToolConfig(
                name="web_search",
                enabled=True,
                custom_params={"api_key": os.getenv("BIGMODEL_API_KEY")}
            )

        # Ollama配置覆盖
        if os.getenv("OLLAMA_HOST"):
            self._config.multimodal_llm.host = os.getenv("OLLAMA_HOST")
        if os.getenv("OLLAMA_MODEL"):
            self._config.multimodal_llm.model_name = os.getenv("OLLAMA_MODEL")

        # 研究配置覆盖
        if os.getenv("RESEARCH_MAX_ITERATIONS"):
            self._config.research.max_iterations = int(os.getenv("RESEARCH_MAX_ITERATIONS"))
        if os.getenv("RESEARCH_SESSION_TIMEOUT"):
            self._config.research.session_timeout = int(os.getenv("RESEARCH_SESSION_TIMEOUT"))

    def get_tool_config(self, tool_name: str) -> Optional[ToolConfig]:
        """
        获取工具配置

        Args:
            tool_name: 工具名称

        Returns:
            工具配置
        """
        config = self.load_config()
        return config.tools.get(tool_name)

    def update_tool_config(self, tool_name: str, tool_config: ToolConfig) -> None:
        """
        更新工具配置

        Args:
            tool_name: 工具名称
            tool_config: 工具配置
        """
        config = self.load_config()
        config.tools[tool_name] = tool_config
        self.save_config()

    def validate_config(self) -> List[str]:
        """
        验证配置

        Returns:
            错误消息列表，空列表表示验证通过
        """
        errors = []

        if not self._config:
            return ["配置未加载"]

        # 验证必需的API密钥
        if self._config.llm.provider == LLMProvider.DEEPSEEK:
            if not self._config.llm.api_key:
                errors.append("DeepSeek API密钥未配置")

        # 验证多模态配置
        if self._config.multimodal_llm.provider == LLMProvider.OLLAMA:
            if not self._config.multimodal_llm.host:
                errors.append("Ollama服务地址未配置")

        # 验证研究配置
        if self._config.research.max_iterations < 1:
            errors.append("最大迭代次数必须大于0")

        # 验证安全配置
        if self._config.security.max_session_per_user < 1:
            errors.append("最大会话数必须大于0")

        return errors

    def get_llm_config(self, provider: Optional[LLMProvider] = None) -> LLMConfig:
        """
        获取LLM配置

        Args:
            provider: 指定的提供商

        Returns:
            LLM配置
        """
        config = self.load_config()
        if provider and config.llm.provider == provider:
            return config.llm
        return config.llm

    def get_multimodal_llm_config(self) -> MultimodalLLMConfig:
        """
        获取多模态LLM配置

        Returns:
            多模态LLM配置
        """
        config = self.load_config()
        return config.multimodal_llm


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config() -> AgentScopeConfig:
    """
    获取全局配置

    Returns:
        配置对象
    """
    return config_manager.load_config()


def reload_config() -> AgentScopeConfig:
    """
    重新加载配置

    Returns:
        新的配置对象
    """
    global config_manager
    config_manager = ConfigManager()
    return config_manager.load_config()