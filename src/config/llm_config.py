"""
LLM Configuration Management System.
Handles configuration for all LLM providers (Ollama, DeepSeek, Zhipu AI).
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class ProviderConfig:
    """Configuration for a single LLM provider."""
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    timeout: int = 60
    max_retries: int = 3
    additional_params: Dict[str, Any] = field(default_factory=dict)


class LLMConfig:
    """
    Central configuration management for all LLM providers.
    Loads configuration from environment variables and provides defaults.
    """
    
    def __init__(self):
        """Initialize LLM configuration with environment variables."""
        self.ollama = self._get_ollama_config()
        self.deepseek = self._get_deepseek_config()
        self.zhipu = self._get_zhipu_config()
        
    def _get_ollama_config(self) -> ProviderConfig:
        """
        Get Ollama configuration.
        
        Returns:
            ProviderConfig for Ollama
        """
        return ProviderConfig(
            name="ollama",
            api_key=os.getenv("OLLAMA_API_KEY"),  # Optional for local Ollama
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            default_model=os.getenv("OLLAMA_DEFAULT_MODEL", "gemma3:4b"),
            timeout=int(os.getenv("OLLAMA_TIMEOUT", "60")),
            max_retries=int(os.getenv("OLLAMA_MAX_RETRIES", "3")),
            additional_params={
                "stream": os.getenv("OLLAMA_STREAM", "false").lower() == "true",
            }
        )
    
    def _get_deepseek_config(self) -> ProviderConfig:
        """
        Get DeepSeek configuration.
        
        Returns:
            ProviderConfig for DeepSeek
        """
        return ProviderConfig(
            name="deepseek",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            default_model=os.getenv("DEEPSEEK_DEFAULT_MODEL", "deepseek-chat"),
            timeout=int(os.getenv("DEEPSEEK_TIMEOUT", "60")),
            max_retries=int(os.getenv("DEEPSEEK_MAX_RETRIES", "3")),
            additional_params={
                "temperature": float(os.getenv("DEEPSEEK_TEMPERATURE", "1.0")),
                "max_tokens": int(os.getenv("DEEPSEEK_MAX_TOKENS", "4096")),
            }
        )
    
    def _get_zhipu_config(self) -> ProviderConfig:
        """
        Get Zhipu AI configuration.
        
        Returns:
            ProviderConfig for Zhipu AI
        """
        return ProviderConfig(
            name="zhipu",
            api_key=os.getenv("BIGMODEL_API_KEY"),
            base_url=os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
            default_model=os.getenv("ZHIPU_DEFAULT_MODEL", "glm-4.6"),
            timeout=int(os.getenv("ZHIPU_TIMEOUT", "60")),
            max_retries=int(os.getenv("ZHIPU_MAX_RETRIES", "3")),
            additional_params={
                "temperature": float(os.getenv("ZHIPU_TEMPERATURE", "1.0")),
                "max_tokens": int(os.getenv("ZHIPU_MAX_TOKENS", "4096")),
            }
        )
    
    def get_provider_config(self, provider: str) -> ProviderConfig:
        """
        Get configuration for a specific provider.
        
        Args:
            provider: Provider name ('ollama', 'deepseek', 'zhipu')
            
        Returns:
            ProviderConfig for the specified provider
            
        Raises:
            ValueError: If provider is not supported
        """
        provider = provider.lower()
        if provider == "ollama":
            return self.ollama
        elif provider == "deepseek":
            return self.deepseek
        elif provider == "zhipu":
            return self.zhipu
        else:
            raise ValueError(f"Unsupported provider: {provider}. Supported providers: ollama, deepseek, zhipu")
    
    def validate_provider_config(self, provider: str) -> tuple[bool, Optional[str]]:
        """
        Validate configuration for a specific provider.
        
        Args:
            provider: Provider name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            config = self.get_provider_config(provider)
        except ValueError as e:
            return False, str(e)
        
        # Ollama doesn't require API key for local usage
        if provider != "ollama" and not config.api_key:
            return False, f"{provider} requires an API key. Set {provider.upper()}_API_KEY environment variable."
        
        if not config.base_url:
            return False, f"{provider} requires a base URL."
        
        if not config.default_model:
            return False, f"{provider} requires a default model."
        
        return True, None
    
    def get_all_configs(self) -> Dict[str, ProviderConfig]:
        """
        Get all provider configurations.
        
        Returns:
            Dictionary mapping provider names to their configurations
        """
        return {
            "ollama": self.ollama,
            "deepseek": self.deepseek,
            "zhipu": self.zhipu,
        }


# Global configuration instance
_config_instance: Optional[LLMConfig] = None


def get_config() -> LLMConfig:
    """
    Get the global LLM configuration instance (singleton pattern).
    
    Returns:
        LLMConfig instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = LLMConfig()
    return _config_instance


def validate_config(provider: Optional[str] = None) -> Dict[str, tuple[bool, Optional[str]]]:
    """
    Validate LLM configuration for one or all providers.
    
    Args:
        provider: Optional provider name to validate. If None, validates all providers.
        
    Returns:
        Dictionary mapping provider names to (is_valid, error_message) tuples
    """
    config = get_config()
    
    if provider:
        is_valid, error = config.validate_provider_config(provider)
        return {provider: (is_valid, error)}
    else:
        # Validate all providers
        results = {}
        for provider_name in ["ollama", "deepseek", "zhipu"]:
            is_valid, error = config.validate_provider_config(provider_name)
            results[provider_name] = (is_valid, error)
        return results
