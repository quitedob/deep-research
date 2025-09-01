#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境配置检查脚本：验证 DeerFlow 深度研究平台的依赖和配置
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_python_version():
    """检查 Python 版本"""
    print("🐍 检查 Python 版本...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - 版本符合要求")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - 需要 Python 3.8+")
        return False


def check_required_packages():
    """检查必需的 Python 包"""
    print("\n📦 检查必需的 Python 包...")
    
    required_packages = [
        "fastapi",
        "uvicorn", 
        "sqlalchemy",
        "asyncpg",
        "pgvector",
        "redis",
        "pydantic",
        "python-dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n💡 安装缺失的包：pip install {' '.join(missing_packages)}")
        return False
    
    return True


def check_optional_packages():
    """检查可选的 Python 包"""
    print("\n📦 检查可选的 Python 包...")
    
    optional_packages = {
        "chromadb": "向量存储（内存回退）",
        "docx2txt": "Word 文档处理",
        "pypandoc": "文档格式转换", 
        "reportlab": "PDF 生成",
        "celery": "异步任务队列",
        "arq": "异步任务队列（备选）"
    }
    
    for package, description in optional_packages.items():
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} - {description}")
        except ImportError:
            print(f"⚠️  {package} - {description} (可选)")


def check_environment_file():
    """检查环境配置文件"""
    print("\n🔧 检查环境配置...")
    
    env_file = project_root / ".env"
    env_example = project_root / "env.example"
    
    if not env_file.exists():
        if env_example.exists():
            print(f"❌ .env 文件不存在")
            print(f"💡 请复制 env.example 为 .env 并配置相关参数")
            return False
        else:
            print(f"❌ .env 和 env.example 文件都不存在")
            return False
    
    print(f"✅ .env 文件存在")
    
    # 检查关键环境变量
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    critical_vars = [
        "DATABASE_URL",
        "REDIS_URL", 
        "SECRET_KEY"
    ]
    
    missing_vars = []
    for var in critical_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            print(f"⚠️  {var} - 未配置")
        else:
            print(f"✅ {var} - 已配置")
    
    return len(missing_vars) == 0


async def check_database_connection():
    """检查数据库连接"""
    print("\n🗄️  检查数据库连接...")
    
    try:
        from pkg.db import init_engine
        
        engine = init_engine(echo=False)
        
        # 测试连接
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            row = result.fetchone()
            
        if row and row[0] == 1:
            print("✅ PostgreSQL 数据库连接成功")
            
            # 检查 pgvector 扩展
            async with engine.begin() as conn:
                try:
                    await conn.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                    print("✅ pgvector 扩展已安装")
                except Exception:
                    print("⚠️  pgvector 扩展未安装，请在数据库中执行: CREATE EXTENSION vector;")
            
            return True
        else:
            print("❌ 数据库连接测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("💡 请检查 DATABASE_URL 配置和 PostgreSQL 服务状态")
        return False


async def check_redis_connection():
    """检查 Redis 连接"""
    print("\n🔴 检查 Redis 连接...")
    
    try:
        import redis.asyncio as redis
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        client = redis.from_url(redis_url)
        
        await client.ping()
        await client.close()
        
        print("✅ Redis 连接成功")
        return True
        
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        print("💡 请检查 REDIS_URL 配置和 Redis 服务状态")
        return False


def check_external_tools():
    """检查外部工具"""
    print("\n🛠️  检查外部工具...")
    
    tools = {
        "ocrmypdf": "OCR 文档处理",
        "pandoc": "文档格式转换"
    }
    
    for tool, description in tools.items():
        try:
            result = subprocess.run([tool, "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ {tool} - {description}")
            else:
                print(f"⚠️  {tool} - {description} (可选)")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"⚠️  {tool} - {description} (未安装，可选)")


async def check_llm_services():
    """检查 LLM 服务配置"""
    print("\n🤖 检查 LLM 服务配置...")
    
    # 检查 API 密钥
    api_keys = {
        "DEEPSEEK_API_KEY": "DeepSeek API",
        "MOONSHOT_API_KEY": "Kimi API", 
        "OPENAI_API_KEY": "OpenAI API",
        "TAVILY_API_KEY": "Tavily 搜索 API"
    }
    
    configured_services = 0
    for key, service in api_keys.items():
        if os.getenv(key):
            print(f"✅ {service} - 已配置")
            configured_services += 1
        else:
            print(f"⚠️  {service} - 未配置")
    
    if configured_services == 0:
        print("❌ 没有配置任何 LLM 服务，系统无法正常工作")
        return False
    
    # 检查 Ollama 服务
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                print(f"✅ Ollama 服务运行中，可用模型: {len(models)} 个")
            else:
                print("⚠️  Ollama 服务未响应")
    except Exception:
        print("⚠️  Ollama 服务未运行（可选）")
    
    return True


async def main():
    """主检查流程"""
    print("🔍 DeerFlow 深度研究平台 - 环境配置检查")
    print("=" * 60)
    
    checks = [
        ("Python 版本", check_python_version),
        ("必需包", check_required_packages),
        ("可选包", check_optional_packages),
        ("环境配置", check_environment_file),
        ("数据库连接", check_database_connection),
        ("Redis 连接", check_redis_connection),
        ("外部工具", check_external_tools),
        ("LLM 服务", check_llm_services)
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} 检查失败: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 检查结果总结:")
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有检查通过！系统已准备就绪")
        print("\n🚀 启动命令:")
        print("   python app.py")
    elif passed >= total * 0.7:
        print("⚠️  大部分检查通过，系统基本可用")
        print("💡 建议修复失败的检查项以获得最佳体验")
    else:
        print("❌ 多项检查失败，请修复配置后重试")
        print("💡 参考文档: README.md")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())