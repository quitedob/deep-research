# -*- coding: utf-8 -*-
"""
深度研究平台主应用：FastAPI 应用入口，集成所有服务和中间件。
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 核心健康检查和提供商信息已整合到 api/health.py
from src.core.db import init_engine
from src.core.db_init import init_database_and_tables
from src.sqlmodel.models import Base
from src.sqlmodel import rag_models  # 确保RAG模型被导入
from src.core.cache import cache
from sqlalchemy.ext.asyncio import AsyncEngine
# 现有API路由
from src.api.billing import router as billing_router
from src.api.rag import router as rag_router
from src.api.llm_config import router as llm_config_router
from src.api.conversation import router as conversation_router
from src.api.evidence import router as evidence_router
from src.api.health import router as health_router
from src.api.admin import router as admin_router
from src.api.ppt import router as ppt_router
from src.api.quota import router as quota_router

# 新重构的API模块
from src.api.chat import router as chat_router
from src.api.export import router as export_router
from src.api.research import router as research_router
from src.api.history import router as history_router
from src.api.search_full import router as search_full_router
from src.api.share import router as share_router
from src.api.user import router as user_router

# 内容审核和智能体配置路由
from src.api.moderation import router as moderation_router
from src.api.agent_llm_config import router as agent_llm_config_router

# 对话监控路由
from src.api.conversation_monitor import router as conversation_monitor_router

# 记忆管理路由
from src.api.memory import router as memory_router
from src.middleware.monitoring import request_monitoring_middleware
from src.middleware.security import security_middleware_func
from src.config.loader.config_loader import get_settings
from src.config.logging.logging import setup_logging

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    # 连接缓存（无 Redis 自动回退内存）
    await cache.connect()

    # 初始化数据库并建表（智能初始化）
    if settings.auto_create_tables:
        from src.core.db_init import initialize_database
        success = await initialize_database(force_recreate=False)
        if not success:
            raise RuntimeError("数据库初始化失败")

    # 创建必要的目录
    _create_directories()

    # 初始化RAG功能
    try:
        from src.core.rag.config import initialize_rag_directories
        initialize_rag_directories()
        print("RAG功能初始化成功")
    except Exception as e:
        print(f"RAG功能初始化失败: {e}")

    # 启动任务工作器
    try:
        from src.tasks.worker import start_task_worker
        await start_task_worker(worker_count=2, concurrency=1)
        print("任务工作器已启动")
    except Exception as e:
        print(f"启动任务工作器失败: {e}")

    print(f"应用启动成功：{settings.app_name} v{settings.app_version}")
    print(f"环境：{settings.environment}")
    print(f"调试模式：{settings.debug}")
    print(f"LLM提供商：{settings.llm_provider}")

    yield  # 应用运行期间

    # 关闭时执行
    # 停止任务工作器
    try:
        from src.tasks.worker import stop_task_worker
        await stop_task_worker()
        print("任务工作器已停止")
    except Exception as e:
        print(f"停止任务工作器失败: {e}")

    # 断开缓存连接
    await cache.disconnect()
    print("应用已关闭")


def create_app() -> FastAPI:
    """创建 FastAPI 应用并注册中间件与路由。"""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan
    )

    # 初始化日志系统
    log_file = os.getenv("LOG_FILE", "logs/deep-research.log")
    setup_logging(
        level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=log_file,
        structured=True
    )

    # 安全中间件（最先执行）
    @app.middleware("http")
    async def security_middleware(request: Request, call_next):
        return await security_middleware_func(request, call_next)

    # 请求监控中间件
    @app.middleware("http")
    async def monitoring_middleware(request: Request, call_next):
        return await request_monitoring_middleware(request, call_next)

    # CORS 中间件（安全配置）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allow_origins or ["http://localhost:3000", "http://localhost:8080"],  # 默认只允许本地开发
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "Accept",
            "Accept-Encoding",
            "Accept-Language",
            "Cache-Control",
            "Connection",
            "Host",
            "User-Agent",
            "X-Request-ID"
        ],
        max_age=86400,  # 24小时
    )

    # 注册路由 - 统一 /api 前缀

    # 健康检查路由（已整合serve层的健康检查和提供商信息）
    app.include_router(health_router, prefix="/api")

    # 原有API路由
    app.include_router(billing_router, prefix="/api")      # 计费
    app.include_router(rag_router, prefix="/api")          # RAG功能
    app.include_router(llm_config_router, prefix="/api")   # LLM配置
    app.include_router(conversation_router, prefix="/api") # 对话记忆
    app.include_router(evidence_router, prefix="/api")     # 证据链
    # app.include_router(health_router, prefix="/api")   # 健康检查已在上方注册
    app.include_router(ppt_router, prefix="/api")          # PPT生成
    app.include_router(admin_router, prefix="/api")        # 管理员
    app.include_router(quota_router, prefix="/api")        # 配额管理

    # 新重构的API模块
    app.include_router(chat_router, prefix="/api")         # 聊天功能
    app.include_router(export_router, prefix="/api")       # 导出功能
    app.include_router(research_router, prefix="/api")     # 研究功能
    app.include_router(history_router, prefix="/api")      # 历史记录
    app.include_router(search_full_router, prefix="/api")  # 搜索功能
    app.include_router(share_router, prefix="/api")        # 分享功能
    app.include_router(user_router, prefix="/api")         # 用户功能

    # 内容审核和智能体配置路由
    app.include_router(moderation_router, prefix="/api")   # 内容审核
    app.include_router(agent_llm_config_router, prefix="/api") # 智能体配置

    # 对话监控路由
    app.include_router(conversation_monitor_router, prefix="/api") # 对话监控

    # 记忆管理路由
    app.include_router(memory_router, prefix="/api")       # 记忆管理

    # 暂时禁用的路由（由于模块不存在）
    # app.include_router(agents_router, prefix="/api")
    # app.include_router(llm_provider_router, prefix="/api")
    # app.include_router(search_router, prefix="/api")
    # app.include_router(ocr_router, prefix="/api")
    # app.include_router(file_upload_router, prefix="/api")

    return app


def _create_directories():
    """创建必要的目录"""
    directories = [
        settings.upload_dir,
        settings.temp_dir,
        settings.rag_index_path,
        settings.vector_store_path,
        "outputs",
        "logs"  # 日志目录
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

app = create_app()


if __name__ == "__main__":
    # 本地启动：与前端默认 API_BASE_URL= http://localhost:8000/api 保持一致
    import uvicorn
    uvicorn.run(
        "app:app", 
        host=settings.host, 
        port=settings.port, 
        reload=settings.enable_reload
    )


