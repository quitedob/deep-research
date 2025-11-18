"""
LLM Factory Pattern implementation.
Provides centralized creation and configuration of LLM instances.
"""

from typing import Optional, Dict, Any
import logging

from src.core.llm.base_llm import BaseLLM, ConfigurationError
from src.core.llm.ollama_llm import OllamaLLM
from src.core.llm.deepseek_llm import DeepSeekLLM
from src.core.llm.zhipu_llm import ZhipuLLM
from src.config.llm_config import get_config, ProviderConfig

logger = logging.getLogger(__name__)


class LLMFactory:
    """
    Factory class for creating LLM instances.
    Handles provider selection, configuration, and validation.
    """
    
    # Mapping of provider names to their implementation classes
    _PROVIDERS = {
        "ollama": OllamaLLM,
        "deepseek": DeepSeekLLM,
        "zhipu": ZhipuLLM,
    }
    
    @staticmethod
    def create_llm(
        provider: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ) -> BaseLLM:
        """
        Create an LLM instance for the specified provider.
        
        Args:
            provider: Provider name ('ollama', 'deepseek', 'zhipu')
            api_key: Optional API key (overrides config)
            base_url: Optional base URL (overrides config)
            **kwargs: Additional configuration parameters
            
        Returns:
            Configured LLM instance
            
        Raises:
            ConfigurationError: If provider is invalid or configuration fails
        """
        provider = provider.lower()
        
        # Validate provider
        if provider not in LLMFactory._PROVIDERS:
            raise ConfigurationError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: {', '.join(LLMFactory._PROVIDERS.keys())}"
            )
        
        # Get provider configuration
        config = get_config()
        provider_config = config.get_provider_config(provider)
        
        # Validate configuration
        is_valid, error = config.validate_provider_config(provider)
        if not is_valid and provider != "ollama":  # Ollama doesn't require API key
            logger.warning(f"Provider {provider} configuration issue: {error}")
        
        # Prepare initialization parameters
        init_params = {
            "api_key": api_key or provider_config.api_key,
            "base_url": base_url or provider_config.base_url,
            **kwargs
        }
        
        # Create and return LLM instance
        llm_class = LLMFactory._PROVIDERS[provider]
        try:
            llm_instance = llm_class(**init_params)
            logger.info(f"Successfully created {provider} LLM instance")
            return llm_instance
        except Exception as e:
            raise ConfigurationError(f"Failed to create {provider} LLM instance: {str(e)}")
    
    @staticmethod
    def get_default_config(provider: str) -> Dict[str, Any]:
        """
        Get default configuration for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Dictionary containing default configuration
            
        Raises:
            ConfigurationError: If provider is invalid
        """
        provider = provider.lower()
        
        if provider not in LLMFactory._PROVIDERS:
            raise ConfigurationError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: {', '.join(LLMFactory._PROVIDERS.keys())}"
            )
        
        config = get_config()
        provider_config = config.get_provider_config(provider)
        
        return {
            "name": provider_config.name,
            "api_key": provider_config.api_key,
            "base_url": provider_config.base_url,
            "default_model": provider_config.default_model,
            "timeout": provider_config.timeout,
            "max_retries": provider_config.max_retries,
            "additional_params": provider_config.additional_params,
        }
    
    @staticmethod
    def list_providers() -> list[str]:
        """
        Get list of supported providers.
        
        Returns:
            List of provider names
        """
        return list(LLMFactory._PROVIDERS.keys())
    
    @staticmethod
    def validate_provider(provider: str) -> tuple[bool, Optional[str]]:
        """
        Validate if a provider is supported and properly configured.
        
        Args:
            provider: Provider name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        provider = provider.lower()
        
        # Check if provider exists
        if provider not in LLMFactory._PROVIDERS:
            return False, f"Unsupported provider: {provider}"
        
        # Check configuration
        config = get_config()
        return config.validate_provider_config(provider)
    
    @staticmethod
    def create_from_config(provider: str) -> BaseLLM:
        """
        Create an LLM instance using only configuration (no overrides).
        
        Args:
            provider: Provider name
            
        Returns:
            Configured LLM instance
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        return LLMFactory.create_llm(provider)
