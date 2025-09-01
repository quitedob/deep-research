# -*- coding: utf-8 -*-
"""
应用配置：集中管理所有环境变量和配置项。
"""

from __future__ import annotations

import os
from typing import List, Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础应用配置
    app_name: str = Field(default="Deep Research Platform", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    enable_reload: bool = Field(default=True, env="ENABLE_RELOAD")
    
    # 数据库配置
    database_url: str = Field(
        default="postgresql+asyncpg://deepresearch:deepresearch_password@localhost:5432/deepresearch_db",
        env="DATABASE_URL"
    )
    
    # Redis配置
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # JWT配置
    secret_key: str = Field(
        default="your_super_secret_jwt_key_here_make_it_long_and_random",
        env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Stripe配置
    stripe_secret_key: str = Field(default="", env="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(default="", env="STRIPE_WEBHOOK_SECRET")
    stripe_price_id: str = Field(default="", env="STRIPE_PRICE_ID")
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    
    # 配额配置
    free_tier_lifetime_limit: int = Field(default=5, env="FREE_TIER_LIFETIME_LIMIT")
    subscribed_tier_hourly_limit: int = Field(default=5, env="SUBSCRIBED_TIER_HOURLY_LIMIT")
    quota_window_size: int = Field(default=3600, env="QUOTA_WINDOW_SIZE")
    
    # 文件上传配置
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    allowed_file_types: str = Field(default=".docx,.doc,.txt,.md,.pdf", env="ALLOWED_FILE_TYPES")
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    temp_dir: str = Field(default="./temp", env="TEMP_DIR")
    
    # RAG配置
    rag_index_path: str = Field(default="./data/rag_documents", env="RAG_INDEX_PATH")
    vector_store_path: str = Field(default="./data/vector_store", env="VECTOR_STORE_PATH")
    vector_dimension: int = Field(default=1536, env="VECTOR_DIMENSION")
    
    # 任务队列配置
    task_queue_type: str = Field(default="redis", env="TASK_QUEUE_TYPE")
    task_queue_url: str = Field(default="redis://localhost:6379", env="TASK_QUEUE_URL")
    max_workers: int = Field(default=4, env="MAX_WORKERS")
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(default=300, env="REQUEST_TIMEOUT")
    
    # 缓存配置
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    cache_ttl: int = Field(default=1800, env="CACHE_TTL")  # 30分钟
    
    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    enable_request_logging: bool = Field(default=True, env="ENABLE_REQUEST_LOGGING")
    
    # CORS配置
    cors_allow_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ALLOW_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    enable_cors_debug: bool = Field(default=False, env="ENABLE_CORS_DEBUG")
    
    # 健康检查配置
    enable_health_check: bool = Field(default=True, env="ENABLE_HEALTH_CHECK")
    health_check_interval: int = Field(default=300, env="HEALTH_CHECK_INTERVAL")
    health_check_timeout: int = Field(default=10, env="HEALTH_CHECK_TIMEOUT")
    
    # 数据库表自动创建（开发环境）
    auto_create_tables: bool = Field(default=True, env="AUTO_CREATE_TABLES")
    
    # LLM配置 - 新增
    llm_provider: str = Field(default="api", env="LLM_PROVIDER")  # "api" 或 "local"
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama2", env="OLLAMA_MODEL")
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", env="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    
    # 对话记忆配置 - 新增
    enable_conversation_memory: bool = Field(default=True, env="ENABLE_CONVERSATION_MEMORY")
    memory_max_tokens: int = Field(default=4000, env="MEMORY_MAX_TOKENS")
    memory_ttl_hours: int = Field(default=24, env="MEMORY_TTL_HOURS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
