#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgentWork - AI智能研究助手统一启动入口
支持多模态输出和深度迭代研究

用法:
    python app.py                    # 启动开发模式
    python app.py --prod             # 启动生产模式  
    python app.py --help             # 显示帮助信息
    python app.py --test             # 运行测试
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(ROOT_DIR))

def run_backend_dev():
    """启动开发模式后端服务"""
    print("🚀 启动开发模式后端服务...")
    print("📡 API服务: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    
    # 确保.env文件存在
    env_file = ROOT_DIR / ".env"
    env_example = ROOT_DIR / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print("⚠️  未找到.env文件，将使用默认环境变量。可复制 .env.example 为 .env 并补充密钥")
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.server.refactored_app:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]
    
    try:
        subprocess.run(cmd, cwd=ROOT_DIR, check=True)
    except KeyboardInterrupt:
        print("\n✅ 后端服务已停止")
    except Exception as e:
        print(f"❌ 启动后端服务失败: {e}")

def run_backend_prod():
    """启动生产模式后端服务"""
    print("🚀 启动生产模式后端服务...")
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.server.refactored_app:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--workers", "4"
    ]
    
    try:
        subprocess.run(cmd, cwd=ROOT_DIR, check=True)
    except KeyboardInterrupt:
        print("\n✅ 后端服务已停止")
    except Exception as e:
        print(f"❌ 启动后端服务失败: {e}")

def run_frontend():
    """启动前端开发服务"""
    print("🎨 启动前端开发服务...")
    print("🌐 前端界面: http://localhost:3000")
    
    vue_dir = ROOT_DIR / "vue"
    if not vue_dir.exists():
        print("❌ 未找到vue目录，请确保前端代码已安装")
        return
    
    # 检查是否安装了依赖
    node_modules = vue_dir / "node_modules"
    if not node_modules.exists():
        print("📦 检测到未安装前端依赖，正在安装...")
        subprocess.run(["npm", "install"], cwd=vue_dir, check=True)
    
    cmd = ["npm", "run", "dev"]
    
    try:
        subprocess.run(cmd, cwd=vue_dir, check=True)
    except KeyboardInterrupt:
        print("\n✅ 前端服务已停止")
    except Exception as e:
        print(f"❌ 启动前端服务失败: {e}")

def run_tests():
    """运行项目测试"""
    print("🧪 运行项目测试...")
    
    test_dir = ROOT_DIR / "test"
    if not test_dir.exists():
        print("❌ 未找到test目录")
        return
    
    cmd = [sys.executable, "-m", "pytest", "test/", "-v"]
    
    try:
        subprocess.run(cmd, cwd=ROOT_DIR, check=True)
    except Exception as e:
        print(f"❌ 运行测试失败: {e}")

def check_dependencies():
    """检查项目依赖"""
    print("🔍 检查项目依赖...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version < (3, 9):
        print(f"❌ Python版本过低: {python_version.major}.{python_version.minor}")
        print("   需要Python 3.9或更高版本")
        return False
    
    print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查.env文件
    env_file = ROOT_DIR / ".env"
    if not env_file.exists():
        print("⚠️  未找到.env文件，将使用默认配置")
    else:
        print("✅ 找到.env配置文件")
    
    return True

def show_status():
    """显示项目状态信息"""
    print("📊 AgentWork 项目状态")
    print("=" * 50)
    print(f"📁 项目根目录: {ROOT_DIR}")
    print(f"🐍 Python路径: {sys.executable}")
    
    # 检查关键目录
    dirs_to_check = ["src", "vue", "test", "scripts"]
    for dir_name in dirs_to_check:
        dir_path = ROOT_DIR / dir_name
        status = "✅" if dir_path.exists() else "❌"
        print(f"{status} {dir_name}/ 目录")
    
    # 检查关键文件
    files_to_check = [".env", "pyproject.toml", "conf.yaml"]
    for file_name in files_to_check:
        file_path = ROOT_DIR / file_name
        status = "✅" if file_path.exists() else "❌"
        print(f"{status} {file_name} 文件")

def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="AgentWork - AI智能研究助手启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python mainstart.py              # 开发模式启动后端
  python mainstart.py --prod       # 生产模式启动后端
  python mainstart.py --frontend   # 启动前端开发服务
  python mainstart.py --test       # 运行测试
  python mainstart.py --status     # 显示项目状态
        """
    )
    
    parser.add_argument(
        "--prod", 
        action="store_true", 
        help="启动生产模式"
    )
    
    parser.add_argument(
        "--frontend", 
        action="store_true", 
        help="启动前端开发服务"
    )
    
    parser.add_argument(
        "--test", 
        action="store_true", 
        help="运行项目测试"
    )
    
    parser.add_argument(
        "--status", 
        action="store_true", 
        help="显示项目状态"
    )
    
    parser.add_argument(
        "--check", 
        action="store_true", 
        help="检查项目依赖"
    )
    
    args = parser.parse_args()
    
    # 显示欢迎信息
    print("🤖 AgentWork - AI智能研究助手")
    print("=" * 50)
    
    if args.status:
        show_status()
        return
    
    if args.check:
        if check_dependencies():
            print("✅ 依赖检查通过")
        return
    
    if args.test:
        run_tests()
        return
    
    if args.frontend:
        run_frontend()
        return
    
    if args.prod:
        run_backend_prod()
        return
    
    # 默认启动开发模式
    run_backend_dev()

if __name__ == "__main__":
    main() 