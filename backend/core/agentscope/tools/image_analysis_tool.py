#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像分析工具
基于testollama.py的Ollama多模态图像分析功能
"""

import asyncio
import base64
import os
from typing import Any, Dict, List, Optional, Union
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock, ImageBlock

from pathlib import Path
import mimetypes
from backend.core.llm.factory import LLMFactory


class ImageAnalysisTool:
    """Analyze images with the configured vision model."""

    def __init__(self, host: Optional[str] = None, model: Optional[str] = None, llm_instance=None):
        self.llm = llm_instance or LLMFactory.create_llm(provider="deepseek", base_url=host)
        self.model = model or self.llm.model or "deepseek-flash"

    async def _image_block(self, image_path):
        path = Path(image_path)
        if not path.is_file():
            raise ValueError("Image file does not exist")
        if path.stat().st_size > 20 * 1024 * 1024:
            raise ValueError("Image exceeds 20 MB")
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if not mime.startswith("image/"):
            raise ValueError("Unsupported image type")
        image_data = await asyncio.to_thread(path.read_bytes)
        return {"type": "image_url", "image_url": {
            "url": f"data:{mime};base64,{base64.b64encode(image_data).decode('ascii')}"
        }}

    async def analyze_image(self, image_path: str, prompt: str = "请详细分析这张图片的内容") -> ToolResponse:
        """Analyze a supplied image with the configured vision model."""
        return await self.analyze_multiple_images([image_path], prompt)

    async def analyze_multiple_images(self, image_paths: List[str], prompt: str = "请分析这些图片之间的关系和共同点") -> ToolResponse:
        """Send all images together so the model can compare their contents."""
        if not image_paths or len(image_paths) > 10:
            raise ValueError("Provide between 1 and 10 images")
        blocks = [{"type": "text", "text": prompt}]
        blocks.extend(await asyncio.gather(*(self._image_block(path) for path in image_paths)))
        if self.llm.get_provider_name() == "ollama":
            messages = [{"role": "user", "content": prompt,
                         "images": [block["image_url"]["url"].split(",", 1)[1] for block in blocks[1:]]}]
        else:
            messages = [{"role": "user", "content": blocks}]
        response = await self.llm.chat_completion(messages=messages, model=self.model)
        content = response.get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            raise RuntimeError("Image analysis returned no content")
        return ToolResponse(content=[TextBlock(type="text", text=content)])

    async def extract_text_from_image(
        self,
        image_path: str
    ) -> ToolResponse:
        """
        从图像中提取文字

        Args:
            image_path: 图像文件路径

        Returns:
            文字提取结果的ToolResponse
        """
        ocr_prompt = """请仔细分析这张图片，提取其中的所有文字内容。
如果图片中包含表格、图表或结构化信息，请尽可能准确地还原其内容。
如果图片是手写文字，请尽力识别。如果是印刷文字，请确保准确提取。"""

        return await self.analyze_image(image_path, ocr_prompt)

    async def analyze_chart_or_graph(
        self,
        image_path: str
    ) -> ToolResponse:
        """
        分析图表或图形

        Args:
            image_path: 图像文件路径

        Returns:
            图表分析结果的ToolResponse
        """
        chart_prompt = """请详细分析这张图表或图形：
1. 识别图表类型（柱状图、折线图、饼图、散点图等）
2. 描述图表的主要组成部分
3. 分析数据趋势和模式
4. 提取关键数据点和数值
5. 总结图表传达的主要信息或结论
6. 如果有坐标轴，请说明其含义和刻度"""

        return await self.analyze_image(image_path, chart_prompt)

    async def analyze_scientific_diagram(
        self,
        image_path: str
    ) -> ToolResponse:
        """
        分析科学图表

        Args:
            image_path: 图像文件路径

        Returns:
            科学图表分析结果的ToolResponse
        """
        diagram_prompt = """请详细分析这张科学图表：
1. 识别图表的学科领域和类型（流程图、结构图、实验装置图、分子结构图等）
2. 解释图表中各个组件的含义
3. 描述图表展示的科学原理或实验方法
4. 如果是实验装置图，说明实验流程和关键步骤
5. 如果是理论图解，解释其科学原理
6. 提供相关的科学背景信息"""

        return await self.analyze_image(image_path, diagram_prompt)

    async def analyze_research_figure(
        self,
        image_path: str,
        context: Optional[str] = None
    ) -> ToolResponse:
        """
        分析研究论文中的图表

        Args:
            image_path: 图像文件路径
            context: 可选的上下文信息

        Returns:
            研究图表分析结果的ToolResponse
        """
        context_info = f"\n相关上下文: {context}" if context else ""
        research_prompt = f"""请作为专业研究人员，详细分析这张研究图表：{context_info}

1. 识别图表类型和研究领域
2. 分析实验设计和数据处理方法
3. 解释主要研究发现和结论
4. 讨论结果的重要性和创新性
5. 指出可能的局限性或需要注意的地方
6. 如果可能，提供对研究方法的评价
7. 总结图表对该研究领域的贡献"""

        return await self.analyze_image(image_path, research_prompt)

    def _encode_image_to_base64(self, image_path: str) -> str:
        """
        将图像文件编码为base64格式

        Args:
            image_path: 图像文件路径

        Returns:
            base64编码的图像字符串
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')


def register_image_analysis_tools(toolkit, host: Optional[str] = None, model: Optional[str] = None, llm_instance=None):
    """Register vision tools using the same configured model as the research agent."""
    image_tool = ImageAnalysisTool(host=host, model=model, llm_instance=llm_instance)

    # 注册基础图像分析
    toolkit.register_tool_function(
        image_tool.analyze_image,
        func_description="使用AI模型分析图像内容"
    )

    # 注册多图分析
    toolkit.register_tool_function(
        image_tool.analyze_multiple_images,
        func_description="分析多张图像之间的关系和内容"
    )

    # 注册文字提取
    toolkit.register_tool_function(
        image_tool.extract_text_from_image,
        func_description="从图像中提取文字内容（OCR）"
    )

    # 注册图表分析
    toolkit.register_tool_function(
        image_tool.analyze_chart_or_graph,
        func_description="分析数据图表和图形"
    )

    # 注册科学图表分析
    toolkit.register_tool_function(
        image_tool.analyze_scientific_diagram,
        func_description="分析科学图表和原理图"
    )

    # 注册研究图表分析
    toolkit.register_tool_function(
        image_tool.analyze_research_figure,
        func_description="分析研究论文中的专业图表"
    )

    return image_tool