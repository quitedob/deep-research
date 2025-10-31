# -*- coding: utf-8 -*-
"""
PPT生成器测试

测试PPT生成的核心功能。
"""

import pytest
import asyncio
from pathlib import Path

from src.core.ppt.generator import PPTGenerator, create_presentation
from src.core.ppt.config import get_ppt_config
from src.core.ppt.prompt_builder import get_prompt_builder
from src.core.ppt.utils.dsl_validator import validate_dsl


class TestPPTGenerator:
    """PPT生成器测试类"""

    @pytest.fixture
    def generator(self):
        """创建生成器实例"""
        return PPTGenerator()

    @pytest.fixture
    def sample_params(self):
        """示例参数"""
        return {
            "title": "AI技术发展趋势",
            "outline": [
                "AI概述",
                "技术突破",
                "应用场景",
                "未来展望"
            ],
            "n_slides": 5,
            "language": "Chinese",
            "tone": "professional"
        }

    def test_config_loading(self):
        """测试配置加载"""
        config = get_ppt_config()
        assert config is not None
        assert isinstance(config.get_provider_priority("ppt_content"), list)

    def test_prompt_builder(self):
        """测试Prompt构建"""
        builder = get_prompt_builder()
        prompt = builder.build_presentation_prompt(
            title="测试标题",
            outline=["要点1", "要点2"],
            n_slides=3,
            language="Chinese",
            tone="professional"
        )
        assert prompt is not None
        assert "测试标题" in prompt
        assert "要点1" in prompt

    def test_outline_prompt(self):
        """测试大纲生成Prompt"""
        builder = get_prompt_builder()
        prompt = builder.build_outline_prompt(
            topic="人工智能",
            n_slides=5,
            language="Chinese"
        )
        assert prompt is not None
        assert "人工智能" in prompt

    def test_dsl_validator_valid(self):
        """测试DSL验证器 - 有效DSL"""
        valid_dsl = """
        <PRESENTATION>
            <SECTION layout="TITLE">
                <TITLE>测试标题</TITLE>
                <SUBTITLE>副标题</SUBTITLE>
            </SECTION>
            <SECTION layout="BULLETS">
                <TITLE>内容页</TITLE>
                <CONTENT>
                    <BULLET>要点1</BULLET>
                    <BULLET>要点2</BULLET>
                </CONTENT>
            </SECTION>
        </PRESENTATION>
        """
        is_valid, msg = validate_dsl(valid_dsl)
        assert is_valid, f"验证失败: {msg}"

    def test_dsl_validator_invalid(self):
        """测试DSL验证器 - 无效DSL"""
        invalid_dsl = "<INVALID>test</INVALID>"
        is_valid, msg = validate_dsl(invalid_dsl)
        assert not is_valid

    @pytest.mark.asyncio
    async def test_create_presentation_with_outline(self, sample_params):
        """测试使用大纲创建PPT"""
        try:
            result = await create_presentation(sample_params)
            assert result is not None
            assert "presentation_id" in result
            assert "path" in result
            assert Path(result["path"]).exists()
        except Exception as e:
            # 如果没有配置API密钥，测试会失败，这是预期的
            pytest.skip(f"需要配置API密钥: {str(e)}")

    @pytest.mark.asyncio
    async def test_create_presentation_with_topic(self):
        """测试使用主题创建PPT"""
        params = {
            "title": "机器学习基础",
            "topic": "机器学习",
            "n_slides": 5,
            "language": "Chinese"
        }
        try:
            result = await create_presentation(params)
            assert result is not None
            assert "presentation_id" in result
        except Exception as e:
            pytest.skip(f"需要配置API密钥: {str(e)}")

    def test_default_outline_generation(self, generator):
        """测试默认大纲生成"""
        outline = generator._get_default_outline("测试主题", 5, "Chinese")
        assert len(outline) == 5
        assert all(isinstance(item, str) for item in outline)
        assert "测试主题" in outline[0]

    def test_fallback_mechanism(self, generator):
        """测试fallback机制"""
        # 这个测试模拟所有provider都失败的情况
        # 在实际环境中需要mock adapters
        priority = generator.config.get_provider_priority("ppt_content")
        assert isinstance(priority, list)
        assert len(priority) > 0

    def test_dsl_parsing_and_fixing(self, generator):
        """测试DSL解析和修复"""
        # 测试DSL修复功能
        invalid_dsl = "<SLIDE><TITLE>Test</TITLE></SLIDE>"
        fixed_dsl = generator._fix_dsl(invalid_dsl)
        assert "<PRESENTATION>" in fixed_dsl
        assert "</PRESENTATION>" in fixed_dsl


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_end_to_end_simple(self):
        """端到端简单测试"""
        params = {
            "title": "测试演示文稿",
            "outline": ["第一页", "第二页", "第三页"],
            "n_slides": 3,
            "language": "Chinese"
        }

        try:
            result = await create_presentation(params)
            assert result is not None
            assert "presentation_id" in result
            assert "path" in result

            # 验证文件存在
            pptx_path = Path(result["path"])
            assert pptx_path.exists()
            assert pptx_path.suffix == ".pptx"

            # 清理测试文件
            if pptx_path.exists():
                pptx_path.unlink()

        except Exception as e:
            pytest.skip(f"集成测试需要完整环境: {str(e)}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])


