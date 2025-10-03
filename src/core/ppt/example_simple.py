#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PPT生成模块 - 简单示例

这是一个最简单的使用示例，展示如何快速生成一个PPT。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


async def example_1_basic():
    """示例1: 基础用法 - 使用大纲生成PPT"""
    print("\n" + "="*60)
    print("示例1: 基础用法 - 使用大纲生成PPT")
    print("="*60)
    
    from src.core.ppt import create_presentation
    
    params = {
        "title": "人工智能技术概览",
        "outline": [
            "AI简介",
            "机器学习基础",
            "深度学习",
            "自然语言处理",
            "计算机视觉",
            "实际应用案例"
        ],
        "n_slides": 8,
        "language": "Chinese",
        "tone": "professional"
    }
    
    print("正在生成PPT，请稍候...")
    try:
        result = await create_presentation(params)
        print(f"\n✅ PPT生成成功！")
        print(f"📁 文件路径: {result['path']}")
        print(f"🆔 演示文稿ID: {result['presentation_id']}")
        print(f"📊 幻灯片数量: {result['slides_count']}")
        return result
    except Exception as e:
        print(f"\n❌ 生成失败: {str(e)}")
        print("\n💡 提示:")
        print("1. 确保已配置 DEEPSEEK_API_KEY 或 OLLAMA_HOST 环境变量")
        print("2. 如果使用Ollama，确保服务已启动: ollama serve")
        print("3. 检查网络连接是否正常")
        return None


async def example_2_topic_only():
    """示例2: 仅使用主题 - 自动生成大纲"""
    print("\n" + "="*60)
    print("示例2: 仅使用主题 - 自动生成大纲")
    print("="*60)
    
    from src.core.ppt import create_presentation
    
    params = {
        "title": "区块链技术入门",
        "topic": "区块链",  # 只提供主题，系统会自动生成大纲
        "n_slides": 10,
        "language": "Chinese",
        "tone": "casual"
    }
    
    print("正在生成PPT（包括自动生成大纲），请稍候...")
    try:
        result = await create_presentation(params)
        print(f"\n✅ PPT生成成功！")
        print(f"📁 文件路径: {result['path']}")
        return result
    except Exception as e:
        print(f"\n❌ 生成失败: {str(e)}")
        return None


async def example_3_english():
    """示例3: 英文演示文稿"""
    print("\n" + "="*60)
    print("示例3: 英文演示文稿")
    print("="*60)
    
    from src.core.ppt import create_presentation
    
    params = {
        "title": "Introduction to Machine Learning",
        "outline": [
            "What is Machine Learning",
            "Types of ML",
            "Supervised Learning",
            "Unsupervised Learning",
            "Deep Learning",
            "Applications"
        ],
        "n_slides": 8,
        "language": "English",
        "tone": "professional"
    }
    
    print("Generating presentation, please wait...")
    try:
        result = await create_presentation(params)
        print(f"\n✅ Presentation created successfully!")
        print(f"📁 File path: {result['path']}")
        return result
    except Exception as e:
        print(f"\n❌ Generation failed: {str(e)}")
        return None


async def example_4_creative():
    """示例4: 创意风格演示文稿"""
    print("\n" + "="*60)
    print("示例4: 创意风格演示文稿")
    print("="*60)
    
    from src.core.ppt import create_presentation
    
    params = {
        "title": "未来科技畅想",
        "topic": "未来科技",
        "n_slides": 12,
        "language": "Chinese",
        "tone": "creative"  # 创意风格
    }
    
    print("正在生成创意风格PPT，请稍候...")
    try:
        result = await create_presentation(params)
        print(f"\n✅ PPT生成成功！")
        print(f"📁 文件路径: {result['path']}")
        return result
    except Exception as e:
        print(f"\n❌ 生成失败: {str(e)}")
        return None


async def check_health():
    """检查服务健康状态"""
    print("\n" + "="*60)
    print("检查服务健康状态")
    print("="*60)
    
    from src.core.ppt.adapters.deepseek_adapter import DeepSeekAdapter
    from src.core.ppt.adapters.ollama_adapter import OllamaAdapter
    
    # 检查DeepSeek
    print("\n🔍 检查DeepSeek...")
    deepseek = DeepSeekAdapter()
    deepseek_health = await deepseek.health_check()
    if deepseek_health[0]:
        print(f"✅ DeepSeek: {deepseek_health[1]}")
    else:
        print(f"❌ DeepSeek: {deepseek_health[1]}")
    
    # 检查Ollama
    print("\n🔍 检查Ollama...")
    ollama = OllamaAdapter()
    ollama_health = await ollama.health_check()
    if ollama_health[0]:
        print(f"✅ Ollama: {ollama_health[1]}")
        models = await ollama.list_models()
        if models:
            print(f"📦 可用模型: {', '.join([m['name'] for m in models[:5]])}")
    else:
        print(f"❌ Ollama: {ollama_health[1]}")
    
    return deepseek_health[0] or ollama_health[0]


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("🎉 欢迎使用 deep-research PPT生成模块")
    print("="*60)
    
    # 先检查健康状态
    is_healthy = await check_health()
    
    if not is_healthy:
        print("\n⚠️  警告: 没有可用的LLM provider")
        print("\n请配置以下任一选项:")
        print("1. DeepSeek: 设置 DEEPSEEK_API_KEY 环境变量")
        print("2. Ollama: 启动 Ollama 服务 (ollama serve)")
        print("\n示例:")
        print("  export DEEPSEEK_API_KEY='your_api_key'")
        print("  或")
        print("  ollama serve")
        return
    
    # 运行示例
    print("\n" + "="*60)
    print("开始运行示例")
    print("="*60)
    
    # 选择要运行的示例
    print("\n请选择要运行的示例:")
    print("1. 基础用法 - 使用大纲生成PPT")
    print("2. 仅使用主题 - 自动生成大纲")
    print("3. 英文演示文稿")
    print("4. 创意风格演示文稿")
    print("5. 运行所有示例")
    print("0. 退出")
    
    try:
        choice = input("\n请输入选项 (0-5): ").strip()
        
        if choice == "1":
            await example_1_basic()
        elif choice == "2":
            await example_2_topic_only()
        elif choice == "3":
            await example_3_english()
        elif choice == "4":
            await example_4_creative()
        elif choice == "5":
            print("\n运行所有示例...")
            await example_1_basic()
            await example_2_topic_only()
            await example_3_english()
            await example_4_creative()
        elif choice == "0":
            print("\n👋 再见！")
            return
        else:
            print("\n❌ 无效的选项")
            return
        
        print("\n" + "="*60)
        print("✅ 示例运行完成！")
        print("="*60)
        print("\n📚 更多信息:")
        print("- 快速开始: src/core/ppt/QUICKSTART.md")
        print("- 使用示例: src/core/ppt/USAGE_EXAMPLES.md")
        print("- 完整文档: src/core/ppt/README.md")
        
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，再见！")
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
