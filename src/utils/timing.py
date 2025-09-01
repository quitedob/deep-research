# -*- coding: utf-8 -*-
"""
时间测量和性能监控工具
提供函数执行时间统计、性能基准测试和延迟跟踪功能
"""

import time
import logging
import functools
import asyncio
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager, asynccontextmanager
import threading
import statistics

logger = logging.getLogger(__name__)


@dataclass
class TimingRecord:
    """时间记录数据类"""
    name: str
    start_time: float
    end_time: float
    duration_ms: float
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        """返回持续时间（秒）"""
        return self.duration_ms / 1000


@dataclass
class TimingStats:
    """时间统计数据类"""
    name: str
    count: int = 0
    total_ms: float = 0.0
    min_ms: float = float('inf')
    max_ms: float = 0.0
    avg_ms: float = 0.0
    median_ms: float = 0.0
    p95_ms: float = 0.0
    success_count: int = 0
    error_count: int = 0
    recent_times: List[float] = field(default_factory=list)
    
    def update(self, duration_ms: float, success: bool = True):
        """更新统计信息"""
        self.count += 1
        self.total_ms += duration_ms
        self.min_ms = min(self.min_ms, duration_ms)
        self.max_ms = max(self.max_ms, duration_ms)
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        
        # 保持最近100次的记录用于计算中位数和P95
        self.recent_times.append(duration_ms)
        if len(self.recent_times) > 100:
            self.recent_times.pop(0)
        
        # 重新计算统计值
        self.avg_ms = self.total_ms / self.count
        if self.recent_times:
            self.median_ms = statistics.median(self.recent_times)
            self.p95_ms = statistics.quantiles(self.recent_times, n=20)[18] if len(self.recent_times) >= 20 else self.max_ms


