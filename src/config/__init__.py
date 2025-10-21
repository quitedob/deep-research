# -*- coding: utf-8 -*-
"""
Deep Research Platform Configuration Module
统一配置管理系统
"""

from .loader.config_loader import get_config, get_settings
from .logging.logging import (
    setup_logging,
    get_logger,
    set_request_context,
    get_request_context,
    log_performance,
    get_performance_monitor
)

__all__ = [
    "get_config",
    "get_settings",
    "setup_logging",
    "get_logger",
    "set_request_context",
    "get_request_context",
    "log_performance",
    "get_performance_monitor"
]