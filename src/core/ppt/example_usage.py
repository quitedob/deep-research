#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPT生成模块使用示例：演示如何使用deep-research的PPT生成功能。

此脚本展示了：
1. 基本演示文稿生成
2. 自定义参数生成
3. 批量生成演示文稿
4. 与现有系统的集成

使用前请确保：
1. 配置好环境变量（DEEPSEEK_API_KEY等）
2. 安装所需的依赖包
3. 确保Ollama服务正在运行（如果使用本地模型）
"""

import os
import asyncio
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from src.core.ppt.generator import PPTGenerator, GenerationRequest
from src.core.ppt.config import PPTConfig


async def basic_example():
    """基本使用示例"""
    logger.info("=== 基本使用示例 ===")

    # 创建生成请求
    request = GenerationRequest(
        topic="人工智能的发展前景",
        n_slides=5,
        language="chinese",
        tone="专业"
    )

    # 生成演示文稿
    generator = PPTGenerator()
    result = await generator.create_presentation(request)

    if result.success:
        logger.info(f"演示文稿生成成功！")
        logger.info(f"文件路径: {result.pptx_path}")
        logger.info(f"生成ID: {result.presentation_id}")
        logger.info(f"元数据: {result.metadata}")
    else:
        logger.error(f"演示文稿生成失败: {result.error_message}")

    return result


async def custom_example():
    """自定义参数示例"""
    logger.info("=== 自定义参数示例 ===")

    # 使用自定义配置
    config = PPTConfig(
        provider_priority=["ollama", "deepseek"],  # 优先使用本地模型
        output_dir="./examples_output"
    )

    request = GenerationRequest(
        topic="机器学习在医疗健康领域的应用",
        n_slides=8,
        language="chinese",
        tone="学术",
        template="classic",
        outline=[
            "引言：医疗AI的发展现状",
            "核心技术：机器学习算法",
            "应用案例：疾病诊断",
            "应用案例：药物研发",
            "挑战与机遇",
            "未来发展趋势",
            "结论与展望"
        ]
    )

    generator = PPTGenerator(config)
    result = await generator.create_presentation(request)

    if result.success:
        logger.info("自定义演示文稿生成成功！")
        logger.info(f"文件路径: {result.pptx_path}")

        # 验证文件是否存在且大小合理
        if os.path.exists(result.pptx_path):
            file_size = os.path.getsize(result.pptx_path)
            logger.info(f"文件大小: {file_size} bytes")

    return result


async def batch_example():
    """批量生成示例"""
    logger.info("=== 批量生成示例 ===")

    topics = [
        "可持续发展与绿色能源",
        "区块链技术的商业应用",
        "5G网络的发展趋势",
        "智能制造的未来展望"
    ]

    generator = PPTGenerator()
    results = []

    for topic in topics:
        logger.info(f"生成演示文稿: {topic}")

        request = GenerationRequest(
            topic=topic,
            n_slides=4,
            language="chinese",
            tone="专业"
        )

        result = await generator.create_presentation(request)
        results.append((topic, result))

        # 添加小延迟避免API限流
        await asyncio.sleep(1)

    # 统计结果
    success_count = sum(1 for _, result in results if result.success)
    logger.info(f"批量生成完成: {success_count}/{len(topics)} 成功")

    return results


async def api_integration_example():
    """API集成示例"""
    logger.info("=== API集成示例 ===")

    # 模拟API调用的方式
    from fastapi import FastAPI
    from src.core.ppt.api.routes import router

    # 这里只是展示如何集成到FastAPI应用中
    # app = FastAPI()
    # app.include_router(router, prefix="/api/v1")

    # 模拟API请求参数
    api_params = {
        "topic": "量子计算的原理与应用",
        "n_slides": 6,
        "language": "chinese",
        "tone": "科普"
    }

    # 转换为内部格式
    request = GenerationRequest(**api_params)

    generator = PPTGenerator()
    result = await generator.create_presentation(request)

    if result.success:
        logger.info("API集成演示文稿生成成功！")
        logger.info(f"可以通过以下方式下载: /api/v1/ppt/presentation/{result.presentation_id}/download")

    return result


async def main():
    """主函数：运行所有示例"""
    logger.info("开始PPT生成功能演示")

    # 确保输出目录存在
    os.makedirs("./examples_output", exist_ok=True)

    try:
        # 运行基本示例
        await basic_example()
        print("\n" + "="*50 + "\n")

        # 运行自定义示例
        await custom_example()
        print("\n" + "="*50 + "\n")

        # 运行批量示例
        await batch_example()
        print("\n" + "="*50 + "\n")

        # 运行API集成示例
        await api_integration_example()

    except KeyboardInterrupt:
        logger.info("演示被用户中断")
    except Exception as e:
        logger.error(f"演示过程中出错: {str(e)}")
        raise
    finally:
        logger.info("PPT生成功能演示完成")


if __name__ == "__main__":
    # 设置环境变量（示例）
    os.environ.setdefault("DEEPSEEK_API_KEY", "your_api_key_here")
    os.environ.setdefault("OLLAMA_HOST", "http://localhost:11434")
    os.environ.setdefault("OLLAMA_PPT_MODEL", "llama3.2:3b")

    # 运行异步主函数
    asyncio.run(main())
