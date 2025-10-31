#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPT模块使用示例

演示如何使用PPT生成模块创建演示文稿。
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.core.ppt.generator import create_presentation
from src.core.ppt.config import get_ppt_config
from src.core.ppt.prompt_builder import get_prompt_builder
from src.core.ppt.image_service import get_image_service
from src.core.ppt.utils.dsl_validator import validate_dsl

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_basic_ppt():
    """基础PPT生成示例"""
    logger.info("开始基础PPT生成示例...")

    params = {
        "title": "人工智能技术发展报告",
        "outline": [
            "AI技术概述",
            "机器学习核心算法",
            "深度学习突破",
            "实际应用案例",
            "未来发展趋势"
        ],
        "n_slides": 5,
        "language": "Chinese",
        "tone": "professional"
    }

    try:
        result = await create_presentation(params)
        logger.info(f"PPT生成成功: {result['path']}")
        logger.info(f"演示文稿ID: {result['presentation_id']}")
        logger.info(f"编辑链接: {result['edit_path']}")
        return result
    except Exception as e:
        logger.error(f"PPT生成失败: {e}")
        return None


async def example_topic_based_ppt():
    """基于主题的PPT生成示例"""
    logger.info("开始基于主题的PPT生成示例...")

    params = {
        "title": "量子计算技术介绍",
        "topic": "量子计算基础原理和应用前景",
        "n_slides": 8,
        "language": "Chinese",
        "tone": "educational"
    }

    try:
        result = await create_presentation(params)
        logger.info(f"基于主题的PPT生成成功: {result['path']}")
        return result
    except Exception as e:
        logger.error(f"基于主题的PPT生成失败: {e}")
        return None


async def example_english_ppt():
    """英文PPT生成示例"""
    logger.info("开始英文PPT生成示例...")

    params = {
        "title": "Machine Learning Fundamentals",
        "outline": [
            "Introduction to ML",
            "Supervised Learning",
            "Unsupervised Learning",
            "Neural Networks",
            "Real-world Applications"
        ],
        "n_slides": 5,
        "language": "English",
        "tone": "academic"
    }

    try:
        result = await create_presentation(params)
        logger.info(f"英文PPT生成成功: {result['path']}")
        return result
    except Exception as e:
        logger.error(f"英文PPT生成失败: {e}")
        return None


def example_config_usage():
    """配置使用示例"""
    logger.info("配置使用示例...")

    config = get_ppt_config()

    # 获取provider优先级
    priority = config.get_provider_priority("ppt_content")
    logger.info(f"PPT内容生成provider优先级: {priority}")

    # 获取DeepSeek配置
    deepseek_config = config.get_deepseek_config()
    logger.info(f"DeepSeek模型: {deepseek_config['models']}")

    # 获取Ollama配置
    ollama_config = config.get_ollama_config()
    logger.info(f"Ollama模型: {ollama_config['small_model']}, {ollama_config['large_model']}")

    # 检查provider是否启用
    for provider in ["deepseek", "ollama"]:
        enabled = config.is_provider_enabled(provider)
        logger.info(f"Provider {provider}: {'已启用' if enabled else '未启用'}")


def example_prompt_builder():
    """Prompt构建器示例"""
    logger.info("Prompt构建器示例...")

    builder = get_prompt_builder()

    # 构建演示文稿prompt
    prompt = builder.build_presentation_prompt(
        title="区块链技术原理",
        outline=["基础概念", "技术架构", "应用场景", "挑战与机遇"],
        n_slides=4,
        language="Chinese",
        tone="technical"
    )

    logger.info(f"生成的prompt长度: {len(prompt)} 字符")

    # 构建大纲prompt
    outline_prompt = builder.build_outline_prompt(
        topic="可持续发展",
        n_slides=6,
        language="Chinese"
    )

    logger.info(f"大纲prompt长度: {len(outline_prompt)} 字符")


async def example_image_service():
    """图像服务示例"""
    logger.info("图像服务示例...")

    image_service = get_image_service()

    # 获取占位符图像
    placeholder_url = image_service._get_placeholder_image("技术概念图")
    logger.info(f"占位符图像URL: {placeholder_url}")

    # 测试缓存功能
    cache_key = image_service._get_cache_key("test query")
    logger.info(f"缓存键: {cache_key}")

    # 清空缓存（可选）
    # image_service.clear_cache()


def example_dsl_validation():
    """DSL验证示例"""
    logger.info("DSL验证示例...")

    # 有效的DSL
    valid_dsl = """<PRESENTATION>
    <SECTION layout="TITLE">
        <TITLE>技术演示</TITLE>
        <SUBTITLE>副标题</SUBTITLE>
    </SECTION>
    <SECTION layout="BULLETS">
        <TITLE>要点</TITLE>
        <CONTENT>
            <BULLET>第一点</BULLET>
            <BULLET>第二点</BULLET>
        </CONTENT>
    </SECTION>
</PRESENTATION>"""

    is_valid, msg = validate_dsl(valid_dsl)
    logger.info(f"有效DSL验证结果: {is_valid}, 消息: {msg}")

    # 无效的DSL
    invalid_dsl = "<INVALID>test</INVALID>"
    is_valid, msg = validate_dsl(invalid_dsl)
    logger.info(f"无效DSL验证结果: {is_valid}, 消息: {msg}")


async def main():
    """主函数 - 运行所有示例"""
    logger.info("开始PPT模块使用示例...")

    # 配置示例
    example_config_usage()
    print("\n" + "="*50 + "\n")

    # Prompt构建器示例
    example_prompt_builder()
    print("\n" + "="*50 + "\n")

    # 图像服务示例
    await example_image_service()
    print("\n" + "="*50 + "\n")

    # DSL验证示例
    example_dsl_validation()
    print("\n" + "="*50 + "\n")

    # 基础PPT生成（需要API密钥）
    logger.info("注意: 以下示例需要配置相应的API密钥")

    # 取消注释以运行实际PPT生成示例
    # await example_basic_ppt()
    # await example_topic_based_ppt()
    # await example_english_ppt()

    logger.info("示例演示完成！")


if __name__ == "__main__":
    asyncio.run(main())