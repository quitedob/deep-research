#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证修复效果的脚本
测试数据库连接、API导入和基本功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_database_connection():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")
    try:
        from pkg.db import init_engine, get_db_session
        from sqlalchemy import text

        # 初始化数据库引擎
        engine = init_engine()

        async for session in get_db_session():
            # 测试基本连接
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ 数据库连接成功: PostgreSQL {version[:50]}...")

            # 测试pgvector扩展
            result = await session.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            if result.fetchone():
                print("✅ pgvector扩展已安装")
            else:
                print("❌ pgvector扩展未找到")

        return True

    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False

async def test_imports():
    """测试关键模块导入"""
    print("\n🔍 测试关键模块导入...")
    try:
        # 测试API模块导入
        from src.api.rag import router as rag_router
        from src.api.health import router as health_router
        from src.api.errors import ErrorCodes, create_error_response
        print("✅ API模块导入成功")

        # 测试配置模块导入
        from src.config.settings import get_settings
        from src.config.logging import get_logger
        print("✅ 配置模块导入成功")

        # 测试数据库模块导入
        from pkg.db import init_engine
        from pkg.db_init import init_database_and_tables
        print("✅ 数据库模块导入成功")

        return True

    except ImportError as e:
        print(f"❌ 模块导入失败: {str(e)}")
        return False

async def test_error_handling():
    """测试错误处理机制"""
    print("\n🔍 测试错误处理机制...")
    try:
        from src.api.errors import create_error_response, ErrorCodes
        from fastapi.responses import JSONResponse

        # 测试错误响应创建
        error_response = create_error_response(
            code=ErrorCodes.INTERNAL_ERROR,
            message="测试错误",
            status_code=500
        )

        if isinstance(error_response, JSONResponse):
            print("✅ 错误响应创建成功")
            return True
        else:
            print("❌ 错误响应创建失败")
            return False

    except Exception as e:
        print(f"❌ 错误处理测试失败: {str(e)}")
        return False

async def test_configuration():
    """测试配置加载"""
    print("\n🔍 测试配置加载...")
    try:
        import yaml
        from src.config.settings import get_settings

        # 测试配置文件加载
        with open('conf.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 检查关键配置
        if 'PRIMARY_LLM_BACKEND' in config:
            print(f"✅ LLM配置加载成功: {config['PRIMARY_LLM_BACKEND']}")
        else:
            print("❌ LLM配置缺失")
            return False

        # 检查安全配置
        if 'CORS_ALLOW_ORIGINS' in config:
            origins = config['CORS_ALLOW_ORIGINS']
            if origins != ["*"]:  # 不应该使用通配符
                print(f"✅ CORS配置安全: {origins}")
            else:
                print("❌ CORS配置不安全，使用通配符")
                return False
        else:
            print("❌ CORS配置缺失")
            return False

        # 测试settings模块
        settings = get_settings()
        if hasattr(settings, 'app_name'):
            print(f"✅ Settings模块工作正常: {settings.app_name}")
        else:
            print("❌ Settings模块配置不完整")
            return False

        return True

    except Exception as e:
        print(f"❌ 配置测试失败: {str(e)}")
        return False

async def main():
    """主验证函数"""
    print("🚀 开始验证修复效果...\n")

    results = []

    # 执行各项测试
    results.append(await test_imports())
    results.append(await test_configuration())
    results.append(await test_database_connection())
    results.append(await test_error_handling())

    # 输出总结
    print("\n" + "="*50)
    print("📊 验证结果总结:")

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ 所有测试通过 ({passed}/{total})")
        print("🎉 修复效果良好！项目已准备好运行。")
        return 0
    else:
        print(f"❌ 部分测试失败 ({passed}/{total})")
        print("⚠️  请检查失败的测试项并修复相关问题。")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


