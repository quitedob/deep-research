# -*- coding: utf-8 -*-
"""
PPT生成器主流程

协调prompt构建、provider路由、DSL验证和渲染的完整流程。
"""

import logging
import uuid
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .config import get_ppt_config
from .prompt_builder import get_prompt_builder
from .adapters.deepseek_adapter import DeepSeekAdapter
from .adapters.ollama_adapter import OllamaAdapter
from .renderer import PPTXRenderer
from .utils.dsl_validator import validate_dsl

logger = logging.getLogger(__name__)


class PPTGenerator:
    """PPT生成器类"""

    def __init__(self):
        """初始化生成器"""
        self.config = get_ppt_config()
        self.prompt_builder = get_prompt_builder()
        self.renderer = PPTXRenderer()

        # 初始化adapters
        self.adapters = {
            "deepseek": DeepSeekAdapter(),
            "ollama": OllamaAdapter()
        }

        # 输出目录
        self.output_dir = Path("./output_reports/ppt")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def create_presentation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建演示文稿

        参数:
            params: 包含以下字段的字典
                - title: 标题
                - outline: 大纲列表（可选）
                - topic: 主题（如果没有outline）
                - n_slides: 幻灯片数量
                - language: 语言（默认Chinese）
                - tone: 语气（默认professional）
                - template: 模板名称（可选）

        返回:
            包含presentation_id, path, edit_path的字典
        """
        presentation_id = str(uuid.uuid4())
        logger.info(f"开始生成PPT: {presentation_id}")

        try:
            # 1. 提取参数
            title = params.get("title", "未命名演示文稿")
            outline = params.get("outline")
            topic = params.get("topic", title)
            n_slides = params.get("n_slides", 10)
            language = params.get("language", "Chinese")
            tone = params.get("tone", "professional")
            template = params.get("template")

            # 2. 如果没有outline，先生成outline
            if not outline:
                logger.info("未提供大纲，开始生成大纲...")
                outline = await self._generate_outline(topic, n_slides, language)

            # 3. 构建prompt
            logger.info("构建生成prompt...")
            prompt = self.prompt_builder.build_presentation_prompt(
                title=title,
                outline=outline,
                n_slides=n_slides,
                language=language,
                tone=tone
            )

            # 4. 使用provider生成DSL
            logger.info("调用LLM生成DSL...")
            dsl_content = await self._generate_with_fallback(
                prompt=prompt,
                task_type="ppt_content"
            )

            # 5. 验证DSL
            logger.info("验证DSL格式...")
            is_valid, error_msg = validate_dsl(dsl_content)
            if not is_valid:
                logger.warning(f"DSL验证失败: {error_msg}，尝试修复...")
                dsl_content = self._fix_dsl(dsl_content)

            # 6. 渲染为PPTX
            logger.info("渲染PPTX文件...")
            pptx_path = await self.renderer.render_dsl_to_pptx(
                dsl_content=dsl_content,
                title=title,
                template=template,
                output_dir=self.output_dir,
                presentation_id=presentation_id
            )

            # 7. 返回结果
            result = {
                "presentation_id": presentation_id,
                "path": str(pptx_path),
                "edit_path": f"/presentation?id={presentation_id}",
                "title": title,
                "slides_count": n_slides,
                "created_at": datetime.now().isoformat()
            }

            logger.info(f"PPT生成成功: {pptx_path}")
            return result

        except Exception as e:
            logger.error(f"PPT生成失败: {str(e)}", exc_info=True)
            raise Exception(f"PPT生成失败: {str(e)}")

    async def _generate_outline(
        self,
        topic: str,
        n_slides: int,
        language: str
    ) -> List[str]:
        """
        生成演示文稿大纲

        参数:
            topic: 主题
            n_slides: 幻灯片数量
            language: 语言

        返回:
            大纲列表
        """
        prompt = self.prompt_builder.build_outline_prompt(topic, n_slides, language)

        try:
            response = await self._generate_with_fallback(
                prompt=prompt,
                task_type="ppt_outline"
            )

            # 尝试解析JSON
            try:
                outline_data = json.loads(response)
                if isinstance(outline_data, list):
                    return [item.get("title", "") for item in outline_data if item.get("title")]
            except json.JSONDecodeError:
                pass

            # 如果JSON解析失败，尝试从文本中提取
            lines = response.strip().split("\n")
            outline = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("[") and not line.startswith("{"):
                    # 移除序号和特殊字符
                    cleaned = line.lstrip("0123456789.-*• ")
                    if cleaned:
                        outline.append(cleaned)

            if outline:
                return outline[:n_slides]

            # 如果都失败，返回默认大纲
            return self._get_default_outline(topic, n_slides, language)

        except Exception as e:
            logger.error(f"生成大纲失败: {str(e)}")
            return self._get_default_outline(topic, n_slides, language)

    def _get_default_outline(self, topic: str, n_slides: int, language: str) -> List[str]:
        """获取默认大纲"""
        if language == "Chinese":
            return [
                f"{topic} - 概述",
                "背景介绍",
                "核心概念",
                "关键要点",
                "实际应用",
                "案例分析",
                "优势与挑战",
                "未来展望",
                "总结",
                "Q&A"
            ][:n_slides]
        else:
            return [
                f"{topic} - Overview",
                "Background",
                "Core Concepts",
                "Key Points",
                "Applications",
                "Case Studies",
                "Advantages & Challenges",
                "Future Outlook",
                "Summary",
                "Q&A"
            ][:n_slides]

    async def _generate_with_fallback(
        self,
        prompt: str,
        task_type: str
    ) -> str:
        """
        使用fallback机制生成内容

        参数:
            prompt: 提示词
            task_type: 任务类型

        返回:
            生成的内容
        """
        # 获取provider优先级
        priority = self.config.get_provider_priority(task_type)

        last_error = None
        for provider_name in priority:
            if not self.config.is_provider_enabled(provider_name):
                logger.info(f"Provider {provider_name} 未启用，跳过")
                continue

            try:
                logger.info(f"尝试使用provider: {provider_name}")
                adapter = self.adapters.get(provider_name)

                if not adapter:
                    logger.warning(f"Provider {provider_name} 的adapter未找到")
                    continue

                # 健康检查
                is_healthy, health_msg = await adapter.health_check()
                if not is_healthy:
                    logger.warning(f"Provider {provider_name} 健康检查失败: {health_msg}")
                    continue

                # 生成内容
                if provider_name == "deepseek":
                    # DeepSeek使用chat模式
                    messages = [{"role": "user", "content": prompt}]
                    content = await adapter.generate(prompt, temperature=1.0)
                else:
                    # Ollama使用generate模式
                    content = await adapter.generate(prompt, temperature=0.7)

                if content:
                    logger.info(f"使用provider {provider_name} 生成成功")
                    return content

            except Exception as e:
                logger.error(f"Provider {provider_name} 生成失败: {str(e)}")
                last_error = e
                continue

        # 所有provider都失败
        error_msg = f"所有provider都失败，最后错误: {str(last_error)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    def _fix_dsl(self, dsl_content: str) -> str:
        """
        尝试修复DSL格式

        参数:
            dsl_content: 原始DSL内容

        返回:
            修复后的DSL内容
        """
        # 简单的修复策略：确保有PRESENTATION标签
        if "<PRESENTATION>" not in dsl_content:
            dsl_content = f"<PRESENTATION>\n{dsl_content}\n</PRESENTATION>"

        return dsl_content


# 全局实例
_generator: Optional[PPTGenerator] = None


async def create_presentation(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建演示文稿（便捷函数）

    参数:
        params: 参数字典

    返回:
        结果字典
    """
    global _generator
    if _generator is None:
        _generator = PPTGenerator()

    return await _generator.create_presentation(params)
