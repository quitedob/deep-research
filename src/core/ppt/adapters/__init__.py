# -*- coding: utf-8 -*-
"""
PPT生成模块适配器：统一不同语言模型提供商的调用接口。

主要适配器：
- DeepSeekAdapter: 适配DeepSeek API，支持OpenAI兼容接口
- OllamaAdapter: 适配本地Ollama服务
- DomesticAdapter: 适配国内厂商API（百度、阿里、腾讯等）
"""

from .deepseek_adapter import DeepSeekAdapter
from .ollama_adapter import OllamaAdapter
from .domestic_adapter import DomesticAdapter

__all__ = ["DeepSeekAdapter", "OllamaAdapter", "DomesticAdapter"]
