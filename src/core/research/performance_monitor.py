# -*- coding: utf-8 -*-
"""
Performance Monitoring and Optimization System for Research Platform
Provides comprehensive performance monitoring, metrics collection, and optimization
"""

import asyncio
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import threading
from enum import Enum

class MetricType(Enum):
    """Types of performance metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class PerformanceMetric:
    """Represents a performance metric"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""

@dataclass
class AgentPerformance:
    """Performance metrics for an agent"""
    agent_id: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_task_time: float = 0.0
    success_rate: float = 1.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    last_activity: Optional[datetime] = None
    total_execution_time: float = 0.0

@dataclass
class SystemPerformance:
    """Overall system performance metrics"""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_io: Dict[str, float] = field(default_factory=dict)
    active_agents: int = 0
    active_plans: int = 0
    queue_length: int = 0
    response_time: float = 0.0
    error_rate: float = 0.0
    throughput: float = 0.0

class PerformanceMonitor:
    """Comprehensive performance monitoring system"""

    def __init__(self, collection_interval: float = 5.0):
        self.logger = logging.getLogger(__name__)
        self.collection_interval = collection_interval
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.agent_metrics: Dict[str, AgentPerformance] = {}
        self.system_metrics: deque = deque(maxlen=1000)
        self.custom_metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.callbacks: List[Callable] = []
        self.alert_thresholds: Dict[str, Dict[str, float]] = {}

        # Performance counters
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self.histograms: Dict[str, List[float]] = defaultdict(list)

    async def start_monitoring(self):
        """Start performance monitoring"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Performance monitoring started")

    async def stop_monitoring(self):
        """Stop performance monitoring"""
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Performance monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                await self._collect_system_metrics()
                await self._check_alerts()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(1)

    async def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # System resource usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }

            # Create system performance record
            system_perf = SystemPerformance(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_io=network_io,
                active_agents=len(self.agent_metrics),
                active_plans=self.gauges.get('active_plans', 0),
                queue_length=self.gauges.get('queue_length', 0),
                response_time=self.gauges.get('response_time', 0),
                error_rate=self.counters.get('errors', 0) / max(self.counters.get('total_requests', 1), 1),
                throughput=self.counters.get('requests_per_second', 0)
            )

            self.system_metrics.append(system_perf)

            # Update gauges
            self.gauges['cpu_usage'] = cpu_percent
            self.gauges['memory_usage'] = memory.percent
            self.gauges['disk_usage'] = disk.percent

            # Notify callbacks
            for callback in self.callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(system_perf)
                    else:
                        callback(system_perf)
                except Exception as e:
                    self.logger.error(f"Callback error: {e}")

        except Exception as e:
            self.logger.error(f"System metrics collection failed: {e}")

    def record_agent_performance(
        self,
        agent_id: str,
        task_duration: float,
        success: bool,
        memory_usage: float = 0.0,
        cpu_usage: float = 0.0
    ):
        """Record performance metrics for an agent"""
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = AgentPerformance(agent_id=agent_id)

        agent_perf = self.agent_metrics[agent_id]

        if success:
            agent_perf.tasks_completed += 1
            # Update average task time
            total_tasks = agent_perf.tasks_completed + agent_perf.tasks_failed
            agent_perf.total_execution_time += task_duration
            agent_perf.average_task_time = agent_perf.total_execution_time / total_tasks
        else:
            agent_perf.tasks_failed += 1

        agent_perf.success_rate = agent_perf.tasks_completed / max(
            agent_perf.tasks_completed + agent_perf.tasks_failed, 1
        )
        agent_perf.memory_usage = memory_usage
        agent_perf.cpu_usage = cpu_usage
        agent_perf.last_activity = datetime.now()

        # Record metrics
        self.increment_counter('agent_tasks_completed', 1 if success else 0)
        self.set_gauge(f'agent_{agent_id}_success_rate', agent_perf.success_rate)
        self.set_gauge(f'agent_{agent_id}_avg_task_time', agent_perf.average_task_time)

    def record_task_execution(
        self,
        task_type: str,
        duration: float,
        success: bool,
        metadata: Dict[str, Any] = None
    ):
        """Record task execution metrics"""
        # Timer metric
        self.record_timer(f'task_duration_{task_type}', duration)

        # Counter metrics
        self.increment_counter('tasks_total')
        if success:
            self.increment_counter(f'tasks_success_{task_type}')
        else:
            self.increment_counter(f'tasks_failed_{task_type}')

        # Custom metric
        metric = PerformanceMetric(
            name=f'task_execution_{task_type}',
            value=duration,
            metric_type=MetricType.TIMER,
            tags={'success': str(success), **(metadata or {})},
            unit='seconds'
        )
        self.add_custom_metric(metric)

    def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float
    ):
        """Record HTTP request metrics"""
        # Timer for response time
        self.record_timer('request_duration', duration)
        self.record_timer(f'request_duration_{endpoint}', duration)

        # Counters
        self.increment_counter('requests_total')
        self.increment_counter(f'requests_{method}')
        self.increment_counter(f'requests_{endpoint}')
        self.increment_counter(f'requests_status_{status_code}')

        # Update response time gauge
        self.gauges['response_time'] = duration

        # Error rate
        if status_code >= 400:
            self.increment_counter('errors')

    def increment_counter(self, name: str, value: float = 1.0):
        """Increment a counter metric"""
        self.counters[name] += value

    def set_gauge(self, name: str, value: float):
        """Set a gauge metric"""
        self.gauges[name] = value

    def record_timer(self, name: str, value: float):
        """Record a timer metric"""
        self.timers[name].append(value)
        # Keep only last 1000 values
        if len(self.timers[name]) > 1000:
            self.timers[name] = self.timers[name][-1000:]

    def record_histogram(self, name: str, value: float):
        """Record a histogram metric"""
        self.histograms[name].append(value)
        # Keep only last 1000 values
        if len(self.histograms[name]) > 1000:
            self.histograms[name] = self.histograms[name][-1000:]

    def add_custom_metric(self, metric: PerformanceMetric):
        """Add a custom metric"""
        self.custom_metrics[metric.name].append(metric)
        # Keep only last 1000 values
        if len(self.custom_metrics[metric.name]) > 1000:
            self.custom_metrics[metric.name] = self.custom_metrics[metric.name][-1000:]

    def add_callback(self, callback: Callable):
        """Add a callback to be notified of new metrics"""
        self.callbacks.append(callback)

    def set_alert_threshold(self, metric_name: str, operator: str, threshold: float):
        """Set an alert threshold for a metric"""
        self.alert_thresholds[metric_name] = {
            'operator': operator,
            'threshold': threshold,
            'last_triggered': None
        }

    async def _check_alerts(self):
        """Check if any alert thresholds are exceeded"""
        for metric_name, alert_config in self.alert_thresholds.items():
            try:
                current_value = self._get_metric_value(metric_name)
                if current_value is None:
                    continue

                operator = alert_config['operator']
                threshold = alert_config['threshold']
                triggered = False

                if operator == '>' and current_value > threshold:
                    triggered = True
                elif operator == '<' and current_value < threshold:
                    triggered = True
                elif operator == '>=' and current_value >= threshold:
                    triggered = True
                elif operator == '<=' and current_value <= threshold:
                    triggered = True
                elif operator == '==' and current_value == threshold:
                    triggered = True

                if triggered:
                    last_triggered = alert_config.get('last_triggered')
                    now = datetime.now()

                    # Rate limit alerts to once per minute
                    if not last_triggered or (now - last_triggered).seconds > 60:
                        await self._trigger_alert(metric_name, current_value, threshold, operator)
                        alert_config['last_triggered'] = now

            except Exception as e:
                self.logger.error(f"Alert check failed for {metric_name}: {e}")

    def _get_metric_value(self, metric_name: str) -> Optional[float]:
        """Get current value for a metric"""
        if metric_name in self.gauges:
            return self.gauges[metric_name]
        elif metric_name in self.counters:
            return self.counters[metric_name]
        elif metric_name in self.timers and self.timers[metric_name]:
            return sum(self.timers[metric_name]) / len(self.timers[metric_name])
        else:
            # Try to get from system metrics
            if self.system_metrics:
                latest_system_metric = self.system_metrics[-1]
                return getattr(latest_system_metric, metric_name, None)
        return None

    async def _trigger_alert(self, metric_name: str, value: float, threshold: float, operator: str):
        """Trigger an alert"""
        self.logger.warning(
            f"Performance Alert: {metric_name} {operator} {threshold} (current: {value})"
        )
        # Here you could add additional alert mechanisms like:
        # - Sending notifications
        # - Creating system alerts in the database
        # - Triggering automated responses

    def get_performance_summary(self, time_window: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Get performance summary for a time window"""
        cutoff_time = datetime.now() - time_window

        # System metrics summary
        recent_system_metrics = [
            m for m in self.system_metrics
            if m.timestamp > cutoff_time
        ]

        if recent_system_metrics:
            avg_cpu = sum(m.cpu_usage for m in recent_system_metrics) / len(recent_system_metrics)
            avg_memory = sum(m.memory_usage for m in recent_system_metrics) / len(recent_system_metrics)
            max_response_time = max(m.response_time for m in recent_system_metrics)
            avg_error_rate = sum(m.error_rate for m in recent_system_metrics) / len(recent_system_metrics)
        else:
            avg_cpu = avg_memory = max_response_time = avg_error_rate = 0

        # Agent performance summary
        active_agents = [
            agent for agent in self.agent_metrics.values()
            if agent.last_activity and agent.last_activity > cutoff_time
        ]

        agent_summary = {
            'total_agents': len(self.agent_metrics),
            'active_agents': len(active_agents),
            'total_tasks_completed': sum(a.tasks_completed for a in self.agent_metrics.values()),
            'total_tasks_failed': sum(a.tasks_failed for a in self.agent_metrics.values()),
            'average_success_rate': sum(a.success_rate for a in active_agents) / len(active_agents) if active_agents else 0,
            'average_task_time': sum(a.average_task_time for a in active_agents) / len(active_agents) if active_agents else 0
        }

        # Request metrics
        total_requests = self.counters.get('requests_total', 0)
        total_errors = self.counters.get('errors', 0)
        error_rate = total_errors / max(total_requests, 1)

        return {
            'time_window_hours': time_window.total_seconds() / 3600,
            'system_performance': {
                'average_cpu_usage': avg_cpu,
                'average_memory_usage': avg_memory,
                'max_response_time': max_response_time,
                'average_error_rate': avg_error_rate
            },
            'agent_performance': agent_summary,
            'request_metrics': {
                'total_requests': total_requests,
                'total_errors': total_errors,
                'error_rate': error_rate,
                'average_response_time': sum(self.timers.get('request_duration', [])) / max(len(self.timers.get('request_duration', [])), 1)
            },
            'active_alerts': len([a for a in self.alert_thresholds.values() if a.get('last_triggered')]),
            'timestamp': datetime.now().isoformat()
        }

    def get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed metrics for all components"""
        return {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'timers': {
                name: {
                    'count': len(values),
                    'sum': sum(values),
                    'average': sum(values) / len(values) if values else 0,
                    'min': min(values) if values else 0,
                    'max': max(values) if values else 0
                }
                for name, values in self.timers.items()
            },
            'agents': {
                agent_id: {
                    'tasks_completed': agent.tasks_completed,
                    'tasks_failed': agent.tasks_failed,
                    'success_rate': agent.success_rate,
                    'average_task_time': agent.average_task_time,
                    'memory_usage': agent.memory_usage,
                    'cpu_usage': agent.cpu_usage,
                    'last_activity': agent.last_activity.isoformat() if agent.last_activity else None
                }
                for agent_id, agent in self.agent_metrics.items()
            },
            'system_metrics': [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'cpu_usage': m.cpu_usage,
                    'memory_usage': m.memory_usage,
                    'active_agents': m.active_agents,
                    'active_plans': m.active_plans,
                    'queue_length': m.queue_length,
                    'response_time': m.response_time,
                    'error_rate': m.error_rate,
                    'throughput': m.throughput
                }
                for m in list(self.system_metrics)[-100:]  # Last 100 metrics
            ]
        }

    def reset_metrics(self):
        """Reset all metrics"""
        self.counters.clear()
        self.gauges.clear()
        self.timers.clear()
        self.histograms.clear()
        self.custom_metrics.clear()
        self.agent_metrics.clear()
        self.system_metrics.clear()
        self.logger.info("All performance metrics reset")

# Performance monitoring decorator
def monitor_performance(metric_name: str = None, include_args: bool = False):
    """Decorator to monitor function performance"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            function_name = metric_name or f"{func.__module__}.{func.__name__}"

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Record metrics
                global_monitor.record_timer(f'{function_name}_duration', duration)
                global_monitor.increment_counter(f'{function_name}_calls')
                global_monitor.increment_counter(f'{function_name}_success')

                if include_args:
                    global_monitor.record_histogram(
                        f'{function_name}_args_count',
                        len(args) + len(kwargs)
                    )

                return result

            except Exception as e:
                duration = time.time() - start_time
                global_monitor.record_timer(f'{function_name}_duration', duration)
                global_monitor.increment_counter(f'{function_name}_calls')
                global_monitor.increment_counter(f'{function_name}_error')
                raise e

        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            function_name = metric_name or f"{func.__module__}.{func.__name__}"

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Record metrics
                global_monitor.record_timer(f'{function_name}_duration', duration)
                global_monitor.increment_counter(f'{function_name}_calls')
                global_monitor.increment_counter(f'{function_name}_success')

                return result

            except Exception as e:
                duration = time.time() - start_time
                global_monitor.record_timer(f'{function_name}_duration', duration)
                global_monitor.increment_counter(f'{function_name}_calls')
                global_monitor.increment_counter(f'{function_name}_error')
                raise e

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

# Global performance monitor instance
global_monitor = PerformanceMonitor()