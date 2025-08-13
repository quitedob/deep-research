# -*- coding: utf-8 -*-
"""
AgentWork 配置管理模块（统一配置源）
以 conf.yaml 为唯一可信源，结合环境变量（如 API Key）进行加载与校验。
"""

import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml

ROOT_DIR = Path(__file__).parent.parent.parent.absolute()
CONFIG_FILE = ROOT_DIR / "conf.yaml"


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"配置文件未找到: {path}")
    text = path.read_text(encoding="utf-8")
    # 展开 ${VAR} 环境变量占位
    text = os.path.expandvars(text)
    return yaml.safe_load(text)


class Settings(BaseSettings):
    """应用设置（强类型），从 conf.yaml 加载并允许环境覆盖。"""

    # 服务器
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    DEBUG: bool = Field(default=True)

    # CORS
    CORS_ALLOW_ORIGINS: List[str] = Field(default=["*"])
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)

    # 日志
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Provider 相关（供路由器参考）
    OLLAMA_BASE_URL: Optional[str] = None
    OLLAMA_SMALL_MODEL: Optional[str] = None
    DEEPSEEK_BASE_URL: Optional[str] = None
    KIMI_BASE_URL: Optional[str] = None

    PROVIDER_PRIORITY: Dict[str, List[str]] = Field(default_factory=dict)

    # API Keys（来自环境变量）
    DEEPSEEK_API_KEY: Optional[str] = None
    MOONSHOT_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @classmethod
    def from_yaml(cls) -> "Settings":
        data = _load_yaml(CONFIG_FILE)
        return cls.model_validate(data)

_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings.from_yaml()
    return _settings
