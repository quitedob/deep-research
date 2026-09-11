#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Application Entry Point
Deep Research API with LLM abstraction layer
"""

import logging
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from backend.api.deep_research import router as research_router
from backend.config.llm_config import validate_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Required storage is ready before serving; one process owns research tasks."""
    from backend.core.security.jwt_manager import jwt_manager
    from backend.core.security.redis_client import redis_client
    from backend.repositories.db_init import init_database
    from backend.repositories.db_config import db_config
    from backend.repositories.base import BaseDAO
    from backend.api.deep_research import research_service
    from backend.core.llm.base_llm import BaseLLM

    jwt_manager.validate_configuration()
    owner_connection = None
    try:
        await redis_client.connect()
        if not await init_database():
            raise RuntimeError("Database initialization failed; startup aborted")
        owner_connection = await asyncpg.connect(db_config.get_dsn())
        # Session-level lock is released by PostgreSQL even after process termination.
        if not await owner_connection.fetchval("SELECT pg_try_advisory_lock(742881906)"):
            raise RuntimeError("Research task execution requires a single application worker")
        await BaseDAO.init_pool(db_config.get_dsn(), db_config.min_pool_size, db_config.max_pool_size)
        app.state.research_owner_connection = owner_connection
        for provider, (valid, reason) in validate_config().items():
            if not valid:
                logger.warning("Provider %s configuration: %s", provider, reason)
        yield
    finally:
        await research_service.close()
        await BaseLLM.close_all()
        await BaseDAO.close_pool()
        if owner_connection is not None:
            await owner_connection.close()
        await redis_client.close()


# Create FastAPI application
app = FastAPI(
    title="Deep Research API",
    description="AI-powered deep research system with multi-provider LLM support",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if origin.strip() and origin.strip() != "*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
from backend.api.user import router as user_router
from backend.api.chat import router as chat_router
from backend.api.interactions import router as interaction_router

app.include_router(research_router)
app.include_router(user_router)
app.include_router(chat_router)
app.include_router(interaction_router)

from backend.repositories.base import DatabaseUnavailableError
from backend.core.security.redis_client import SecurityStoreUnavailableError


@app.exception_handler(DatabaseUnavailableError)
@app.exception_handler(SecurityStoreUnavailableError)
async def storage_unavailable_handler(request, exc):
    logger.error("Required storage unavailable", exc_info=exc)
    return JSONResponse(status_code=503, content={"detail": "服务暂时不可用，请稍后重试"})


@app.get("/api/health")
@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API is running.

    Returns:
        JSON response with health status
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "Deep Research API",
            "version": "1.0.0"
        }
    )


@app.get("/")
async def root():
    """
    Root endpoint with API information.

    Returns:
        JSON response with API details
    """
    return {
        "message": "Deep Research API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.

    Args:
        request: The request that caused the error
        exc: The exception that was raised

    Returns:
        JSON error response
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": "请求处理失败，请稍后重试"
        }
    )


def run():
    """
    Run the application with Uvicorn server.

    Configuration:
    - Host: 0.0.0.0 (accessible from all network interfaces)
    - Port: 8000
    - Reload: True (auto-reload on code changes for development)
    - Log level: info
    """
    try:
        logger.info("Starting Uvicorn server...")
        uvicorn.run(
            "backend.main:app",
            host=os.getenv("API_HOST", "127.0.0.1"),
            port=int(os.getenv("API_PORT", "8000")),
            reload=os.getenv("API_RELOAD", "false").lower() == "true",
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run()
