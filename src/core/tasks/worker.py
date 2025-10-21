# -*- coding: utf-8 -*-
"""
任务工作器：注册和启动异步任务处理器
"""

import asyncio
import logging
from typing import Dict, Any

from .queue import get_task_queue, TaskQueue
from .document_processor import process_document_task

logger = logging.getLogger(__name__)


class TaskWorker:
    """任务工作器管理器"""
    
    def __init__(self):
        self.queue: TaskQueue = None
        self.is_running = False
    
    async def initialize(self):
        """初始化工作器"""
        self.queue = await get_task_queue()
        
        # 注册任务处理器
        self.register_handlers()
        
        logger.info("任务工作器已初始化")
    
    def register_handlers(self):
        """注册任务处理器"""
        # 注册文档处理任务
        self.queue.register_handler("process_document", process_document_task)
        
        logger.info("已注册任务处理器: process_document")
    
    async def start(self, worker_count: int = 2, concurrency: int = 1):
        """启动工作器"""
        if self.is_running:
            return
        
        if not self.queue:
            await self.initialize()
        
        # 启动多个工作进程
        for i in range(worker_count):
            worker_id = f"worker_{i}"
            await self.queue.start_worker(worker_id, concurrency)
            logger.info(f"启动工作器: {worker_id}")
        
        self.is_running = True
        logger.info(f"任务工作器已启动，工作进程数: {worker_count}")
    
    async def stop(self):
        """停止工作器"""
        if not self.is_running:
            return
        
        if self.queue:
            await self.queue.stop_all_workers()
        
        self.is_running = False
        logger.info("任务工作器已停止")
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取工作器统计信息"""
        if not self.queue:
            return {"status": "not_initialized"}
        
        stats = await self.queue.get_queue_stats()
        stats["is_running"] = self.is_running
        return stats


# 全局工作器实例
_task_worker: TaskWorker = None


async def get_task_worker() -> TaskWorker:
    """获取任务工作器实例"""
    global _task_worker
    if _task_worker is None:
        _task_worker = TaskWorker()
        await _task_worker.initialize()
    return _task_worker


async def start_task_worker(worker_count: int = 2, concurrency: int = 1):
    """启动任务工作器"""
    worker = await get_task_worker()
    await worker.start(worker_count, concurrency)


async def stop_task_worker():
    """停止任务工作器"""
    worker = await get_task_worker()
    await worker.stop()