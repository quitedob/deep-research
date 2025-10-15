# -*- coding: utf-8 -*-
"""
统一配置管理系统
使用 Pydantic 提供类型安全的配置加载，消除配置冲突和冗余
优先级: 环境变量 > .env 文件 > conf.yaml > 默认值
"""

import os
import yaml
import logging
import secrets
from pathlib import Path
from typing import Any, Dict, Optional, Type, Union, List, get_type_hints
from pydantic import BaseModel, Field, validator, root_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import re

logger = logging.getLogger(__name__)


class DatabaseConfig(BaseModel):
    """数据库配置"""
    url: str = Field(
        default="postgresql+asyncpg://deerflow:deerflow123@localhost:5432/deerflow",
        description="数据库连接URL"
    )
    echo: bool = Field(default=False, description="SQLAlchemy echo模式")
    pool_size: int = Field(default=5, description="连接池大小")
    max_overflow: int = Field(default=10, description="最大溢出连接数")
    auto_create_tables: bool = Field(default=True, description="自动创建表")

class RedisConfig(BaseModel):
    """Redis配置"""
    url: str = Field(default="redis://localhost:6379", description="Redis连接URL")
    max_connections: int = Field(default=10, description="最大连接数")
    retry_on_timeout: bool = Field(default=True, description="超时重试")
    socket_timeout: float = Field(default=5.0, description="Socket超时")
    socket_connect_timeout: float = Field(default=5.0, description="连接超时")

class SecurityConfig(BaseModel):
    """安全配置"""
    secret_key: str = Field(
        default="your_super_secret_jwt_key_here_make_it_long_and_random",
        description="统一的安全密钥（用于JWT和会话签名）"
    )
    algorithm: str = Field(default="HS256", description="JWT算法")
    access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间（分钟）")

    @validator('secret_key')
    def validate_secret_key(cls, v):
        """验证密钥强度"""
        # 检查弱默认密钥
        weak_keys = [
            "your-secret-key-change-in-production",
            "your-jwt-secret-change-in-production",
            "your_super_secret_jwt_key_here_make_it_long_and_random",
            "secret", "password", "key", "test", "dev", "development"
        ]

        if v.lower() in weak_keys:
            raise ValueError(
                f"检测到弱密钥 '{v}'。请设置强密钥环境变量 DEEP_RESEARCH_SECURITY_SECRET_KEY "
                f"或使用命令生成: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )

        # 检查长度
        if len(v) < 32:
            raise ValueError("密钥长度必须至少32个字符以确保安全性")

        return v

class CORSConfig(BaseModel):
    """CORS配置"""
    allow_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="允许的源"
    )
    allow_credentials: bool = Field(default=True, description="允许凭证")
    allow_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="允许的方法"
    )
    allow_headers: List[str] = Field(
        default=[
            "Authorization", "Content-Type", "X-Requested-With", "Accept",
            "Accept-Encoding", "Accept-Language", "Cache-Control",
            "Connection", "Host", "User-Agent", "X-Request-ID"
        ],
        description="允许的头部"
    )
    max_age: int = Field(default=86400, description="预检缓存时间（秒）")

class LLMProviderConfig(BaseModel):
    """LLM提供商配置"""
    api_key: Optional[str] = Field(default=None, description="API密钥")
    base_url: str = Field(description="API基础URL")
    model: str = Field(description="模型名称")
    timeout: int = Field(default=30, description="超时时间（秒）")
    max_tokens: int = Field(default=4000, description="最大token数")
    temperature: float = Field(default=0.7, description="温度参数")

    @validator('api_key')
    def validate_api_key(cls, v, values):
        if v is None and values.get('model'):
            logger.warning(f"未设置{values.get('model')}的API密钥")
        return v

class OllamaConfig(LLMProviderConfig):
    """Ollama配置"""
    small_model: str = Field(default="gemma3:4b", description="小型模型")
    large_model: str = Field(default="qwen3:32b", description="大型模型")
    vision_model: str = Field(default="qwen2.5vl:7b", description="视觉模型")
    base_url: str = Field(default="http://localhost:11434", description="Ollama基础URL")
    connection_timeout: float = Field(default=30.0, description="连接超时")
    read_timeout: float = Field(default=120.0, description="读取超时")
    retry_attempts: int = Field(default=3, description="重试次数")

