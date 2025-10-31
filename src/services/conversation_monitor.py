# -*- coding: utf-8 -*-
"""
对话监控服务
实时监控对话状态、消息计数、RAG状态、网络连接等
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConversationMonitor:
    """对话监控服务"""

    def __init__(self):
        # 监控数据存储
        self._session_metrics: Dict[str, Dict[str, Any]] = {}
        self._global_metrics: Dict[str, Any] = {
            "total_sessions": 0,
            "total_messages": 0,
            "rag_enhanced_sessions": 0,
            "network_searches": 0,
            "rag_searches": 0,
            "mode_switches": 0,
            "memory_summaries": 0,
            "start_time": datetime.utcnow().isoformat()
        }

        # 性能指标
        self._performance_metrics: Dict[str, List[float]] = defaultdict(list)

        # 监控锁
        self._lock = asyncio.Lock()

    async def track_message(
        self,
        session_id: str,
        user_id: str,
        message_count: int,
        mode: str,
        processing_time: float = 0.0
    ) -> None:
        """
        跟踪消息

        Args:
            session_id: 会话ID
            user_id: 用户ID
            message_count: 消息计数
            mode: 对话模式
            processing_time: 处理时间（秒）
        """
        async with self._lock:
            # 更新会话指标
            if session_id not in self._session_metrics:
                self._session_metrics[session_id] = {
                    "session_id": session_id,
                    "user_id": user_id,
                    "message_count": 0,
                    "current_mode": mode,
                    "rag_searches": 0,
                    "network_searches": 0,
                    "mode_switches": 0,
                    "total_processing_time": 0.0,
                    "created_at": datetime.utcnow().isoformat(),
                    "last_activity": datetime.utcnow().isoformat()
                }
                self._global_metrics["total_sessions"] += 1

            session_metrics = self._session_metrics[session_id]
            session_metrics["message_count"] = message_count
            session_metrics["current_mode"] = mode
            session_metrics["total_processing_time"] += processing_time
            session_metrics["last_activity"] = datetime.utcnow().isoformat()

            # 更新全局指标
            self._global_metrics["total_messages"] += 1

            # 记录性能指标
            self._performance_metrics["message_processing_time"].append(processing_time)

            # 保持性能指标列表大小
            if len(self._performance_metrics["message_processing_time"]) > 1000:
                self._performance_metrics["message_processing_time"] = \
                    self._performance_metrics["message_processing_time"][-1000:]

    async def track_mode_switch(
        self,
        session_id: str,
        old_mode: str,
        new_mode: str
    ) -> None:
        """
        跟踪模式切换

        Args:
            session_id: 会话ID
            old_mode: 旧模式
            new_mode: 新模式
        """
        async with self._lock:
            if session_id in self._session_metrics:
                self._session_metrics[session_id]["mode_switches"] += 1
                self._session_metrics[session_id]["current_mode"] = new_mode

            self._global_metrics["mode_switches"] += 1

            if new_mode == "rag_enhanced":
                self._global_metrics["rag_enhanced_sessions"] += 1

            logger.info(f"会话 {session_id} 模式切换: {old_mode} -> {new_mode}")

    async def track_rag_search(
        self,
        session_id: str,
        results_count: int,
        search_time: float = 0.0
    ) -> None:
        """
        跟踪RAG搜索

        Args:
            session_id: 会话ID
            results_count: 结果数量
            search_time: 搜索时间（秒）
        """
        async with self._lock:
            if session_id in self._session_metrics:
                self._session_metrics[session_id]["rag_searches"] += 1

            self._global_metrics["rag_searches"] += 1

            # 记录性能指标
            self._performance_metrics["rag_search_time"].append(search_time)
            self._performance_metrics["rag_results_count"].append(results_count)

    async def track_network_search(
        self,
        session_id: str,
        results_count: int,
        search_time: float = 0.0
    ) -> None:
        """
        跟踪网络搜索

        Args:
            session_id: 会话ID
            results_count: 结果数量
            search_time: 搜索时间（秒）
        """
        async with self._lock:
            if session_id in self._session_metrics:
                self._session_metrics[session_id]["network_searches"] += 1

            self._global_metrics["network_searches"] += 1

            # 记录性能指标
            self._performance_metrics["network_search_time"].append(search_time)
            self._performance_metrics["network_results_count"].append(results_count)

    async def track_memory_summary(
        self,
        session_id: str,
        summary_time: float = 0.0
    ) -> None:
        """
        跟踪记忆摘要生成

        Args:
            session_id: 会话ID
            summary_time: 摘要生成时间（秒）
        """
        async with self._lock:
            self._global_metrics["memory_summaries"] += 1

            # 记录性能指标
            self._performance_metrics["memory_summary_time"].append(summary_time)

            logger.info(f"会话 {session_id} 生成记忆摘要，耗时 {summary_time:.2f}秒")

    async def get_session_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话指标

        Args:
            session_id: 会话ID

        Returns:
            会话指标数据
        """
        async with self._lock:
            return self._session_metrics.get(session_id)

    async def get_global_metrics(self) -> Dict[str, Any]:
        """
        获取全局指标

        Returns:
            全局指标数据
        """
        async with self._lock:
            # 计算平均值
            avg_message_time = self._calculate_average(
                self._performance_metrics.get("message_processing_time", [])
            )
            avg_rag_time = self._calculate_average(
                self._performance_metrics.get("rag_search_time", [])
            )
            avg_network_time = self._calculate_average(
                self._performance_metrics.get("network_search_time", [])
            )
            avg_memory_time = self._calculate_average(
                self._performance_metrics.get("memory_summary_time", [])
            )

            # 计算运行时间
            start_time = datetime.fromisoformat(self._global_metrics["start_time"])
            uptime_seconds = (datetime.utcnow() - start_time).total_seconds()

            return {
                **self._global_metrics,
                "uptime_seconds": uptime_seconds,
                "active_sessions": len(self._session_metrics),
                "performance": {
                    "avg_message_processing_time": avg_message_time,
                    "avg_rag_search_time": avg_rag_time,
                    "avg_network_search_time": avg_network_time,
                    "avg_memory_summary_time": avg_memory_time
                }
            }

    async def get_all_sessions_metrics(self) -> List[Dict[str, Any]]:
        """
        获取所有会话指标

        Returns:
            所有会话指标列表
        """
        async with self._lock:
            return list(self._session_metrics.values())

    async def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计

        Returns:
            性能统计数据
        """
        async with self._lock:
            stats = {}

            for metric_name, values in self._performance_metrics.items():
                if values:
                    stats[metric_name] = {
                        "count": len(values),
                        "avg": self._calculate_average(values),
                        "min": min(values),
                        "max": max(values),
                        "p50": self._calculate_percentile(values, 50),
                        "p95": self._calculate_percentile(values, 95),
                        "p99": self._calculate_percentile(values, 99)
                    }

            return stats

    async def cleanup_old_sessions(self, hours: int = 24) -> int:
        """
        清理旧会话数据

        Args:
            hours: 保留时间（小时）

        Returns:
            清理的会话数
        """
        async with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            sessions_to_remove = []

            for session_id, metrics in self._session_metrics.items():
                last_activity = datetime.fromisoformat(metrics["last_activity"])
                if last_activity < cutoff_time:
                    sessions_to_remove.append(session_id)

            for session_id in sessions_to_remove:
                del self._session_metrics[session_id]

            logger.info(f"清理了 {len(sessions_to_remove)} 个旧会话")

            return len(sessions_to_remove)

    def _calculate_average(self, values: List[float]) -> float:
        """计算平均值"""
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    async def reset_metrics(self) -> None:
        """重置所有指标"""
        async with self._lock:
            self._session_metrics.clear()
            self._performance_metrics.clear()
            self._global_metrics = {
                "total_sessions": 0,
                "total_messages": 0,
                "rag_enhanced_sessions": 0,
                "network_searches": 0,
                "rag_searches": 0,
                "mode_switches": 0,
                "memory_summaries": 0,
                "start_time": datetime.utcnow().isoformat()
            }

            logger.info("监控指标已重置")


# 全局监控实例
_monitor = None


def get_conversation_monitor() -> ConversationMonitor:
    """获取全局对话监控实例"""
    global _monitor
    if _monitor is None:
        _monitor = ConversationMonitor()
    return _monitor
