# -*- coding: utf-8 -*-
"""PPT测试模块

包含PPT生成器的完整测试套件，包括单元测试、集成测试和性能测试。
"""

from .test_generator import TestPPTGenerator, TestIntegration
from .test_renderer import TestPPTXRenderer, TestImageService, TestRendererIntegration
from .test_adapters import TestDeepSeekAdapter, TestOllamaAdapter, TestDomesticAdapter, TestAdapterIntegration

__all__ = [
    "TestPPTGenerator",
    "TestIntegration",
    "TestPPTXRenderer",
    "TestImageService",
    "TestRendererIntegration",
    "TestDeepSeekAdapter",
    "TestOllamaAdapter",
    "TestDomesticAdapter",
    "TestAdapterIntegration"
]


