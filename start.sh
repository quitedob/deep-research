#!/bin/bash

# 深度研究平台启动脚本

echo "=== 深度研究平台启动脚本 ==="
echo "时间: $(date)"
echo "Python 版本: $(python --version)"
echo "工作目录: $(pwd)"

# 检查环境变量
echo "=== 环境变量检查 ==="
echo "DATABASE_URL: ${DATABASE_URL:-未设置}"
echo "REDIS_URL: ${REDIS_URL:-未设置}"
echo "ENVIRONMENT: ${ENVIRONMENT:-development}"

# 等待数据库就绪
echo "=== 等待数据库就绪 ==="
if [ -n "$DATABASE_URL" ]; then
    echo "等待数据库连接..."
    # 这里可以添加数据库连接检查逻辑
    sleep 5
fi

# 等待 Redis 就绪
echo "=== 等待 Redis 就绪 ==="
if [ -n "$REDIS_URL" ]; then
    echo "等待 Redis 连接..."
    # 这里可以添加 Redis 连接检查逻辑
    sleep 3
fi

# 运行数据库迁移（如果需要）
echo "=== 数据库初始化 ==="
python -c "
import asyncio
from app import create_app
from pkg.db import init_engine
from src.sqlmodel.models import Base

async def init_db():
    app = create_app()
    engine = init_engine(echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('数据库表创建完成')

if __name__ == '__main__':
    asyncio.run(init_db())
"

# 启动应用
echo "=== 启动应用 ==="
echo "启动命令: uvicorn app:app --host 0.0.0.0 --port 8000"
exec uvicorn app:app --host 0.0.0.0 --port 8000
