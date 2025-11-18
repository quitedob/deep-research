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

# Ollama 图像分析器（内嵌实现）
class OllamaImageAnalyzer:
    """Ollama 图像分析器"""

    def __init__(self, host='http://localhost:11434'):
        self.host = host.rstrip('/')
        self.timeout = None  # 将在使用时设置

    def _encode_image_to_base64(self, image_path: str) -> str:
        """将图像文件编码为base64格式"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    async def analyze_image(self, model: str, image_path: str, prompt: str) -> dict:
        """使用指定模型分析图像"""
        import aiohttp
        
        image_b64 = self._encode_image_to_base64(image_path)

        data = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_b64]
                }
            ],
            "stream": False
        }

        url = f"{self.host}/api/chat"
        timeout = aiohttp.ClientTimeout(total=300)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API错误: {response.status} - {error_text}")
                return await response.json()


class ImageAnalysisTool:
    """
    图像分析工具
    使用Ollama的gemma3:4b模型进行多模态图像分析
    """

    def __init__(self, host: str = 'http://localhost:11434', model: str = 'gemma3:4b'):
        """
        初始化图像分析工具

        Args:
            host: Ollama服务地址
            model: 使用的模型名称，默认为gemma3:4b
        """
        if OllamaImageAnalyzer is None:
            raise ImportError(
                "OllamaImageAnalyzer 未找到。请确保 testollama.py 文件存在于 test 目录中。"
            )
        self.analyzer = OllamaImageAnalyzer(host=host)
        self.model = model

    async def analyze_image(
        self,
        image_path: str,
        prompt: str = "请详细分析这张图片的内容"
    ) -> ToolResponse:
        """
        分析图像内容

        Args:
            image_path: 图像文件路径
            prompt: 分析提示词

        Returns:
            图像分析结果的ToolResponse
        """
        try:
            if not os.path.exists(image_path):
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"图像文件不存在: {image_path}"
                    )])

            # 执行图像分析
            result = await self.analyzer.analyze_image(
                model=self.model,
                image_path=image_path,
                prompt=prompt
            )

            if result and "message" in result and "content" in result["message"]:
                analysis_content = result["message"]["content"]
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=analysis_content
                    )])
            else:
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text="图像分析失败，未获取到有效结果"
                    )])

        except Exception as e:
            error_msg = f"图像分析失败: {str(e)}"
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=error_msg
                )])

    async def analyze_multiple_images(
        self,
        image_paths: List[str],
        prompt: str = "请分析这些图片之间的关系和共同点"
    ) -> ToolResponse:
        """
        分析多张图像

        Args:
            image_paths: 图像文件路径列表
            prompt: 分析提示词

        Returns:
            多图分析结果的ToolResponse
        """
        try:
            if not image_paths:
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text="未提供图像文件路径"
                    )])

            # 检查所有文件是否存在
            missing_files = [path for path in image_paths if not os.path.exists(path)]
            if missing_files:
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"以下图像文件不存在: {', '.join(missing_files)}"
                    )])

            analysis_results = []
            combined_prompt = f"分析提示: {prompt}\n\n"

            for i, image_path in enumerate(image_paths):
                try:
                    single_prompt = f"请分析第{i+1}张图片: {prompt}"
                    result = await self.analyze.analyze_image(
                        model=self.model,
                        image_path=image_path,
                        prompt=single_prompt
                    )

                    if result and "message" in result and "content" in result["message"]:
                        content = result["message"]["content"]
                        analysis_results.append(f"图片 {i+1} ({os.path.basename(image_path)}):\n{content}")
                    else:
                        analysis_results.append(f"图片 {i+1} 分析失败")

                    # 添加延时避免请求过于频繁
                    await asyncio.sleep(1)

                except Exception as e:
                    analysis_results.append(f"图片 {i+1} 分析异常: {str(e)}")

            # 如果有多张图片，尝试比较分析
            if len(image_paths) > 1:
                comparison_prompt = f"{prompt}\n\n请特别关注这些图片之间的关系、差异和共同点。"
                # 这里可以实现更复杂的比较分析逻辑

            final_content = f"多图分析结果:\n\n" + "\n\n".join(analysis_results)

            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=final_content
                )])

        except Exception as e:
            error_msg = f"多图分析失败: {str(e)}"
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=error_msg
                )])

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


def register_image_analysis_tools(toolkit, host: str = 'http://localhost:11434', model: str = 'gemma3:4b'):
    """
    注册图像分析相关工具到工具包

    Args:
        toolkit: AgentScope工具包
        host: Ollama服务地址
        model: 使用的模型名称
    """
    # 检查 OllamaImageAnalyzer 是否可用
    if OllamaImageAnalyzer is None:
        print("警告: OllamaImageAnalyzer 不可用，跳过图像分析工具注册")
        return
    
    try:
        image_tool = ImageAnalysisTool(host=host, model=model)
    except Exception as e:
        print(f"警告: 无法初始化图像分析工具: {e}")
        return

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