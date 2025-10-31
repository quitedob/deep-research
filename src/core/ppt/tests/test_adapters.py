# -*- coding: utf-8 -*-
"""
PPT适配器测试

测试各种LLM适配器的功能和性能。
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from ..adapters.deepseek_adapter import DeepSeekAdapter
from ..adapters.ollama_adapter import OllamaAdapter
from ..adapters.domestic_adapter import DomesticAdapter


class TestDeepSeekAdapter:
    """DeepSeek适配器测试类"""

    @pytest.fixture
    def adapter(self):
        """创建DeepSeek适配器实例"""
        with patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test_key'}):
            return DeepSeekAdapter()

    def test_adapter_initialization(self):
        """测试适配器初始化"""
        adapter = DeepSeekAdapter()
        assert adapter.base_url is not None
        assert adapter.default_model == "deepseek-chat"
        assert adapter.timeout == 60

    def test_health_check_without_key(self):
        """测试无API密钥时的健康检查"""
        with patch.dict('os.environ', {}, clear=True):
            adapter = DeepSeekAdapter()
            is_healthy, msg = adapter.health_check()
            assert not is_healthy
            assert "API密钥未配置" in msg

    @pytest.mark.asyncio
    async def test_generate_method(self, adapter):
        """测试生成方法（mock版本）"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "choices": [{"message": {"content": "Generated text"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20}
            })

            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            result = await adapter.generate("Test prompt")
            assert result == "Generated text"

    def test_get_available_models(self, adapter):
        """测试获取可用模型列表"""
        models = adapter.get_available_models()
        assert isinstance(models, list)
        assert "deepseek-chat" in models
        assert "deepseek-coder" in models

    def test_estimate_cost(self, adapter):
        """测试成本估算"""
        cost = adapter.estimate_cost(1000, 2000, "deepseek-chat")
        assert isinstance(cost, float)
        assert cost > 0


class TestOllamaAdapter:
    """Ollama适配器测试类"""

    @pytest.fixture
    def adapter(self):
        """创建Ollama适配器实例"""
        return OllamaAdapter()

    def test_adapter_initialization(self, adapter):
        """测试适配器初始化"""
        assert adapter.base_url is not None
        assert adapter.default_model is not None
        assert adapter.timeout == 120

    @pytest.mark.asyncio
    async def test_generate_method(self, adapter):
        """测试生成方法（mock版本）"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "response": "Generated text from Ollama",
                "eval_count": 15
            })

            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            result = await adapter.generate("Test prompt")
            assert result == "Generated text from Ollama"

    def test_estimate_cost(self, adapter):
        """测试成本估算（Ollama本地运行，成本为0）"""
        cost = adapter.estimate_cost(1000, 2000)
        assert cost == 0.0


class TestDomesticAdapter:
    """国内厂商适配器测试类"""

    @pytest.fixture
    def adapter(self):
        """创建国内厂商适配器实例"""
        return DomesticAdapter()

    def test_adapter_initialization(self, adapter):
        """测试适配器初始化"""
        assert "aliyun" in adapter.providers
        assert "baidu" in adapter.providers
        assert "tencent" in adapter.providers
        assert "xfyun" in adapter.providers

    def test_provider_configurations(self, adapter):
        """测试provider配置"""
        aliyun_config = adapter.providers["aliyun"]
        assert "enabled" in aliyun_config
        assert "api_key" in aliyun_config
        assert "model" in aliyun_config

    def test_get_available_providers(self, adapter):
        """测试获取可用provider列表"""
        providers = adapter.get_available_providers()
        assert isinstance(providers, list)

    def test_health_check(self, adapter):
        """测试健康检查"""
        is_healthy, msg = adapter.health_check()
        assert isinstance(is_healthy, bool)
        assert isinstance(msg, str)

    def test_health_check_specific_provider(self, adapter):
        """测试特定provider的健康检查"""
        is_healthy, msg = adapter.health_check("aliyun")
        assert isinstance(is_healthy, bool)
        assert isinstance(msg, str)

    def test_health_check_invalid_provider(self, adapter):
        """测试无效provider的健康检查"""
        is_healthy, msg = adapter.health_check("invalid_provider")
        assert not is_healthy
        assert "未知的provider" in msg

    def test_estimate_cost(self, adapter):
        """测试成本估算"""
        cost = adapter.estimate_cost(1000, 2000, "aliyun")
        assert isinstance(cost, float)
        assert cost >= 0

    @pytest.mark.asyncio
    async def test_generate_unimplemented_provider(self, adapter):
        """测试未实现的provider生成"""
        with pytest.raises(NotImplementedError):
            await adapter._generate_aliyun("Test prompt", None, 1000, 0.7)


class TestAdapterIntegration:
    """适配器集成测试"""

    @pytest.mark.asyncio
    async def test_all_adapters_initialization(self):
        """测试所有适配器的初始化"""
        adapters = []

        # DeepSeek适配器
        with patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test_key'}):
            adapters.append(DeepSeekAdapter())

        # Ollama适配器
        adapters.append(OllamaAdapter())

        # 国内厂商适配器
        adapters.append(DomesticAdapter())

        for adapter in adapters:
            assert adapter is not None

    def test_adapter_consistency(self):
        """测试适配器接口一致性"""
        adapters = [
            DeepSeekAdapter(),
            OllamaAdapter(),
            DomesticAdapter()
        ]

        # 检查所有适配器都有相同的基本接口
        for adapter in adapters:
            assert hasattr(adapter, 'generate')
            assert hasattr(adapter, 'health_check')
            assert hasattr(adapter, 'estimate_cost')

            # 检查方法的签名
            import inspect
            generate_sig = inspect.signature(adapter.generate)
            assert 'prompt' in generate_sig.parameters


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])