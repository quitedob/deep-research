# -*- coding: utf-8 -*-
"""
AgentWork - AI智能研究助手后端服务（统一应用入口）  # 模块说明
"""
import sys  # 系统路径
from pathlib import Path  # 路径
from contextlib import asynccontextmanager  # 生命周期
from fastapi import FastAPI  # FastAPI
from fastapi.middleware.cors import CORSMiddleware  # CORS
from fastapi.responses import JSONResponse  # JSON响应

# 确保根目录在 sys.path
ROOT_DIR = Path(__file__).parent.parent.parent.absolute()  # 计算根目录
sys.path.insert(0, str(ROOT_DIR))  # 注入路径

from src.config.settings import get_settings  # 配置
from src.config.logging import setup_logging  # 日志
from src.server.routers import chat, research, health, auth, admin, chat_stream  # 路由

settings = get_settings()  # 读取配置
logger = setup_logging(level=settings.LOG_LEVEL)  # 初始化日志


@asynccontextmanager
async def lifespan(app: FastAPI):  # 应用生命周期
    logger.info("🚀 AgentWork 服务启动中...")  # 启动日志
    logger.info(f"🔧 配置: {'开发' if settings.DEBUG else '生产'}")  # 模式
    yield  # 让出
    logger.info("🛑 AgentWork 服务关闭中...")  # 关闭


def create_app() -> FastAPI:  # 工厂函数
    """创建并返回 FastAPI 应用实例"""  # 函数说明
    app = FastAPI(title="AgentWork API", description="AI智能研究与学习助手", version="2.0.0", lifespan=lifespan)  # 应用
    app.add_middleware(  # CORS
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(chat.router)
    app.include_router(research.router)
    app.include_router(chat_stream.router)
    app.include_router(admin.router)

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):  # 全局异常
        logger.error(f"未处理异常: {exc}", exc_info=True)  # 记录
        return JSONResponse(status_code=500, content={"error": "内部服务器错误", "detail": str(exc)})  # 返回

    @app.get("/")
    async def root():  # 根路径
        return {"name": "AgentWork API", "version": "2.0.0", "status": "运行中"}  # 返回

    return app  # 返回应用