class DeepSeekConfig(LLMProviderConfig):
    """DeepSeek配置"""
    base_url: str = Field(default="https://api.deepseek.com/v1", description="DeepSeek API基础URL")
    models: Dict[str, str] = Field(
        default_factory=lambda: {"chat": "deepseek-chat", "reasoner": "deepseek-reasoner"},
        description="模型映射"
    )
    temperature_map: Dict[str, float] = Field(
        default_factory=lambda: {
            "code": 0.0, "math": 0.0, "analysis": 1.0, "chat": 1.3,
            "translation": 1.3, "creative": 1.5, "poetry": 1.5
        },
        description="温度映射"
    )
    enable_off_peak_optimization: bool = Field(default=True, description="启用错峰优化")

class DoubaoConfig(LLMProviderConfig):
    """Doubao配置"""
    base_url: str = Field(default="https://ark.cn-beijing.volces.com/api/v3", description="豆包API基础URL")
    model: str = Field(default="doubao-seed-1-6-flash-250615", description="豆包模型")
    vision_model: str = Field(default="doubao-1-5-vision-pro-250328", description="视觉模型")

class KimiConfig(LLMProviderConfig):
    """Kimi配置"""
    base_url: str = Field(default="https://api.moonshot.cn/v1", description="Kimi API基础URL")
    model: str = Field(default="moonshot-v1-8k", description="Kimi模型")
    long_context_model: str = Field(default="moonshot-v1-128k", description="长上下文模型")

class ZhipuAIConfig(LLMProviderConfig):
    """ZhipuAI配置"""
    base_url: str = Field(default="https://open.bigmodel.cn/api/paas/v4", description="智谱AI API基础URL")
    models: Dict[str, str] = Field(
        default_factory=lambda: {
            "chat": "glm-4.5-air",
            "reasoning": "glm-4.6",
            "vision": "glm-4.1v-thinking-flash",
            "search": "glm-4.5-flash",
            "free": "glm-4.5-flash",
            "premium": "glm-4.6",
            "cost_effective": "glm-4.5-air"
        },
        description="模型映射"
    )
    search_engines: Dict[str, str] = Field(
        default_factory=lambda: {
            "search_std": "基础版（智谱AI自研）",
            "search_pro": "高级版（智谱AI自研）",
            "search_pro_sogou": "搜狗",
            "search_pro_quark": "夸克"
        },
        description="搜索引擎配置"
    )
    default_search_engine: str = Field(default="search_pro", description="默认搜索引擎")
    max_search_results: int = Field(default=10, description="最大搜索结果数")
    enable_vision: bool = Field(default=True, description="启用视觉功能")

class LLMRoutingConfig(BaseModel):
    """LLM路由配置"""
    provider_priority: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "triage": ["ollama", "deepseek"],
            "simple_chat": ["ollama", "deepseek"],
            "code": ["deepseek", "ollama"],
            "reasoning": ["deepseek", "ollama"],
            "research": ["deepseek", "ollama"],
            "creative": ["deepseek", "ollama"],
            "general": ["ollama", "deepseek"]
        },
        description="提供商优先级"
    )
    triage_confidence_threshold: float = Field(
        default=0.7, description="路由置信度阈值"
    )
    routing: Dict[str, Any] = Field(
        default_factory=lambda: {
            "cost_budget_per_request": 0.1,
            "quality_threshold": 0.7,
            "speed_priority": 0.3,
            "cost_priority": 0.4,
            "quality_priority": 0.3,
            "enable_fallback": True,
            "rate_limit_buffer": 0.8
        },
        description="路由配置"
    )

