# -*- coding: utf-8 -*-
"""
配额限制模块
提供滑动窗口限流算法的实现
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

from src.core.cache import cache


@dataclass
class RequestRecord:
    """请求记录"""
    timestamp: float
    endpoint: str


class SlidingWindowLimiter:
    """
    滑动窗口限流器

    使用Redis存储请求记录，实现分布式环境下的配额限制
    """

    def __init__(self, window_size: int = 3600, max_requests: int = 1000):
        """
        初始化滑动窗口限流器

        Args:
            window_size: 滑动窗口大小（秒）
            max_requests: 窗口内最大请求数
        """
        self.window_size = window_size
        self.max_requests = max_requests

    async def is_allowed(self, key: str, endpoint: str = "") -> Tuple[bool, int]:
        """
        检查请求是否被允许

        Args:
            key: 标识用户的键（如用户ID）
            endpoint: 请求的端点路径

        Returns:
            Tuple[bool, int]: (是否允许, 当前窗口内的请求数)
        """
        current_time = time.time()
        window_start = current_time - self.window_size

        # 构建缓存键
        cache_key = f"rate_limit:{key}:{endpoint}"

        try:
            # 获取当前窗口内的请求记录
            records_data = await cache.get(cache_key)
            if records_data is None:
                records = []
            else:
                records = records_data if isinstance(records_data, list) else []

            # 过滤掉窗口外的记录
            valid_records = [
                record for record in records
                if isinstance(record, dict) and record.get('timestamp', 0) > window_start
            ]

            # 检查是否超过限制
            if len(valid_records) >= self.max_requests:
                return False, len(valid_records)

            # 添加新记录
            new_record = RequestRecord(timestamp=current_time, endpoint=endpoint)
            valid_records.append({
                'timestamp': new_record.timestamp,
                'endpoint': new_record.endpoint
            })

            # 更新缓存（过期时间为窗口大小）
            await cache.set(cache_key, valid_records, ttl=self.window_size)

            return True, len(valid_records)

        except Exception:
            # 如果缓存操作失败，默认允许请求
            return True, 0

    async def get_remaining_requests(self, key: str, endpoint: str = "") -> int:
        """
        获取剩余可用请求数

        Args:
            key: 标识用户的键
            endpoint: 请求的端点路径

        Returns:
            int: 剩余可用请求数
        """
        _, current_count = await self.is_allowed(key, endpoint)
        remaining = max(0, self.max_requests - current_count)
        return remaining

    async def get_window_info(self, key: str, endpoint: str = "") -> Dict:
        """
        获取窗口信息

        Args:
            key: 标识用户的键
            endpoint: 请求的端点路径

        Returns:
            Dict: 包含窗口大小、当前请求数、剩余请求数等信息
        """
        _, current_count = await self.is_allowed(key, endpoint)

        return {
            "window_size": self.window_size,
            "max_requests": self.max_requests,
            "current_requests": current_count,
            "remaining_requests": max(0, self.max_requests - current_count),
            "reset_time": time.time() + self.window_size
        }

    async def reset(self, key: str, endpoint: str = "") -> bool:
        """
        重置用户的配额计数

        Args:
            key: 标识用户的键
            endpoint: 请求的端点路径

        Returns:
            bool: 重置是否成功
        """
        cache_key = f"rate_limit:{key}:{endpoint}"
        return await cache.delete(cache_key)
