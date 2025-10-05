# -*- coding: utf-8 -*-
"""
监控中间件：请求监控、性能指标收集和健康检查
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from src.config.logging import (
    get_logger,
    set_request_context,
    get_performance_monitor,
    get_request_context
)

logger = get_logger("middleware")
monitor = get_performance_monitor()

class MonitoringMiddleware:
    """监控中间件"""

    def __init__(self, app: Callable):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 生成请求ID
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # 创建包装的send函数来捕获响应
        response_started = False
        response_status = 200

        async def wrapped_send(message):
            nonlocal response_started, response_status

            if message["type"] == "http.response.start":
                response_started = True
                response_status = message["status"]

            await send(message)

        # 设置请求上下文
        set_request_context(request_id)

        try:
            # 处理请求
            await self.app(scope, receive, wrapped_send)

            # 记录请求完成
            duration = time.time() - start_time
            monitor.record_request(duration, response_status)

            # 记录慢请求
            if duration > 1.0:  # 超过1秒的请求
                logger.warning("慢请求检测",
                             extra={
                                 "path": scope.get("path"),
                                 "method": scope.get("method"),
                                 "duration": duration,
                                 "status": response_status
                             })

        except Exception as e:
            # 记录错误请求
            duration = time.time() - start_time
            monitor.record_request(duration, 500)

            logger.error("请求处理异常",
                        extra={
                            "path": scope.get("path"),
                            "method": scope.get("method"),
                            "duration": duration,
                            "error": str(e)
                        })
            raise

async def request_monitoring_middleware(request: Request, call_next):
    """FastAPI请求监控中间件"""

    # 生成请求ID
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # 设置请求上下文
    user_id = getattr(request.state, 'user_id', None)
    set_request_context(request_id, user_id)

    # 记录请求开始
    logger.info("请求开始",
               extra={
                   "method": request.method,
                   "url": str(request.url),
                   "headers": dict(request.headers),
                   "client": request.client.host if request.client else None
               })

    try:
        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        duration = time.time() - start_time

        # 记录性能指标
        monitor.record_request(duration, response.status_code)

        # 记录慢请求
        if duration > 1.0:
            logger.warning("慢请求告警",
                         extra={
                             "method": request.method,
                             "url": str(request.url),
                             "duration": duration,
                             "status": response.status_code
                         })

        # 添加请求ID到响应头
        response.headers["X-Request-ID"] = request_id

        # 记录请求完成
        logger.info("请求完成",
                   extra={
                       "method": request.method,
                       "url": str(request.url),
                       "status": response.status_code,
                       "duration": duration
                   })

        return response

    except Exception as e:
        # 计算处理时间
        duration = time.time() - start_time

        # 记录错误请求
        monitor.record_request(duration, 500)

        logger.error("请求异常",
                    extra={
                        "method": request.method,
                        "url": str(request.url),
                        "duration": duration,
                        "error": str(e)
                    })
        raise

def llm_call_monitoring(func):
    """LLM调用监控装饰器"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time

            # 记录LLM调用指标
            if hasattr(result, 'usage'):
                tokens_used = result.usage.get('total_tokens', 0)
                monitor.record_llm_call(tokens_used, 0.0)  # 成本需要根据提供商计算

            logger.info("LLM调用完成",
                       extra={
                           "model": getattr(result, 'model', 'unknown'),
                           "duration": duration,
                           "tokens_used": getattr(result, 'usage', {}).get('total_tokens', 0)
                       })

            return result

        except Exception as e:
            duration = time.time() - start_time

            logger.error("LLM调用失败",
                        extra={
                            "duration": duration,
                            "error": str(e)
                        })
            raise

    return wrapper

def vector_search_monitoring(func):
    """向量搜索监控装饰器"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time

            # 记录向量搜索
            monitor.record_vector_search()

            logger.info("向量搜索完成",
                       extra={
                           "duration": duration,
                           "results_count": len(result) if hasattr(result, '__len__') else 0
                       })

            return result

        except Exception as e:
            duration = time.time() - start_time

            logger.error("向量搜索失败",
                        extra={
                            "duration": duration,
                            "error": str(e)
                        })
            raise

    return wrapper

async def get_health_status():
    """获取健康状态"""
    try:
        # 检查数据库连接
        from src.core.db import get_db_session
        async for session in get_db_session():
            await session.execute("SELECT 1")
            db_status = "healthy"
            break
    except Exception:
        db_status = "unhealthy"

    # 检查Redis连接
    try:
        import redis.asyncio as redis
        from src.config.config_loader import get_settings
        settings = get_settings()
        r = redis.from_url(settings.redis_url)
        await r.ping()
        redis_status = "healthy"
        await r.close()
    except Exception:
        redis_status = "unhealthy"

    # 获取性能统计
    stats = monitor.get_stats()

    health_data = {
        "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "unhealthy",
        "timestamp": time.time(),
        "services": {
            "database": db_status,
            "redis": redis_status
        },
        "performance": stats,
        "version": "1.0.0"
    }

    status_code = 200 if health_data["status"] == "healthy" else 503
    return JSONResponse(content=health_data, status_code=status_code)

async def get_metrics():
    """获取监控指标（Prometheus格式）"""
    stats = monitor.get_stats()

    metrics = []

    # 请求指标
    metrics.append(f'# HELP deep_research_requests_total 总请求数')
    metrics.append(f'# TYPE deep_research_requests_total counter')
    metrics.append(f'deep_research_requests_total {stats["requests_total"]}')

    # 错误指标
    metrics.append(f'# HELP deep_research_errors_total 总错误数')
    metrics.append(f'# TYPE deep_research_errors_total counter')
    metrics.append(f'deep_research_errors_total {stats["errors_total"]}')

    # LLM调用指标
    metrics.append(f'# HELP deep_research_llm_calls_total LLM调用总数')
    metrics.append(f'# TYPE deep_research_llm_calls_total counter')
    metrics.append(f'deep_research_llm_calls_total {stats["llm_calls_total"]}')

    # Token使用指标
    metrics.append(f'# HELP deep_research_llm_tokens_total LLM Token总数')
    metrics.append(f'# TYPE deep_research_llm_tokens_total counter')
    metrics.append(f'deep_research_llm_tokens_total {stats["llm_tokens_total"]}')

    # 向量搜索指标
    metrics.append(f'# HELP deep_research_vector_searches_total 向量搜索总数')
    metrics.append(f'# TYPE deep_research_vector_searches_total counter')
    metrics.append(f'deep_research_vector_searches_total {stats["vector_searches_total"]}')

    # 请求持续时间
    if "avg_request_duration" in stats:
        metrics.append(f'# HELP deep_research_request_duration_seconds 请求持续时间')
        metrics.append(f'# TYPE deep_research_request_duration_seconds histogram')
        metrics.append(f'deep_research_request_duration_seconds_avg {stats["avg_request_duration"]}')
        metrics.append(f'deep_research_request_duration_seconds_p95 {stats["p95_request_duration"]}')

    return "\n".join(metrics)

