# -*- coding: utf-8 -*-
"""
统一配置加载器
从 conf.yaml 和环境变量加载所有配置
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
import re


class ConfigLoader:
    """配置加载器 - 统一从 conf.yaml 加载配置"""
    
    def __init__(self, config_path: str = "conf.yaml"):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f) or {}
        
        # 处理环境变量替换
        self._resolve_env_vars(self._config)
    
    def _resolve_env_vars(self, config: Dict[str, Any]):
        """
        递归解析配置中的环境变量
        支持格式: ${ENV_VAR:default_value}
        """
        for key, value in config.items():
            if isinstance(value, str):
                # 匹配 ${VAR:default} 或 ${VAR} 格式
                match = re.match(r'\$\{([^:}]+)(?::([^}]*))?\}', value)
                if match:
                    env_var = match.group(1)
                    default = match.group(2) if match.group(2) is not None else ""
                    config[key] = os.getenv(env_var, default)
            elif isinstance(value, dict):
                self._resolve_env_vars(value)
    
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
        return self.get('OLLAMA_BASE_URL', 'http://localhost:11434/v1')
    
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
