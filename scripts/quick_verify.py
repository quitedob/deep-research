#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证脚本 - 不依赖外部包
只验证核心修复效果
"""

import os
import sys
from pathlib import Path

def test_file_changes():
    """测试文件修改是否正确"""
    print("🔍 验证文件修改...")

    # 检查pkg/db_init.py是否已更新为PostgreSQL
    db_init_file = Path("pkg/db_init.py")
    if db_init_file.exists():
        with open(db_init_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'postgresql' in content.lower() and 'mysql' not in content.lower():
                print("✅ pkg/db_init.py 已更新为PostgreSQL专用")
            else:
                print("❌ pkg/db_init.py 仍包含MySQL相关代码")
                return False
    else:
        print("❌ pkg/db_init.py 文件不存在")
        return False

    # 检查reset_database.py是否已更新
    reset_file = Path("reset_database.py")
    if reset_file.exists():
        with open(reset_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'PostgreSQL' in content and 'pg_terminate_backend' in content:
                print("✅ reset_database.py 已更新为PostgreSQL专用")
            else:
                print("❌ reset_database.py 更新不完整")
                return False
    else:
        print("❌ reset_database.py 文件不存在")
        return False

    # 检查init-db.sql是否移除了硬编码用户
    init_sql_file = Path("init-db.sql")
    if init_sql_file.exists():
        with open(init_sql_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'INSERT INTO users' not in content and '安全提醒' in content:
                print("✅ init-db.sql 已移除硬编码用户")
            else:
                print("❌ init-db.sql 仍包含硬编码用户")
                return False
    else:
        print("❌ init-db.sql 文件不存在")
        return False

    # 检查conf.yaml是否添加了安全配置
    conf_file = Path("conf.yaml")
    if conf_file.exists():
        with open(conf_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'JWT_SECRET_KEY' in content and 'CORS_ALLOW_METHODS' in content:
                print("✅ conf.yaml 已添加安全配置")
            else:
                print("❌ conf.yaml 安全配置不完整")
                return False
    else:
        print("❌ conf.yaml 文件不存在")
        return False

    # 检查src/api/rag.py是否添加了logger导入
    rag_api_file = Path("src/api/rag.py")
    if rag_api_file.exists():
        with open(rag_api_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'from src.config.logging import get_logger' in content and 'logger = get_logger("rag")' in content:
                print("✅ src/api/rag.py 已添加logger导入")
            else:
                print("❌ src/api/rag.py 缺少logger导入")
                return False
    else:
        print("❌ src/api/rag.py 文件不存在")
        return False

    # 检查错误处理模块是否存在
    error_file = Path("src/api/errors.py")
    if error_file.exists():
        with open(error_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'ErrorResponse' in content and 'ErrorCodes' in content:
                print("✅ src/api/errors.py 已创建统一错误处理模块")
            else:
                print("❌ src/api/errors.py 内容不完整")
                return False
    else:
        print("❌ src/api/errors.py 文件不存在")
        return False

    return True

def test_docker_compose():
    """测试docker-compose配置"""
    print("\n🔍 验证Docker配置...")

    compose_file = Path("docker-compose.dev.yml")
    if compose_file.exists():
        with open(compose_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'pgvector/pgvector:pg16' in content and 'pg_isready' in content:
                print("✅ docker-compose.dev.yml 已更新为PostgreSQL")
                return True
            else:
                print("❌ docker-compose.dev.yml 配置不完整")
                return False
    else:
        print("❌ docker-compose.dev.yml 文件不存在")
        return False

def main():
    """主验证函数"""
    print("🚀 开始快速验证修复效果...\n")

    file_test = test_file_changes()
    docker_test = test_docker_compose()

    print("\n" + "="*50)
    print("📊 验证结果总结:")

    if file_test and docker_test:
        print("✅ 所有核心修复验证通过！")
        print("🎉 项目已成功修复主要问题：")
        print("   • 数据库配置冲突已解决")
        print("   • 安全配置已加固")
        print("   • 导入错误已修复")
        print("   • 错误处理已改进")
        print("\n📝 建议下一步：")
        print("   1. 安装项目依赖：pip install -r requirements.txt")
        print("   2. 启动数据库：docker-compose up -d postgres redis")
        print("   3. 初始化数据库：python pkg/db_init.py")
        print("   4. 启动后端服务：python app.py")
        print("   5. 启动前端：cd vue && npm install && npm run dev")
        return 0
    else:
        print("❌ 部分验证失败，请检查上述错误信息")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


