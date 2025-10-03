# -*- coding: utf-8 -*-
"""
PPTX渲染器测试：测试DSL到PPTX的转换功能。
"""

import os
import pytest
import tempfile
from unittest.mock import Mock, patch

from ..renderer import PPTXRenderer
from ..config import PPTConfig


class TestPPTXRenderer:
    """PPTX渲染器测试类"""

    @pytest.fixture
    def temp_dir(self):
        """临时目录fixture"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def config(self, temp_dir):
        """测试配置fixture"""
        return PPTConfig(
            output_dir=os.path.join(temp_dir, "output"),
            image_cache_dir=os.path.join(temp_dir, "images")
        )

    @pytest.fixture
    def renderer(self):
        """渲染器fixture"""
        return PPTXRenderer()

    @pytest.fixture
    def sample_dsl(self):
        """示例DSL fixture"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<PRESENTATION>
    <METADATA>
        <TITLE>测试演示文稿</TITLE>
        <LANGUAGE>chinese</LANGUAGE>
        <TONE>专业</TONE>
        <TOTAL_SLIDES>3</TOTAL_SLIDES>
    </METADATA>
    <SLIDES>
        <SLIDE>
            <LAYOUT>title</LAYOUT>
            <TITLE>欢迎来到演示文稿</TITLE>
            <SUBTITLE>专业呈现</SUBTITLE>
            <CONTENT>让我们开始精彩的旅程</CONTENT>
            <IMAGE_QUERY>professional business presentation background</IMAGE_QUERY>
        </SLIDE>
        <SLIDE>
            <LAYOUT>content</LAYOUT>
            <TITLE>主要内容</TITLE>
            <CONTENT>• 第一点内容<br/>• 第二点内容<br/>• 第三点内容</CONTENT>
            <IMAGE_QUERY>business infographic data visualization</IMAGE_QUERY>
        </SLIDE>
        <SLIDE>
            <LAYOUT>conclusion</LAYOUT>
            <TITLE>总结</TITLE>
            <CONTENT>感谢您的观看</CONTENT>
            <IMAGE_QUERY>inspiring conclusion with call to action</IMAGE_QUERY>
        </SLIDE>
    </SLIDES>
</PRESENTATION>"""

    def test_renderer_initialization(self):
        """测试渲染器初始化"""
        renderer = PPTXRenderer()
        assert renderer.image_service is not None
        assert len(renderer.supported_layouts) > 0

    def test_parse_dsl(self, renderer, sample_dsl):
        """测试DSL解析"""
        data = renderer._parse_dsl(sample_dsl)

        assert data["title"] == "测试演示文稿"
        assert data["language"] == "chinese"
        assert data["total_slides"] == 3
        assert len(data["slides"]) == 3

        # 检查第一张幻灯片
        first_slide = data["slides"][0]
        assert first_slide["layout"] == "title"
        assert first_slide["title"] == "欢迎来到演示文稿"

    def test_parse_slide_element(self, renderer):
        """测试幻灯片元素解析"""
        # 这里可以测试_parse_slide_element方法
        pass

    def test_validate_dsl(self, renderer):
        """测试DSL验证"""
        # 有效DSL
        valid_dsl = """<?xml version="1.0"?>
<PRESENTATION>
    <METADATA><TITLE>Test</TITLE><TOTAL_SLIDES>1</TOTAL_SLIDES></METADATA>
    <SLIDES><SLIDE><LAYOUT>title</LAYOUT></SLIDE></SLIDES>
</PRESENTATION>"""

        assert renderer._validate_dsl(valid_dsl) is True

        # 无效DSL
        invalid_dsl = "<INVALID></INVALID>"
        assert renderer._validate_dsl(invalid_dsl) is False

    @pytest.mark.skipif(
        not os.getenv("PPTX_AVAILABLE", "false").lower() == "true",
        reason="PPTX库不可用或未安装"
    )
    def test_render_pptx(self, renderer, sample_dsl, temp_dir):
        """测试PPTX渲染（需要python-pptx库）"""
        presentation_id = "test_presentation"

        # Mock图片服务避免网络调用
        with patch.object(renderer.image_service, 'get_image_for_query') as mock_get_image:
            mock_get_image.return_value = None  # 不使用真实图片

            output_path = renderer.render(sample_dsl, presentation_id)

            # 检查文件是否生成
            assert os.path.exists(output_path)
            assert output_path.endswith(".pptx")

            # 检查文件大小（应该大于0）
            assert os.path.getsize(output_path) > 0

    def test_preview_dsl_structure(self, renderer, sample_dsl):
        """测试DSL结构预览"""
        preview = renderer.preview_dsl_structure(sample_dsl)

        assert preview["title"] == "测试演示文稿"
        assert preview["total_slides"] == 3
        assert len(preview["slide_titles"]) == 3
        assert len(preview["slide_layouts"]) == 3


class TestImageService:
    """图片服务测试类"""

    @pytest.fixture
    def image_service(self, temp_dir):
        """图片服务fixture"""
        # 这里需要mock或设置测试环境
        pass

    def test_image_service_initialization(self):
        """测试图片服务初始化"""
        from ..image_service import ImageService

        service = ImageService()
        assert service.cache_dir is not None

    def test_cache_key_generation(self):
        """测试缓存键生成"""
        from ..image_service import ImageService

        service = ImageService()
        key1 = service._generate_cache_key("test query", "style1")
        key2 = service._generate_cache_key("test query", "style2")
        key3 = service._generate_cache_key("different query", "style1")

        # 相同查询不同风格应该生成不同键
        assert key1 != key2
        # 不同查询应该生成不同键
        assert key1 != key3
        # 相同查询相同风格应该生成相同键
        key1_again = service._generate_cache_key("test query", "style1")
        assert key1 == key1_again


@pytest.mark.integration
class TestRendererIntegration:
    """渲染器集成测试"""

    @pytest.mark.asyncio
    async def test_full_rendering_pipeline(self):
        """测试完整的渲染流水线"""
        # 这个测试需要完整的环境设置
        # 包括真实的DSL和PPTX渲染

        dsl_content = """<?xml version="1.0" encoding="UTF-8"?>
<PRESENTATION>
    <METADATA>
        <TITLE>集成测试演示文稿</TITLE>
        <TOTAL_SLIDES>2</TOTAL_SLIDES>
    </METADATA>
    <SLIDES>
        <SLIDE>
            <LAYOUT>title</LAYOUT>
            <TITLE>测试标题页</TITLE>
            <CONTENT>集成测试</CONTENT>
        </SLIDE>
        <SLIDE>
            <LAYOUT>content</LAYOUT>
            <TITLE>测试内容页</TITLE>
            <CONTENT>这是测试内容</CONTENT>
        </SLIDE>
    </SLIDES>
</PRESENTATION>"""

        with tempfile.TemporaryDirectory() as tmpdir:
            config = PPTConfig(
                output_dir=os.path.join(tmpdir, "output"),
                image_cache_dir=os.path.join(tmpdir, "images")
            )

            # 这里应该测试完整的流水线
            # 但由于依赖较多，这里只是框架
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