class PerformanceTimer:
    """性能计时器"""
    
    def __init__(self, max_records: int = 10000):
        """初始化性能计时器"""
        self.max_records = max_records
        self.records: List[TimingRecord] = []
        self.stats: Dict[str, TimingStats] = {}
        self._lock = threading.Lock()
    
    def start_timer(self, name: str) -> float:
        """开始计时"""
        return time.perf_counter()
    
    def end_timer(self, name: str, start_time: float, 
                  success: bool = True, error_message: Optional[str] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> TimingRecord:
        """结束计时并记录"""
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        record = TimingRecord(
            name=name,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        with self._lock:
            # 添加记录
            self.records.append(record)
            
            # 限制记录数量
            if len(self.records) > self.max_records:
                self.records.pop(0)
            
            # 更新统计
            if name not in self.stats:
                self.stats[name] = TimingStats(name=name)
            
            self.stats[name].update(duration_ms, success)
        
        logger.debug(f"Timer '{name}': {duration_ms:.2f}ms")
        return record
    
    def get_stats(self, name: Optional[str] = None) -> Union[TimingStats, Dict[str, TimingStats]]:
        """获取统计信息"""
        with self._lock:
            if name:
                return self.stats.get(name, TimingStats(name=name))
            return dict(self.stats)
    
    def get_recent_records(self, name: Optional[str] = None, 
                          limit: int = 100) -> List[TimingRecord]:
        """获取最近的记录"""
        with self._lock:
            records = self.records
            if name:
                records = [r for r in records if r.name == name]
            return records[-limit:]
    
    def clear_stats(self, name: Optional[str] = None):
        """清除统计信息"""
        with self._lock:
            if name:
                if name in self.stats:
                    del self.stats[name]
                self.records = [r for r in self.records if r.name != name]
            else:
                self.stats.clear()
                self.records.clear()
        
        logger.info(f"Cleared timer stats: {name or 'all'}")
    
    def get_summary_report(self) -> Dict[str, Any]:
        """获取性能摘要报告"""
        with self._lock:
            total_records = len(self.records)
            total_errors = sum(1 for r in self.records if not r.success)
            
            # 最慢的操作
            slowest_operations = sorted(
                [(name, stats.max_ms) for name, stats in self.stats.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            # 最频繁的操作
            most_frequent_operations = sorted(
                [(name, stats.count) for name, stats in self.stats.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return {
                "total_records": total_records,
                "total_errors": total_errors,
                "error_rate": total_errors / total_records if total_records > 0 else 0.0,
                "slowest_operations": slowest_operations,
                "most_frequent_operations": most_frequent_operations,
                "stats_by_operation": {
                    name: {
                        "count": stats.count,
                        "avg_ms": stats.avg_ms,
                        "min_ms": stats.min_ms,
                        "max_ms": stats.max_ms,
                        "median_ms": stats.median_ms,
                        "p95_ms": stats.p95_ms,
                        "success_rate": stats.success_count / stats.count if stats.count > 0 else 0.0
                    }
                    for name, stats in self.stats.items()
                }
            }


# 全局性能计时器实例
performance_timer = PerformanceTimer()


@contextmanager
def timer(name: str, metadata: Optional[Dict[str, Any]] = None):
    """上下文管理器形式的计时器"""
    start_time = performance_timer.start_timer(name)
    success = True
    error_message = None
    
    try:
        yield
    except Exception as e:
        success = False
        error_message = str(e)
        raise
    finally:
        performance_timer.end_timer(
            name=name,
            start_time=start_time,
            success=success,
            error_message=error_message,
            metadata=metadata
        )


@asynccontextmanager
async def async_timer(name: str, metadata: Optional[Dict[str, Any]] = None):
    """异步上下文管理器形式的计时器"""
    start_time = performance_timer.start_timer(name)
    success = True
    error_message = None
    
    try:
        yield
    except Exception as e:
        success = False
        error_message = str(e)
        raise
    finally:
        performance_timer.end_timer(
            name=name,
            start_time=start_time,
            success=success,
            error_message=error_message,
            metadata=metadata
        )


def timed(name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
    """函数装饰器形式的计时器"""
    def decorator(func: Callable) -> Callable:
        timer_name = name or f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                async with async_timer(timer_name, metadata):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with timer(timer_name, metadata):
                    return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator


class BenchmarkSuite:
    """基准测试套件"""
    
    def __init__(self, name: str):
        self.name = name
        self.benchmarks: List[Dict[str, Any]] = []
        self.results: Dict[str, List[float]] = {}
    
    def add_benchmark(self, name: str, func: Callable, 
                     iterations: int = 10, warmup: int = 2,
                     args: tuple = (), kwargs: Optional[Dict] = None):
        """添加基准测试"""
        self.benchmarks.append({
            "name": name,
            "func": func,
            "iterations": iterations,
            "warmup": warmup,
            "args": args,
            "kwargs": kwargs or {}
        })
    
    async def run_benchmarks(self) -> Dict[str, Dict[str, float]]:
        """运行所有基准测试"""
        logger.info(f"Running benchmark suite: {self.name}")
        results = {}
        
        for benchmark in self.benchmarks:
            name = benchmark["name"]
            func = benchmark["func"]
            iterations = benchmark["iterations"]
            warmup = benchmark["warmup"]
            args = benchmark["args"]
            kwargs = benchmark["kwargs"]
            
            logger.info(f"Running benchmark: {name}")
            
            # 预热
            for _ in range(warmup):
                if asyncio.iscoroutinefunction(func):
                    await func(*args, **kwargs)
                else:
                    func(*args, **kwargs)
            
            # 实际测试
            times = []
            for i in range(iterations):
                start_time = time.perf_counter()
                
                try:
                    if asyncio.iscoroutinefunction(func):
                        await func(*args, **kwargs)
                    else:
                        func(*args, **kwargs)
                    
                    end_time = time.perf_counter()
                    duration_ms = (end_time - start_time) * 1000
                    times.append(duration_ms)
                    
                except Exception as e:
                    logger.error(f"Benchmark {name} iteration {i} failed: {e}")
                    continue
            
            if times:
                results[name] = {
                    "iterations": len(times),
                    "min_ms": min(times),
                    "max_ms": max(times),
                    "avg_ms": sum(times) / len(times),
                    "median_ms": statistics.median(times),
                    "p95_ms": statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times),
                    "total_ms": sum(times)
                }
                
                logger.info(f"Benchmark {name} completed: avg={results[name]['avg_ms']:.2f}ms")
            else:
                logger.warning(f"Benchmark {name} produced no valid results")
        
        return results
    
    def print_results(self, results: Dict[str, Dict[str, float]]):
        """打印基准测试结果"""
        print(f"\n=== Benchmark Results: {self.name} ===")
        print(f"{'Benchmark':<30} {'Iterations':<12} {'Avg (ms)':<12} {'Min (ms)':<12} {'Max (ms)':<12} {'P95 (ms)':<12}")
        print("-" * 90)
        
        for name, stats in results.items():
            print(f"{name:<30} {stats['iterations']:<12} {stats['avg_ms']:<12.2f} "
                  f"{stats['min_ms']:<12.2f} {stats['max_ms']:<12.2f} {stats['p95_ms']:<12.2f}")


class LatencyTracker:
    """延迟跟踪器 - 专门用于网络请求和API调用的延迟监控"""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.latencies: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
    
    def record_latency(self, operation: str, latency_ms: float):
        """记录延迟"""
        with self._lock:
            if operation not in self.latencies:
                self.latencies[operation] = []
            
            self.latencies[operation].append(latency_ms)
            
            # 保持窗口大小
            if len(self.latencies[operation]) > self.window_size:
                self.latencies[operation].pop(0)
    
    def get_latency_stats(self, operation: str) -> Optional[Dict[str, float]]:
        """获取延迟统计"""
        with self._lock:
            if operation not in self.latencies or not self.latencies[operation]:
                return None
            
            latencies = self.latencies[operation]
            return {
                "count": len(latencies),
                "avg_ms": sum(latencies) / len(latencies),
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "median_ms": statistics.median(latencies),
                "p95_ms": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
                "p99_ms": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
            }
    
    def is_healthy(self, operation: str, max_avg_ms: float = 1000, 
                   max_p95_ms: float = 5000) -> bool:
        """检查操作延迟是否健康"""
        stats = self.get_latency_stats(operation)
        if not stats:
            return True  # 没有数据时认为健康
        
        return (stats["avg_ms"] <= max_avg_ms and 
                stats["p95_ms"] <= max_p95_ms)


# 全局延迟跟踪器实例
latency_tracker = LatencyTracker()


def track_latency(operation: str):
    """延迟跟踪装饰器"""
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    return await func(*args, **kwargs)
                finally:
                    end_time = time.perf_counter()
                    latency_ms = (end_time - start_time) * 1000
                    latency_tracker.record_latency(operation, latency_ms)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                finally:
                    end_time = time.perf_counter()
                    latency_ms = (end_time - start_time) * 1000
                    latency_tracker.record_latency(operation, latency_ms)
            return sync_wrapper
    
    return decorator


# 便捷函数
def measure_time(func: Callable, *args, **kwargs) -> tuple:
    """测量函数执行时间，返回(结果, 执行时间毫秒)"""
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000
    return result, duration_ms


async def async_measure_time(coro) -> tuple:
    """测量协程执行时间，返回(结果, 执行时间毫秒)"""
    start_time = time.perf_counter()
    result = await coro
    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000
    return result, duration_ms
