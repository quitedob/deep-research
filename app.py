#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Application Entry Point
Deep Research API with LLM abstraction layer
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from src.api.deep_research import router as research_router
from src.config.llm_config import validate_config

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
    """
    Application lifespan manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting Deep Research API...")
    
    # Initialize Redis
    logger.info("Initializing Redis...")
    from src.core.security.redis_client import redis_client
    await redis_client.connect()
    
    # Initialize database
    logger.info("Initializing database...")
    from src.dao.db_init import init_database
    from src.dao.db_config import db_config
    from src.dao.base import BaseDAO
    
    db_initialized = await init_database()
    
    if db_initialized:
        # 初始化连接池
        await BaseDAO.init_pool(
            dsn=db_config.get_dsn(),
            min_size=db_config.min_pool_size,
            max_size=db_config.max_pool_size
        )
        logger.info("✓ Database initialized successfully")
    else:
        logger.warning("⚠ Database not available, running in memory mode")
    
    # Validate LLM configurations
    logger.info("Validating LLM provider configurations...")
    validation_results = validate_config()
    
    all_valid = True
    for provider, (is_valid, error_msg) in validation_results.items():
        if is_valid:
            logger.info(f"✓ {provider.capitalize()} configuration valid")
        else:
            logger.warning(f"✗ {provider.capitalize()} configuration error: {error_msg}")
            all_valid = False
    
    if not all_valid:
        logger.warning("Some LLM providers have configuration issues. Check environment variables.")
    else:
        logger.info("All LLM provider configurations validated successfully")
    
    logger.info("Deep Research API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Deep Research API...")
    
    # Close Redis connection
    await redis_client.close()
    
    # Close database connection pool
    await BaseDAO.close_pool()
    logger.info("Database connections closed")


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
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
from src.api.user import router as user_router
from src.api.chat import router as chat_router

app.include_router(research_router)
app.include_router(user_router)
app.include_router(chat_router)


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
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
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
            "app:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)
