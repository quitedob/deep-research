#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPT生成功能设置脚本：帮助用户快速配置和验证PPT生成功能。

此脚本将：
1. 检查必要的依赖是否安装
2. 创建必需的目录结构
3. 验证环境变量配置
4. 测试基本功能是否正常工作
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error(f"需要Python 3.8或更高版本，当前版本: {version.major}.{version.minor}")
        return False
    logger.info(f"Python版本检查通过: {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """检查依赖包是否安装"""
    required_packages = [
        "fastapi", "uvicorn", "python-pptx", "jinja2",
        "aiohttp", "aiofiles", "openai", "ollama"
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            logger.info(f"✓ {package} 已安装")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"✗ {package} 未安装")

    if missing_packages:
        logger.error(f"缺少依赖包: {', '.join(missing_packages)}")
        logger.info("请运行以下命令安装依赖: pip install -r requirements.txt")
        return False

    return True


def create_directories():
    """创建必要的目录结构"""
    directories = [
        "./data/ppt_exports",
        "./data/ppt_images",
        "./data/uploads",
        "./examples_output"
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"✓ 创建目录: {directory}")


def check_environment_variables():
    """检查环境变量配置"""
    required_vars = [
        ("DEEPSEEK_API_KEY", "DeepSeek API密钥（推荐）"),
        ("OLLAMA_HOST", "Ollama服务地址（推荐）")
    ]

    optional_vars = [
        ("PEXELS_API_KEY", "Pexels图片库API密钥（用于获取配图）"),
        ("UNSPLASH_API_KEY", "Unsplash图片库API密钥（用于获取配图）")
    ]

    all_good = True

    logger.info("检查必需的环境变量:")
    for var_name, description in required_vars:
        value = os.getenv(var_name)
        if value:
            logger.info(f"✓ {var_name}: 已配置")
        else:
            logger.warning(f"✗ {var_name}: 未配置 - {description}")
            all_good = False

    logger.info("检查可选的环境变量:")
    for var_name, description in optional_vars:
        value = os.getenv(var_name)
        if value:
            logger.info(f"✓ {var_name}: 已配置")
        else:
            logger.info(f"- {var_name}: 未配置（可选）- {description}")

    return all_good


def test_basic_functionality():
    """测试基本功能"""
    try:
        logger.info("测试PPT生成器初始化...")

        # 导入并初始化生成器
        from src.core.ppt.generator import PPTGenerator
        from src.core.ppt.config import PPTConfig

        config = PPTConfig()
        generator = PPTGenerator(config)

        logger.info("✓ PPT生成器初始化成功")

        # 测试提示词构建器
        from src.core.ppt.prompt_builder import PromptBuilder

        builder = PromptBuilder()
        prompt = builder.build_outline_prompt("测试主题", 3, "chinese", "专业")

        logger.info("✓ 提示词构建器工作正常")

        # 测试渲染器初始化
        from src.core.ppt.renderer import PPTXRenderer

        renderer = PPTXRenderer()
        logger.info("✓ PPTX渲染器初始化成功")

        return True

    except Exception as e:
        logger.error(f"功能测试失败: {str(e)}")
        return False


def print_usage_guide():
    """打印使用指南"""
    print("\n" + "="*60)
    print("🎉 PPT生成功能设置完成！")
    print("="*60)

    print("\n📋 使用方法:")
    print("1. 启动服务:")
    print("   uvicorn src.serve.api:app --reload")

    print("\n2. 生成演示文稿（命令行）:")
    print("   curl -X POST 'http://localhost:8000/api/v1/ppt/presentation/create' \\")
    print("     -H 'Content-Type: application/x-www-form-urlencoded' \\")
    print("     -d 'topic=人工智能的发展前景&n_slides=5&language=chinese&tone=专业'")

    print("\n3. 生成演示文稿（Python）:")
    print("   from src.core.ppt.generator import create_presentation")
    print("   result = await create_presentation('机器学习基础', n_slides=8)")

    print("\n4. 查看生成的演示文稿:")
    print("   打开浏览器访问: http://localhost:8000")
    print("   或直接下载文件: http://localhost:8000/api/v1/ppt/presentation/{id}/download")

    print("\n🔧 配置文件位置:")
    print("   - 主配置文件: conf.yaml")
    print("   - 环境变量: .env 文件（推荐）")

    print("\n📁 输出目录:")
    print("   - 演示文稿文件: ./data/ppt_exports/")
    print("   - 图片缓存: ./data/ppt_images/")
    print("   - 示例输出: ./examples_output/")

    print("\n🧪 测试示例:")
    print("   python src/core/ppt/example_usage.py")

    print("\n💡 提示:")
    print("   - 确保DeepSeek API密钥已配置以获得最佳体验")
    print("   - 本地Ollama服务可作为免费备选方案")
    print("   - 首次运行可能需要一些时间下载模型")
    print("="*60)


def main():
    """主函数"""
    print("🚀 Deep Research PPT生成功能设置向导")
    print("="*60)

    # 检查Python版本
    if not check_python_version():
        sys.exit(1)

    # 检查依赖
    if not check_dependencies():
        print("\n❌ 请先安装依赖包: pip install -r requirements.txt")
        sys.exit(1)

    # 创建目录
    create_directories()

    # 检查环境变量
    env_ok = check_environment_variables()

    # 测试基本功能
    if not test_basic_functionality():
        print("\n❌ 基本功能测试失败，请检查配置")
        sys.exit(1)

    # 打印使用指南
    print_usage_guide()

    if not env_ok:
        print("\n⚠️  警告: 部分环境变量未配置，某些功能可能受限")
        print("   请参考README.md配置相关环境变量")
    else:
        print("\n✅ 设置完成！所有功能都已就绪")


if __name__ == "__main__":
    main()
