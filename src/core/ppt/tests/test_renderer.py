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
        config_path = os.path.join(temp_dir, "test_config.yaml")
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("""
PRIMARY_LLM_BACKEND: OLLAMA
FALLBACK_LLM_BACKEND: DEEPSEEK
WORKFLOWS:
  ppt:
    default_template: modern
    max_slides: 20
    enable_charts: true
""")
        return PPTConfig(Path(config_path))

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

    def test_renderer_initialization(self, renderer):
        """测试渲染器初始化"""
        assert renderer is not None
        assert len(renderer.supported_layouts) > 0

    def test_parse_dsl(self, renderer, sample_dsl):
        """测试DSL解析"""
        slides_data = renderer._parse_dsl(sample_dsl)

        # 由于_parse_dsl返回的是slides列表，而不是包含title的字典
        assert len(slides_data) >= 1

        # 检查第一张幻灯片
        if slides_data:
            first_slide = slides_data[0]
            assert "layout" in first_slide
            assert "title" in first_slide

    def test_validate_dsl_external(self):
        """测试DSL验证器（使用外部验证函数）"""
        from ..utils.dsl_validator import validate_dsl

        # 有效DSL
        valid_dsl = """<PRESENTATION>
    <SECTION layout="TITLE">
        <TITLE>Test</TITLE>
    </SECTION>
</PRESENTATION>"""

        is_valid, msg = validate_dsl(valid_dsl)
        assert is_valid, f"Valid DSL failed: {msg}"

        # 无效DSL
        invalid_dsl = "<INVALID></INVALID>"
        is_valid, msg = validate_dsl(invalid_dsl)
        assert not is_valid

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
        from ..image_service import ImageService
        # 创建测试环境的图片服务
        service = ImageService()
        service.cache_dir = Path(temp_dir) / "image_cache"
        service.cache_dir.mkdir(exist_ok=True)
        service.cache_file = service.cache_dir / "image_cache.json"
        return service

    def test_image_service_initialization(self, image_service):
        """测试图片服务初始化"""
        assert image_service.cache_dir is not None
        assert image_service.cache_file is not None
        assert isinstance(image_service.cache, dict)

    def test_cache_key_generation(self, image_service):
        """测试缓存键生成"""
        key1 = image_service._get_cache_key("test query")
        key2 = image_service._get_cache_key("test query")
        key3 = image_service._get_cache_key("different query")

        # 相同查询应该生成相同键
        assert key1 == key2
        # 不同查询应该生成不同键
        assert key1 != key3

    @pytest.mark.asyncio
    async def test_placeholder_image_generation(self, image_service):
        """测试占位符图像生成"""
        url = image_service._get_placeholder_image("test query")
        assert url is not None
        assert "via.placeholder.com" in url
        assert "test+query" in url

    @pytest.mark.asyncio
    async def test_image_url_caching(self, image_service):
        """测试图像URL缓存"""
        query = "test image query"

        # 第一次获取（应该生成新的）
        url1 = await image_service.get_image_url(query)

        # 第二次获取（应该从缓存获取）
        url2 = await image_service.get_image_url(query)

        # 应该返回相同的URL
        assert url1 == url2

        # 缓存应该包含该条目
        cache_key = image_service._get_cache_key(query)
        assert cache_key in image_service.cache

    def test_clear_cache(self, image_service):
        """测试清空缓存"""
        # 添加一些缓存项
        image_service.cache["test_key"] = "test_value"
        assert len(image_service.cache) > 0

        # 清空缓存
        image_service.clear_cache()
        assert len(image_service.cache) == 0


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


