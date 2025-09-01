# -*- coding: utf-8 -*-
"""
统一配置入口：包装原有 src.config.settings.get_settings。
"""

from __future__ import annotations

from src.config.settings import get_settings as _get_settings


def get_settings():
    return _get_settings()


