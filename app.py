# -*- coding: utf-8 -*-
"""
深度研究平台主应用：FastAPI 应用入口，集成所有服务和中间件。
"""

import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 路由层
from src.serve.api import api_router
from src.core.db import init_engine
from src.core.db_init import init_database_and_tables
from src.sqlmodel.models import Base
from src.sqlmodel import rag_models  # 确保RAG模型被导入
from src.core.cache import cache
from sqlalchemy.ext.asyncio import AsyncEngine
from src.api.billing import router as billing_router
from src.api.rag import router as rag_router
from src.api.llm_config import router as llm_config_router
from src.api.conversation import router as conversation_router
from src.api.evidence import router as evidence_router
from src.api.health import router as health_router
from src.core.ppt.api.routes import router as ppt_router
from src.middleware.monitoring import request_monitoring_middleware
from src.middleware.security import security_middleware_func
from src.config.settings import get_settings
from src.config.logging import setup_logging

settings = get_settings()

def create_app() -> FastAPI:
    """创建 FastAPI 应用并注册中间件与路由。"""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug
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
        allow_origins=settings.cors_allow_origins or ["http://localhost:3000", "http://localhost:8080"],  # 默认只允许本地开发
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

    # 注册路由
    # 注册统一 /api 前缀路由
    app.include_router(api_router, prefix="/api")

    # 注册计费路由
    app.include_router(billing_router, prefix="/api")

    # 注册 RAG 路由
    app.include_router(rag_router, prefix="/api")

    # 注册 LLM 配置路由
    app.include_router(llm_config_router, prefix="/api")

    # 注册对话记忆路由
    app.include_router(conversation_router, prefix="/api")

    # 注册证据链路由
    app.include_router(evidence_router, prefix="/api")

    # 注册健康检查路由
    app.include_router(health_router, prefix="/api")

    # 注册PPT生成路由
    app.include_router(ppt_router)
    
    @app.on_event("startup")
    async def _startup():
        # 连接缓存（无 Redis 自动回退内存）
        await cache.connect()
        
        # 初始化数据库并建表（开发期）
        if settings.auto_create_tables:
            success = await init_database_and_tables(settings.database_url)
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
        
        # 初始化 pgvector 索引（如果需要）
        try:
            from src.rag.pgvector_store import get_pgvector_store
            pgvector_store = get_pgvector_store()
            await pgvector_store.create_vector_index('ivfflat')
            print("pgvector 索引已初始化")
        except Exception as e:
            print(f"初始化 pgvector 索引失败: {e}")
        
        print(f"应用启动成功：{settings.app_name} v{settings.app_version}")
        print(f"环境：{settings.environment}")
        print(f"调试模式：{settings.debug}")
        print(f"LLM提供商：{settings.llm_provider}")
    
    @app.on_event("shutdown")
    async def _shutdown():
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


