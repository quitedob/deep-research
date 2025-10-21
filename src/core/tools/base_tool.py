# -*- coding: utf-8 -*-
"""
基础工具类
定义所有工具的通用接口和行为
"""

import time
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from src.config.logging.logging import get_logger

logger = get_logger("tools")


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    execution_time_ms: int = 0
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseTool(ABC):
    """工具基类"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._cache = {}
        self._cache_ttl = 300  # 5分钟缓存
        
    @abstractmethod
    def execute(self, query: str, **kwargs) -> ToolResult:
        """执行工具（同步）"""
        pass
    
    async def aexecute(self, query: str, **kwargs) -> ToolResult:
        """执行工具（异步）"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute, query, **kwargs)
    
    def _get_cache_key(self, query: str, **kwargs) -> str:
        """生成缓存键"""
        import hashlib
        key_data = f"{query}_{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[ToolResult]:
        """获取缓存结果"""
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                logger.debug(f"缓存命中: {self.name}")
                return cached_data
            else:
                # 清理过期缓存
                del self._cache[cache_key]
        return None
    
    def _set_cached_result(self, cache_key: str, result: ToolResult):
        """设置缓存结果"""
        self._cache[cache_key] = (result, time.time())
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info(f"已清空工具缓存: {self.name}")
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具的schema定义（用于LLM Function Calling）"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "查询或操作内容"
                    }
                },
                "required": ["query"]
            }
        }
    
    def _measure_time(self, func, *args, **kwargs):
        """测量执行时间的装饰器助手"""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = int((time.time() - start_time) * 1000)
            
            if isinstance(result, ToolResult):
                result.execution_time_ms = execution_time
                return result
            else:
                return ToolResult(
                    success=True,
                    data=result,
                    execution_time_ms=execution_time
                )
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error(f"工具执行失败 {self.name}: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time
            ) 