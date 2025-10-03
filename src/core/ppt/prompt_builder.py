# -*- coding: utf-8 -*-
"""
Prompt构建器

将用户输入转换为LLM prompt，支持不同provider的消息格式。
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from jinja2 import Template

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Prompt构建器类"""

    def __init__(self):
        """初始化Prompt构建器"""
        self.template_path = Path(__file__).parent / "templates" / "slides_template.xml.j2"
        self.template = self._load_template()

    def _load_template(self) -> Template:
        """加载Jinja2模板"""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
                return Template(template_content)
        except Exception as e:
            logger.error(f"加载模板失败: {str(e)}")
            # 返回一个简单的默认模板
            return Template("Generate a presentation about {{ TITLE }}")

    def build_presentation_prompt(
        self,
        title: str,
        outline: List[str],
        n_slides: int,
        language: str = "Chinese",
        tone: str = "professional"
    ) -> str:
        """
        构建演示文稿生成prompt

        参数:
            title: 演示文稿标题
            outline: 大纲列表
            n_slides: 幻灯片数量
            language: 语言（Chinese/English）
            tone: 语气（professional/casual/creative）

        返回:
            完整的prompt字符串
        """
        # 格式化大纲
        outline_formatted = "\n".join([f"- {item}" for item in outline])

        # 渲染模板
        try:
            prompt = self.template.render(
                TITLE=title,
                OUTLINE_FORMATTED=outline_formatted,
                LANGUAGE=language,
                TONE=tone,
                TOTAL_SLIDES=n_slides
            )
            return prompt
        except Exception as e:
            logger.error(f"渲染模板失败: {str(e)}")
            # 返回一个简单的fallback prompt
            return self._build_fallback_prompt(title, outline, n_slides, language, tone)

    def _build_fallback_prompt(
        self,
        title: str,
        outline: List[str],
        n_slides: int,
        language: str,
        tone: str
    ) -> str:
        """构建简单的fallback prompt"""
        outline_text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(outline)])

        return f"""Create a professional presentation with the following details:

Title: {title}
Language: {language}
Tone: {tone}
Number of Slides: {n_slides}

Outline:
{outline_text}

Generate a complete presentation with varied slide layouts including:
- Title slide
- Content slides with bullet points
- Visual slides with images
- Summary slide

Each slide should be concise and professional."""

    def build_outline_prompt(
        self,
        topic: str,
        n_slides: int,
        language: str = "Chinese"
    ) -> str:
        """
        构建大纲生成prompt

        参数:
            topic: 主题
            n_slides: 幻灯片数量
            language: 语言

        返回:
            大纲生成prompt
        """
        if language == "Chinese":
            prompt = f"""请为以下主题生成一个专业的演示文稿大纲：

主题：{topic}
幻灯片数量：{n_slides}

要求：
1. 生成{n_slides}个幻灯片的标题和简要描述
2. 确保逻辑清晰，结构合理
3. 包含引言、主体内容和总结
4. 每个幻灯片标题简洁明了

请以JSON格式输出，格式如下：
[
  {{"title": "标题1", "description": "简要描述"}},
  {{"title": "标题2", "description": "简要描述"}},
  ...
]"""
        else:
            prompt = f"""Generate a professional presentation outline for the following topic:

Topic: {topic}
Number of Slides: {n_slides}

Requirements:
1. Generate {n_slides} slide titles with brief descriptions
2. Ensure logical flow and clear structure
3. Include introduction, main content, and conclusion
4. Keep titles concise and clear

Output in JSON format:
[
  {{"title": "Title 1", "description": "Brief description"}},
  {{"title": "Title 2", "description": "Brief description"}},
  ...
]"""

        return prompt

    def build_slide_content_prompt(
        self,
        slide_title: str,
        slide_description: str,
        main_topic: str,
        language: str = "Chinese"
    ) -> str:
        """
        构建单页内容生成prompt

        参数:
            slide_title: 幻灯片标题
            slide_description: 幻灯片描述
            main_topic: 主题
            language: 语言

        返回:
            单页内容生成prompt
        """
        if language == "Chinese":
            prompt = f"""为演示文稿生成单页内容：

主题：{main_topic}
幻灯片标题：{slide_title}
描述：{slide_description}

要求：
1. 生成3-5个要点
2. 每个要点简洁明了（不超过20字）
3. 内容专业、准确
4. 符合整体主题

请以Markdown格式输出：
# {slide_title}

- 要点1
- 要点2
- 要点3
"""
        else:
            prompt = f"""Generate slide content for a presentation:

Topic: {main_topic}
Slide Title: {slide_title}
Description: {slide_description}

Requirements:
1. Generate 3-5 bullet points
2. Keep each point concise (max 20 words)
3. Professional and accurate content
4. Align with the main topic

Output in Markdown format:
# {slide_title}

- Point 1
- Point 2
- Point 3
"""

        return prompt

    def format_for_provider(
        self,
        prompt: str,
        provider: str,
        system_message: Optional[str] = None
    ) -> Any:
        """
        将prompt格式化为特定provider的消息格式

        参数:
            prompt: 原始prompt
            provider: provider名称（deepseek/ollama）
            system_message: 系统消息（可选）

        返回:
            格式化后的消息（字符串或消息列表）
        """
        if provider == "deepseek":
            # DeepSeek使用OpenAI风格的消息格式
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            return messages

        elif provider == "ollama":
            # Ollama可以使用简单的字符串prompt
            if system_message:
                return f"{system_message}\n\n{prompt}"
            return prompt

        else:
            # 默认返回原始prompt
            return prompt


# 全局实例
_prompt_builder: Optional[PromptBuilder] = None


def get_prompt_builder() -> PromptBuilder:
    """获取PromptBuilder实例（单例模式）"""
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder
