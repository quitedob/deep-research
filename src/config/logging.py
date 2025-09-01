# -*- coding: utf-8 -*-
"""
Deep Research 日志配置和监控模块
配置统一的日志格式、性能监控和指标收集
"""

import logging
import sys
import json
import time
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any
from datetime import datetime
from contextvars import ContextVar
from functools import wraps

# 请求ID上下文变量
request_id_context: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_context: ContextVar[Optional[int]] = ContextVar('user_id', default=None)

class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        # 基础日志信息
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }

        # 添加请求上下文
        request_id = request_id_context.get()
        if request_id:
            log_data["request_id"] = request_id

        user_id = user_id_context.get()
        if user_id:
            log_data["user_id"] = user_id

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外字段
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno',
                          'pathname', 'filename', 'module', 'exc_info',
                          'exc_text', 'stack_info', 'lineno', 'funcName',
                          'created', 'msecs', 'relativeCreated', 'thread',
                          'threadName', 'processName', 'process', 'message']:
                log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False, default=str)

class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "requests_total": 0,
            "requests_duration": [],
            "errors_total": 0,
            "llm_calls_total": 0,
            "llm_tokens_total": 0,
            "vector_searches_total": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }

    def record_request(self, duration: float, status_code: int):
        """记录请求"""
        self.metrics["requests_total"] += 1
        self.metrics["requests_duration"].append(duration)

        if status_code >= 400:
            self.metrics["errors_total"] += 1

        # 只保留最近1000个请求的持续时间
        if len(self.metrics["requests_duration"]) > 1000:
            self.metrics["requests_duration"] = self.metrics["requests_duration"][-1000:]

    def record_llm_call(self, tokens_used: int, cost: float):
        """记录LLM调用"""
        self.metrics["llm_calls_total"] += 1
        self.metrics["llm_tokens_total"] += tokens_used

    def record_vector_search(self):
        """记录向量搜索"""
        self.metrics["vector_searches_total"] += 1

    def record_cache(self, hit: bool):
        """记录缓存命中/缺失"""
        if hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        durations = self.metrics["requests_duration"]
        stats = {
            "requests_total": self.metrics["requests_total"],
            "errors_total": self.metrics["errors_total"],
            "error_rate": self.metrics["errors_total"] / max(self.metrics["requests_total"], 1),
            "llm_calls_total": self.metrics["llm_calls_total"],
            "llm_tokens_total": self.metrics["llm_tokens_total"],
            "vector_searches_total": self.metrics["vector_searches_total"],
            "cache_hit_rate": self.metrics["cache_hits"] / max(self.metrics["cache_hits"] + self.metrics["cache_misses"], 1),
        }

        if durations:
            stats.update({
                "avg_request_duration": sum(durations) / len(durations),
                "min_request_duration": min(durations),
                "max_request_duration": max(durations),
                "p95_request_duration": sorted(durations)[int(len(durations) * 0.95)]
            })

        return stats

# 全局性能监控器实例
performance_monitor = PerformanceMonitor()

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    structured: bool = True
) -> logging.Logger:
    """设置增强的日志配置"""

    # 创建根logger
    logger = logging.getLogger("deep-research")
    logger.setLevel(getattr(logging, level.upper()))

    # 防止重复添加handler
    if logger.handlers:
        return logger

    # 创建格式化器
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（如果指定了日志文件）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def get_logger(name: str = None) -> logging.Logger:
    """获取指定名称的logger"""
    if name:
        return logging.getLogger(f"deep-research.{name}")
    return logging.getLogger("deep-research")

def set_request_context(request_id: str, user_id: Optional[int] = None):
    """设置请求上下文"""
    request_id_context.set(request_id)
    if user_id:
        user_id_context.set(user_id)

def get_request_context() -> Dict[str, Any]:
    """获取请求上下文"""
    return {
        "request_id": request_id_context.get(),
        "user_id": user_id_context.get()
    }

def log_performance(operation: str):
    """性能日志装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            logger = get_logger("performance")

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                logger.info(f"操作完成: {operation}",
                          extra={
                              "operation": operation,
                              "duration": duration,
                              "status": "success"
                          })

                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"操作失败: {operation}",
                           extra={
                               "operation": operation,
                               "duration": duration,
                               "status": "error",
                               "error": str(e)
                           })
                raise

        return wrapper
    return decorator

def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    return performance_monitor