class AppSettings(BaseSettings):
    """应用主配置类"""
    # 基础配置
    app_name: str = Field(default="Deep Research Platform", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    environment: str = Field(default="development", description="运行环境")
    debug: bool = Field(default=True, description="调试模式")
    host: str = Field(default="0.0.0.0", description="监听主机")
    port: int = Field(default=8000, description="监听端口")
    enable_reload: bool = Field(default=True, description="启用热重载")

    # 文件上传配置
    max_file_size: int = Field(default=10485760, description="最大文件大小（字节）")
    allowed_file_types: str = Field(
        default=".docx,.doc,.txt,.md,.pdf,.ppt,.pptx",
        description="允许的文件类型"
    )
    upload_dir: str = Field(default="./uploads", description="上传目录")
    temp_dir: str = Field(default="./temp", description="临时目录")

    # 数据库配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    # Redis配置
    redis: RedisConfig = Field(default_factory=RedisConfig)

    # 安全配置
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    # CORS配置
    cors: CORSConfig = Field(default_factory=CORSConfig)

    # LLM配置
    primary_llm_backend: str = Field(default="DOUBAO", description="主要LLM后端")
    default_search_provider: str = Field(default="doubao", description="默认搜索提供商")

    # Ollama配置
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)

    # DeepSeek配置
    deepseek: DeepSeekConfig = Field(default_factory=DeepSeekConfig)

    # Doubao配置
    doubao: DoubaoConfig = Field(default_factory=DoubaoConfig)

    # Kimi配置
    kimi: KimiConfig = Field(default_factory=KimiConfig)

    # ZhipuAI配置
    zhipuai: ZhipuAIConfig = Field(default_factory=ZhipuAIConfig)

    # LLM路由配置
    llm_routing: LLMRoutingConfig = Field(default_factory=LLMRoutingConfig)

    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    enable_request_logging: bool = Field(default=True, description="启用请求日志")

    # 缓存配置
    enable_caching: bool = Field(default=True, description="启用缓存")
    cache_ttl: int = Field(default=1800, description="缓存过期时间（秒）")

    # 性能配置
    max_concurrent_requests: int = Field(default=10, description="最大并发请求数")
    request_timeout: int = Field(default=300, description="请求超时（秒）")

    # RAG配置
    rag_index_path: str = Field(default="./data/rag_documents", description="RAG索引路径")
    vector_store_path: str = Field(default="./data/vector_store", description="向量存储路径")
    vector_dimension: int = Field(default=1536, description="向量维度")

    # 任务队列配置
    task_queue_type: str = Field(default="redis", description="任务队列类型")
    task_queue_url: str = Field(default="redis://localhost:6379", description="任务队列URL")
    max_workers: int = Field(default=4, description="最大工作进程数")

    # 对话记忆配置
    enable_conversation_memory: bool = Field(default=True, description="启用对话记忆")
    memory_max_tokens: int = Field(default=4000, description="记忆最大token数")
    memory_ttl_hours: int = Field(default=24, description="记忆生存时间（小时）")

    # OCR配置
    ocr_provider: str = Field(default="doubao", description="OCR提供商")
    ocr_model: str = Field(default="doubao-seed-1-6-flash-250615", description="OCR模型")

    # 配额配置
    free_tier_lifetime_limit: int = Field(default=5, description="免费层终身限制")
    subscribed_tier_hourly_limit: int = Field(default=5, description="订阅层每小时限制")
    quota_window_size: int = Field(default=3600, description="配额窗口大小（秒）")

    # 输出配置
    output_dir: str = Field(default="./output_reports", description="输出目录")

    # 支付配置
    stripe_secret_key: Optional[str] = Field(default=None, description="Stripe密钥")
    stripe_webhook_secret: Optional[str] = Field(default=None, description="Stripe Webhook密钥")
    stripe_price_id: Optional[str] = Field(default=None, description="Stripe价格ID")
    frontend_url: str = Field(default="http://localhost:3000", description="前端URL")

    # 模型配置
    basic_model: Dict[str, Any] = Field(
        default_factory=lambda: {
            "model_name": "deepseek-chat",
            "temperature": 1.0,
            "max_tokens": 4000
        },
        description="基础模型配置"
    )
    reasoning_model: Dict[str, Any] = Field(
        default_factory=lambda: {
            "model_name": "deepseek-reasoner",
            "temperature": 1.0,
            "max_tokens": 32000
        },
        description="推理模型配置"
    )
    vision_model: Dict[str, Any] = Field(
        default_factory=lambda: {
            "model_name": "qwen2.5vl:7b",
            "temperature": 0.0,
            "max_tokens": 4000
        },
        description="视觉模型配置"
    )

    # 工作流配置
    workflows: Dict[str, Any] = Field(
        default_factory=lambda: {
            "main": {
                "enable_background_investigation": True,
                "max_plan_iterations": 3,
                "enable_human_feedback": False
            },
            "ppt": {
                "default_template": "modern",
                "max_slides": 20,
                "enable_charts": True,
                "provider_priority": ["deepseek", "ollama", "domestic"],
                "models": {
                    "outline_generation": "deepseek-chat",
                    "content_generation": "deepseek-reasoner",
                    "fallback_model": "ollama:qwen3:7b"
                },
                "output_dir": "./data/ppt_exports",
                "image_cache_dir": "./data/ppt_images",
                "image_service": {
                    "enable_cache": True,
                    "cache_ttl_days": 7,
                    "max_image_size": "1920x1080",
                    "supported_formats": ["jpg", "png"]
                },
                "quality_control": {
                    "min_dsl_validation_score": 0.8,
                    "max_retries": 3,
                    "enable_proofreading": True
                }
            },
            "podcast": {
                "default_voice": "female",
                "audio_format": "mp3",
                "sample_rate": 44100
            },
            "prose": {
                "default_style": "academic",
                "max_length": 5000
            }
        },
        description="工作流配置"
    )

    # 配置优先级
    class Config(SettingsConfigDict):
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

        # 环境变量前缀
        env_prefix = "DEEP_RESEARCH_"

        # 环境变量映射
        env_field_mapping = {
            "DEEP_RESEARCH_SECURITY_SECRET_KEY": "security.secret_key",
        }

        # 额外的配置源
        yaml_file = "conf.yaml"
        yaml_file_encoding = "utf-8"

        # 配置验证
        validate_all = True
        extra = "forbid"

    @root_validator
    def validate_config(cls, values):
        """验证配置一致性"""
        # 检查冲突的配置
        if values.primary_llm_backend and values.llm_routing:
            primary_backend = values.primary_llm_backend.lower()
            priority_map = values.llm_routing.provider_priority

            # 检查主要后端是否在优先级列表中
            for task_type, providers in priority_map.items():
                if primary_backend in providers:
                    # 主要后端与优先级一致，发出警告
                    logger.warning(
                        f"主要后端'{primary_backend}'与任务类型'{task_type}'的优先级配置一致，"
                        f"可能导致路由混乱"
                    )

        # 统一密钥验证已在 SecurityConfig 中处理
        if hasattr(values.security, 'secret_key'):
            secret_key = values.security.secret_key
            if secret_key and any(weak_key in secret_key.lower() for weak_key in
                                ["your_", "secret", "key", "change", "random"]):
                logger.warning("检测到潜在弱密钥，建议在生产环境中使用强密钥")

        return values

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "forbid"

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号分隔的嵌套键）"""
        keys = key.split('.')
        value = self.dict()

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.dict().copy()

    def get_nested(self, key_path: str, default: Any = None) -> Any:
        """获取嵌套配置值"""
        try:
            keys = key_path.split('.')
            value = self.dict()
            for key in keys:
                value = getattr(value, key, default)
            return value
        except (AttributeError, TypeError):
            return default
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的嵌套键）
        
        Args:
            key: 配置键，支持 "WORKFLOWS.ppt.output_dir" 格式
            default: 默认值
        
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    # 便捷属性访问
    @property
    def app_name(self) -> str:
        return self.get('APP_NAME', 'Deep Research Platform')
    
    @property
    def app_version(self) -> str:
        return self.get('APP_VERSION', '1.0.0')
    
    @property
    def environment(self) -> str:
        return self.get('ENVIRONMENT', 'development')
    
    @property
    def debug(self) -> bool:
        return self.get('DEBUG', True)
    
    @property
    def host(self) -> str:
        return self.get('HOST', '0.0.0.0')
    
    @property
    def port(self) -> int:
        return self.get('PORT', 8000)
    
    @property
    def enable_reload(self) -> bool:
        return self.get('ENABLE_RELOAD', True)
    
    # 数据库配置
    @property
    def database_url(self) -> str:
        return self.get('DATABASE_URL', 'postgresql+asyncpg://deerflow:deerflow123@localhost:5432/deerflow')
    
    @property
    def auto_create_tables(self) -> bool:
        return self.get('AUTO_CREATE_TABLES', True)
    
    # Redis 配置
    @property
    def redis_url(self) -> str:
        return self.get('REDIS_URL', 'redis://localhost:6379')
    
    # JWT 配置
    @property
    def secret_key(self) -> str:
        return self.get('SECRET_KEY', 'your_super_secret_jwt_key_here')
    
    @property
    def algorithm(self) -> str:
        return self.get('ALGORITHM', 'HS256')
    
    @property
    def access_token_expire_minutes(self) -> int:
        return self.get('ACCESS_TOKEN_EXPIRE_MINUTES', 30)
    
    # Stripe 配置
    @property
    def stripe_secret_key(self) -> str:
        return self.get('STRIPE_SECRET_KEY', '')
    
    @property
    def stripe_webhook_secret(self) -> str:
        return self.get('STRIPE_WEBHOOK_SECRET', '')
    
    @property
    def stripe_price_id(self) -> str:
        return self.get('STRIPE_PRICE_ID', '')
    
    @property
    def frontend_url(self) -> str:
        return self.get('FRONTEND_URL', 'http://localhost:3000')
    
    # 配额配置
    @property
    def free_tier_lifetime_limit(self) -> int:
        return self.get('FREE_TIER_LIFETIME_LIMIT', 5)
    
    @property
    def subscribed_tier_hourly_limit(self) -> int:
        return self.get('SUBSCRIBED_TIER_HOURLY_LIMIT', 5)
    
    @property
    def quota_window_size(self) -> int:
        return self.get('QUOTA_WINDOW_SIZE', 3600)
    
    # 文件上传配置
    @property
    def max_file_size(self) -> int:
        return self.get('MAX_FILE_SIZE', 10485760)
    
    @property
    def allowed_file_types(self) -> str:
        return self.get('ALLOWED_FILE_TYPES', '.docx,.doc,.txt,.md,.pdf,.ppt,.pptx')
    
    @property
    def upload_dir(self) -> str:
        return self.get('UPLOAD_DIR', './uploads')
    
    @property
    def temp_dir(self) -> str:
        return self.get('TEMP_DIR', './temp')
    
    # RAG 配置
    @property
    def rag_index_path(self) -> str:
        return self.get('RAG_INDEX_PATH', './data/rag_documents')
    
    @property
    def vector_store_path(self) -> str:
        return self.get('VECTOR_STORE_PATH', './data/vector_store')
    
    @property
    def vector_dimension(self) -> int:
        return self.get('VECTOR_DIMENSION', 1536)
    
    # 任务队列配置
    @property
    def task_queue_type(self) -> str:
        return self.get('TASK_QUEUE_TYPE', 'redis')
    
    @property
    def task_queue_url(self) -> str:
        return self.get('TASK_QUEUE_URL', 'redis://localhost:6379')
    
    @property
    def max_workers(self) -> int:
        return self.get('MAX_WORKERS', 4)
    
    @property
    def max_concurrent_requests(self) -> int:
        return self.get('MAX_CONCURRENT_REQUESTS', 10)
    
    @property
    def request_timeout(self) -> int:
        return self.get('REQUEST_TIMEOUT', 300)
    
    # 缓存配置
    @property
    def enable_caching(self) -> bool:
        return self.get('ENABLE_CACHING', True)
    
    @property
    def cache_ttl(self) -> int:
        return self.get('CACHE_TTL', 1800)
    
    # 日志配置
    @property
    def log_level(self) -> str:
        return self.get('LOG_LEVEL', 'INFO')
    
    @property
    def enable_request_logging(self) -> bool:
        return self.get('ENABLE_REQUEST_LOGGING', True)
    
    # CORS 配置
    @property
    def cors_allow_origins(self) -> list:
        origins_str = self.get('CORS_ALLOW_ORIGINS', 'http://localhost:3000,http://localhost:8080')
        return [origin.strip() for origin in origins_str.split(',') if origin.strip()]
    
    @property
    def cors_allow_credentials(self) -> bool:
        return self.get('CORS_ALLOW_CREDENTIALS', True)
    
    # LLM 配置
    @property
    def primary_llm_backend(self) -> str:
        return self.get('PRIMARY_LLM_BACKEND', 'DOUBAO')
    
    @property
    def fallback_llm_backend(self) -> str:
        return self.get('FALLBACK_LLM_BACKEND', 'KIMI')
    
    @property
    def default_search_provider(self) -> str:
        return self.get('DEFAULT_SEARCH_PROVIDER', 'doubao')
    
    # Ollama 配置
    @property
    def ollama_base_url(self) -> str:
        return self.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    @property
    def ollama_small_model(self) -> str:
        return self.get('OLLAMA_SMALL_MODEL', 'gemma3:4b')
    
    @property
    def ollama_large_model(self) -> str:
        return self.get('OLLAMA_LARGE_MODEL', 'qwen3:32b')
    
    @property
    def ollama_vision_model(self) -> str:
        return self.get('OLLAMA_VISION_MODEL', 'qwen2.5vl:7b')
    
    # DeepSeek 配置
    @property
    def deepseek_api_key(self) -> str:
        return os.getenv('DEEPSEEK_API_KEY', '')
    
    @property
    def deepseek_base_url(self) -> str:
        return self.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    
    # Doubao 配置
    @property
    def doubao_api_key(self) -> str:
        return os.getenv('DOUBAO_API_KEY', '')
    
    @property
    def doubao_base_url(self) -> str:
        return self.get('DOUBAO_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3')
    
    @property
    def doubao_model(self) -> str:
        return self.get('DOUBAO_MODEL', 'doubao-seed-1-6-flash-250615')
    
    @property
    def doubao_vision_model(self) -> str:
        return self.get('DOUBAO_VISION_MODEL', 'doubao-1-5-vision-pro-250328')
    
    # Kimi 配置
    @property
    def kimi_api_key(self) -> str:
        return os.getenv('KIMI_API_KEY', '') or os.getenv('MOONSHOT_API_KEY', '')
    
    @property
    def kimi_base_url(self) -> str:
        return self.get('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
    
    @property
    def kimi_model(self) -> str:
        return self.get('KIMI_MODEL', 'moonshot-v1-8k')

    # ZhipuAI配置
    @property
    def zhipuai_api_key(self) -> str:
        return os.getenv('ZHIPUAI_API_KEY', '')

    @property
    def zhipuai_base_url(self) -> str:
        return self.get('ZHIPUAI_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4')

    @property
    def zhipuai_chat_model(self) -> str:
        return self.get('ZHIPUAI_MODELS', {}).get('chat', 'glm-4.5-air')

    @property
    def zhipuai_free_model(self) -> str:
        return self.get('ZHIPUAI_MODELS', {}).get('free', 'glm-4.5-flash')

    @property
    def zhipuai_premium_model(self) -> str:
        return self.get('ZHIPUAI_MODELS', {}).get('premium', 'glm-4.6')

    @property
    def zhipuai_cost_effective_model(self) -> str:
        return self.get('ZHIPUAI_MODELS', {}).get('cost_effective', 'glm-4.5-air')

    @property
    def zhipuai_reasoning_model(self) -> str:
        return self.get('ZHIPUAI_MODELS', {}).get('reasoning', 'glm-4.6')

    @property
    def zhipuai_vision_model(self) -> str:
        return self.get('ZHIPUAI_MODELS', {}).get('vision', 'glm-4.1v-thinking-flash')

    @property
    def zhipuai_search_model(self) -> str:
        return self.get('ZHIPUAI_MODELS', {}).get('search', 'glm-4.5-flash')

    # 对话记忆配置
    @property
    def enable_conversation_memory(self) -> bool:
        return self.get('ENABLE_CONVERSATION_MEMORY', True)

    @property
    def memory_max_tokens(self) -> int:
        return self.get('MEMORY_MAX_TOKENS', 4000)

    @property
    def memory_ttl_hours(self) -> int:
        return self.get('MEMORY_TTL_HOURS', 24)

    # OCR 配置
    @property
    def ocr_provider(self) -> str:
        return self.get('OCR_PROVIDER', 'doubao')

    @property
    def ocr_model(self) -> str:
        return self.get('OCR_MODEL', 'doubao-seed-1-6-flash-250615')


class ConfigLoader:
    """
    配置加载器类
    支持从环境变量、.env文件、conf.yaml文件和默认值加载配置
    优先级: 环境变量 > .env文件 > conf.yaml > 默认值
    """

    def __init__(self, yaml_file: str = "conf.yaml"):
        self.yaml_file = yaml_file
        self._config = {}
        self._load_config()

    def _load_config(self):
        """加载配置"""
        # 1. 加载默认配置
        self._config = self._load_default_config()

        # 2. 加载YAML配置文件
        yaml_config = self._load_yaml_config()
        if yaml_config:
            self._merge_config(self._config, yaml_config)

        # 3. 加载环境变量
        env_config = self._load_env_config()
        if env_config:
            self._merge_config(self._config, env_config)

    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            "APP_NAME": "Deep Research Platform",
            "APP_VERSION": "1.0.0",
            "ENVIRONMENT": "development",
            "DEBUG": True,
            "HOST": "0.0.0.0",
            "PORT": 8000,
            "ENABLE_RELOAD": True,
            "DATABASE_URL": "postgresql+asyncpg://deerflow:deerflow123@localhost:5432/deerflow",
            "AUTO_CREATE_TABLES": True,
            "REDIS_URL": "redis://localhost:6379",
            "SECRET_KEY": "your_super_secret_jwt_key_here_make_it_long_and_random",
            "ALGORITHM": "HS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
            "CORS_ALLOW_ORIGINS": "http://localhost:3000,http://localhost:8080",
            "CORS_ALLOW_CREDENTIALS": True,
            "PRIMARY_LLM_BACKEND": "DOUBAO",
            "DEFAULT_SEARCH_PROVIDER": "doubao",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1",
            "DOUBAO_BASE_URL": "https://ark.cn-beijing.volces.com/api/v3",
            "DOUBAO_MODEL": "doubao-seed-1-6-flash-250615",
            "DOUBAO_VISION_MODEL": "doubao-1-5-vision-pro-250328",
            "KIMI_BASE_URL": "https://api.moonshot.cn/v1",
            "KIMI_MODEL": "moonshot-v1-8k",
            "KIMI_LONG_CONTEXT_MODEL": "moonshot-v1-128k",
            "ZHIPUAI_BASE_URL": "https://open.bigmodel.cn/api/paas/v4",
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "OLLAMA_SMALL_MODEL": "gemma3:4b",
            "OLLAMA_LARGE_MODEL": "qwen3:32b",
            "OLLAMA_VISION_MODEL": "qwen2.5vl:7b",
            "FREE_TIER_LIFETIME_LIMIT": 5,
            "SUBSCRIBED_TIER_HOURLY_LIMIT": 5,
            "QUOTA_WINDOW_SIZE": 3600,
            "MAX_FILE_SIZE": 10485760,
            "ALLOWED_FILE_TYPES": ".docx,.doc,.txt,.md,.pdf,.ppt,.pptx",
            "UPLOAD_DIR": "./uploads",
            "TEMP_DIR": "./temp",
            "RAG_INDEX_PATH": "./data/rag_documents",
            "VECTOR_STORE_PATH": "./data/vector_store",
            "VECTOR_DIMENSION": 1536,
            "TASK_QUEUE_TYPE": "redis",
            "TASK_QUEUE_URL": "redis://localhost:6379",
            "MAX_WORKERS": 4,
            "ENABLE_CONVERSATION_MEMORY": True,
            "MEMORY_MAX_TOKENS": 4000,
            "MEMORY_TTL_HOURS": 24,
            "OCR_PROVIDER": "doubao",
            "OCR_MODEL": "doubao-seed-1-6-flash-250615",
            "LOG_LEVEL": "INFO",
            "ENABLE_REQUEST_LOGGING": True,
            "ENABLE_CACHING": True,
            "CACHE_TTL": 1800,
            "MAX_CONCURRENT_REQUESTS": 10,
            "REQUEST_TIMEOUT": 300,
            "OUTPUT_DIR": "./output_reports"
        }

    def _load_yaml_config(self) -> Optional[Dict[str, Any]]:
        """加载YAML配置文件"""
        try:
            yaml_path = Path(self.yaml_file)
            if yaml_path.exists():
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 处理环境变量替换
                    content = self._substitute_env_vars(content)
                    return yaml.safe_load(content) or {}
        except Exception as e:
            logger.warning(f"加载YAML配置文件失败: {e}")
        return None

    def _substitute_env_vars(self, content: str) -> str:
        """替换配置文件中的环境变量"""
        import re

        def replace_env_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) else ""
            return os.getenv(var_name, default_value)

        # 支持 ${VAR_NAME} 和 ${VAR_NAME:default} 格式
        pattern = r'\$\{([^}]+)(?::([^}]*))?\}'
        return re.sub(pattern, replace_env_var, content)

    def _load_env_config(self) -> Dict[str, Any]:
        """加载环境变量配置"""
        env_config = {}

        # API密钥配置
        api_key_mappings = {
            "DEEP_RESEARCH_DEEPSEEK_API_KEY": "DEEPSEEK_API_KEY",
            "DEEP_RESEARCH_DOUBAO_API_KEY": "DOUBAO_API_KEY",
            "DEEP_RESEARCH_KIMI_API_KEY": "KIMI_API_KEY",
            "DEEP_RESEARCH_MOONSHOT_API_KEY": "MOONSHOT_API_KEY",
            "DEEP_RESEARCH_ZHIPUAI_API_KEY": "ZHIPUAI_API_KEY",
            "DEEP_RESEARCH_SECURITY_SECRET_KEY": "SECRET_KEY",
            "DEEP_RESEARCH_DATABASE_URL": "DATABASE_URL",
            "DEEP_RESEARCH_REDIS_URL": "REDIS_URL",
            "DEEP_RESEARCH_STRIPE_SECRET_KEY": "STRIPE_SECRET_KEY",
            "DEEP_RESEARCH_STRIPE_WEBHOOK_SECRET": "STRIPE_WEBHOOK_SECRET",
            "DEEP_RESEARCH_STRIPE_PRICE_ID": "STRIPE_PRICE_ID",
            "DEEP_RESEARCH_FRONTEND_URL": "FRONTEND_URL"
        }

        # 通用环境变量映射
        for env_var, config_key in api_key_mappings.items():
            value = os.getenv(env_var)
            if value:
                env_config[config_key] = value

        # 处理其他环境变量（去除前缀）
        env_prefix = "DEEP_RESEARCH_"
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):]
                if config_key not in env_config:  # 避免覆盖API密钥映射
                    env_config[config_key] = self._convert_env_value(value)

        return env_config

    def _convert_env_value(self, value: str) -> Any:
        """转换环境变量值的类型"""
        # 布尔值
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False

        # 数字
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # 字符串
        return value

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """合并配置"""
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的嵌套键）

        Args:
            key: 配置键，支持 "WORKFLOWS.ppt.output_dir" 格式
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()

    def get_nested(self, key_path: str, default: Any = None) -> Any:
        """获取嵌套配置值"""
        try:
            keys = key_path.split('.')
            value = self._config
            for key in keys:
                value = getattr(value, key, default)
            return value
        except (AttributeError, TypeError):
            return default


# 全局配置实例
_config: Optional[ConfigLoader] = None


def get_config() -> ConfigLoader:
    """获取全局配置实例（单例模式）"""
    global _config
    if _config is None:
        _config = ConfigLoader()
    return _config


# 向后兼容：提供 get_settings 别名
def get_settings() -> ConfigLoader:
    """向后兼容的函数名"""
    return get_config()
