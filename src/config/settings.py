# -*- coding: utf-8 -*-
"""
AgentWork 配置管理模块
使用pydantic-settings管理环境变量和配置
"""

import os
from typing import List, Optional
from pathlib import Path
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# 加载.env文件
ROOT_DIR = Path(__file__).parent.parent.parent.absolute()
env_file = ROOT_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)

class Settings(BaseSettings):
    """应用设置类（精简为 Kimi/Moonshot 专用）"""

    # === 基础配置 ===
    DEBUG: bool = Field(default=True, env="DEBUG")

    # === 服务器配置 ===
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")

    # === CORS配置 ===
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"], env="CORS_ORIGINS"
    )

    # === 日志配置 ===
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # === Kimi/Moonshot API配置 ===
    MOONSHOT_API_KEY: Optional[str] = Field(default=None, env="MOONSHOT_API_KEY")
    MOONSHOT_BASE_URL: str = Field(default="https://api.moonshot.cn/v1", env="MOONSHOT_BASE_URL")
    KIMI_MODEL_CHAT: str = Field(default="moonshot-v1-8k", env="KIMI_MODEL_CHAT")
    KIMI_MODEL_RESEARCH: str = Field(default="moonshot-v1-32k", env="KIMI_MODEL_RESEARCH")

    class Config:
        env_file = str(env_file) if env_file.exists() else None
        case_sensitive = True

# 全局设置实例
_settings = None

def get_settings() -> Settings:
    """获取设置实例（单例模式）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
