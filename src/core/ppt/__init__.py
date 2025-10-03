# -*- coding: utf-8 -*-
"""
PPT生成模块

提供AI驱动的PPT生成功能，支持多种LLM提供商。
"""

from .generator import create_presentation, PPTGenerator
from .config import get_ppt_config, PPTConfig
from .renderer import PPTXRenderer, get_renderer
from .prompt_builder import PromptBuilder, get_prompt_builder
from .image_service import ImageService, get_image_service

__all__ = [
    "create_presentation",
    "PPTGenerator",
    "get_ppt_config",
    "PPTConfig",
    "PPTXRenderer",
    "get_renderer",
    "PromptBuilder",
    "get_prompt_builder",
    "ImageService",
    "get_image_service"
]

__version__ = "1.0.0"
