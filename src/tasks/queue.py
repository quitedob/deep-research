# -*- coding: utf-8 -*-
"""
异步任务队列：使用 Redis 作为消息代理，支持文档处理的异步化。
经过重构，增强了错误处理、任务超时和状态管理的健壮性。
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum

import redis.asyncio as redis
from pydantic import BaseModel, Field
from src.config.config_loader import get_settings

settings = get_settings()


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class Task(BaseModel):
    """任务模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    args: list = Field(default_factory=list)
    kwargs: dict = Field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Any] = None
    retries: int = 0
    max_retries: int = 3
    timeout_seconds: int = 600  # 10分钟默认超时


class TaskQueue:
    """任务队列管理器"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.redis_url
        self.redis: Optional[redis.Redis] = None
        self.workers: Dict[str, asyncio.Task] = {}
        self.task_handlers: Dict[str, Callable] = {}
        self.is_running = False
        
    async def connect(self):
        """连接到 Redis"""
        if not self.redis:
            self.redis = redis.from_url(self.redis_url)
            await self.redis.ping()
    
    async def disconnect(self):
        """断开 Redis 连接"""
        if self.redis:
            await self.redis.close()
            self.redis = None
    
    async def enqueue(
        self,
        task_name: str,
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout_seconds: int = 600,
        **kwargs
    ) -> Task:
        """将任务加入队列"""
        await self.connect()

        task = Task(
            name=task_name,
            args=list(args),
            kwargs=kwargs,
            priority=priority,
            timeout_seconds=timeout_seconds
        )

        # 将任务序列化并存储到 Redis
        task_data = task.model_dump_json()

        # 使用管道确保原子性
        async with self.redis.pipeline() as pipe:
            pipe.lpush(f"task_queue:{priority.value}", task.id)
            pipe.set(f"task_detail:{task.id}", task_data, ex=timedelta(hours=24))
            await pipe.execute()

        return task
    
    async def dequeue(self) -> Optional[Task]:
        """从队列中取出任务（按优先级顺序）"""
        await self.connect()

        # 按优先级从高到低尝试获取任务
        for p in range(TaskPriority.URGENT.value, TaskPriority.LOW.value - 1, -1):
            task_id = await self.redis.rpop(f"task_queue:{p}")
            if task_id:
                task_data = await self.redis.get(f"task_detail:{task_id}")
                if task_data:
                    task = Task.model_validate_json(task_data)
                    return task

        return None
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务详情"""
        await self.connect()

        task_data = await self.redis.get(f"task_detail:{task_id}")
        if task_data:
            return Task.model_validate_json(task_data)
        return None
    
    async def update_task(self, task: Task) -> None:
        """更新任务详情"""
        await self.connect()
        await self.redis.setex(
            f"task_detail:{task.id}",
            timedelta(hours=24),
            task.model_dump_json()
        )
    
    async def retry_task(self, task: Task) -> bool:
        """重试失败的任务"""
        if task.retries >= task.max_retries:
            return False

        # 增加重试次数
        task.retries += 1
        task.status = TaskStatus.PENDING
        task.error_message = None
        task.started_at = None
        task.completed_at = None

        # 重新加入队列
        async with self.redis.pipeline() as pipe:
            pipe.lpush(f"task_queue:{task.priority.value}", task.id)
            pipe.setex(f"task_detail:{task.id}", timedelta(hours=24), task.model_dump_json())
            await pipe.execute()

        return True
    
    def register_handler(self, task_name: str, handler: Callable):
        """注册任务处理器"""
        self.task_handlers[task_name] = handler
    
    async def start_worker(self, worker_id: str, concurrency: int = 1):
        """启动工作进程"""
        if worker_id in self.workers:
            return
        
        self.workers[worker_id] = asyncio.create_task(
            self._worker_loop(worker_id, concurrency)
        )
    
    async def stop_worker(self, worker_id: str):
        """停止工作进程"""
        if worker_id in self.workers:
            self.workers[worker_id].cancel()
            try:
                await self.workers[worker_id]
            except asyncio.CancelledError:
                pass
            del self.workers[worker_id]
    
    async def stop_all_workers(self):
        """停止所有工作进程"""
        for worker_id in list(self.workers.keys()):
            await self.stop_worker(worker_id)
    
    async def _worker_loop(self, worker_id: str, concurrency: int):
        """工作进程主循环"""
        semaphore = asyncio.Semaphore(concurrency)
        
        while True:
            try:
                # 获取任务
                task = await self.dequeue()
                if not task:
                    await asyncio.sleep(1)
                    continue
                
                # 使用信号量控制并发
                async with semaphore:
                    await self._process_task(task, worker_id)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker {worker_id} error: {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_task(self, task: Task, worker_id: str):
        """处理单个任务（包含超时控制）"""
        try:
            # 更新任务状态为处理中
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.utcnow()
            await self.update_task(task)

            # 获取任务处理器
            handler = self.task_handlers.get(task.name)
            if not handler:
                raise ValueError(f"No handler registered for task: {task.name}")

            # 使用超时控制执行任务
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await asyncio.wait_for(
                        handler(*task.args, **task.kwargs),
                        timeout=task.timeout_seconds
                    )
                else:
                    # 如果是同步函数，在线程池中执行
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, handler, *task.args, **task.kwargs),
                        timeout=task.timeout_seconds
                    )

                # 更新任务状态为完成
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                task.result = result
                await self.update_task(task)

            except asyncio.TimeoutError:
                # 任务超时
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                task.error_message = f"Task timed out after {task.timeout_seconds} seconds"
                await self.update_task(task)

                # 超时任务不重试，直接失败
                return

        except Exception as e:
            # 更新任务状态为失败
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error_message = str(e)
            await self.update_task(task)

            # 如果还有重试次数，重新加入队列
            if task.retries < task.max_retries:
                await self.retry_task(task)
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        await self.connect()

        stats = {
            "pending_tasks": 0,
            "active_workers": len(self.workers),
            "registered_handlers": list(self.task_handlers.keys())
        }

        # 统计各优先级队列中的任务数量
        for priority in TaskPriority:
            queue_name = f"task_queue:{priority.value}"
            count = await self.redis.llen(queue_name)
            stats[f"priority_{priority.name.lower()}_tasks"] = count
            stats["pending_tasks"] += count

        return stats


# 全局任务队列实例
task_queue: Optional[TaskQueue] = None


async def get_task_queue() -> TaskQueue:
    """获取任务队列实例（单例模式）"""
    global task_queue
    if task_queue is None:
        task_queue = TaskQueue()
        await task_queue.connect()
    return task_queue


async def enqueue_task(
    task_name: str,
    *args,
    priority: TaskPriority = TaskPriority.NORMAL,
    timeout_seconds: int = 600,
    **kwargs
) -> Task:
    """便捷函数：将任务加入队列"""
    queue = await get_task_queue()
    return await queue.enqueue(task_name, *args, priority=priority, timeout_seconds=timeout_seconds, **kwargs)


async def get_task_status(task_id: str) -> Optional[Task]:
    """便捷函数：获取任务状态"""
    queue = await get_task_queue()
    return await queue.get_task(task_id)
