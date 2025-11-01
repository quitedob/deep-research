#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一工具管理系统
基于AgentScope的Toolkit实现工具分组和管理
"""
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """工具分类"""
    SEARCH = "search"
    DOCUMENT = "document"
    CODE = "code"
    ANALYSIS = "analysis"
    COMMUNICATION = "communication"
    DATABASE = "database"
    WEB = "web"
    UTILITY = "utility"


class ToolResponseType(str, Enum):
    """工具响应类型"""
    TEXT = "text"
    JSON = "json"
    STREAM = "stream"
    BINARY = "binary"
    ERROR = "error"


@dataclass
class ToolResponse:
    """结构化工具响应"""
    success: bool
    data: Any
    response_type: ToolResponseType = ToolResponseType.TEXT
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "response_type": self.response_type.value,
            "metadata": self.metadata,
            "error": self.error
        }
    
    def to_text(self) -> str:
        """转换为文本"""
        if not self.success:
            return f"Error: {self.error}"
        
        if self.response_type == ToolResponseType.TEXT:
            return str(self.data)
        elif self.response_type == ToolResponseType.JSON:
            import json
            return json.dumps(self.data, ensure_ascii=False, indent=2)
        else:
            return str(self.data)


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    function: Callable
    category: ToolCategory
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_async: bool = False
    requires_auth: bool = False
    rate_limit: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_openai_format(self) -> Dict[str, Any]:
        """转换为OpenAI函数调用格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class Toolkit:
    """统一工具管理器"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._tools: Dict[str, ToolDefinition] = {}
        self._categories: Dict[ToolCategory, List[str]] = {}
        self._call_count: Dict[str, int] = {}
        
    def register_tool(
        self,
        name: str,
        function: Callable,
        description: str,
        category: ToolCategory,
        parameters: Optional[Dict[str, Any]] = None,
        is_async: bool = False,
        **kwargs
    ) -> None:
        """注册工具"""
        tool = ToolDefinition(
            name=name,
            description=description,
            function=function,
            category=category,
            parameters=parameters or {},
            is_async=is_async,
            **kwargs
        )
        
        self._tools[name] = tool
        
        # 添加到分类索引
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(name)
        
        # 初始化调用计数
        self._call_count[name] = 0
        
        logger.info(f"Registered tool: {name} in category {category.value}")
    
    def tool(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: ToolCategory = ToolCategory.UTILITY,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """装饰器：注册工具函数"""
        def decorator(func: Callable):
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or "No description"
            is_async = asyncio.iscoroutinefunction(func)
            
            self.register_tool(
                name=tool_name,
                function=func,
                description=tool_desc,
                category=category,
                parameters=parameters,
                is_async=is_async,
                **kwargs
            )
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self.call_tool(tool_name, *args, **kwargs)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self.call_tool_sync(tool_name, *args, **kwargs)
            
            return async_wrapper if is_async else sync_wrapper
        
        return decorator
    
    async def call_tool(
        self,
        tool_name: str,
        *args,
        **kwargs
    ) -> ToolResponse:
        """异步调用工具"""
        if tool_name not in self._tools:
            return ToolResponse(
                success=False,
                data=None,
                response_type=ToolResponseType.ERROR,
                error=f"Tool '{tool_name}' not found"
            )
        
        tool = self._tools[tool_name]
        self._call_count[tool_name] += 1
        
        try:
            if tool.is_async:
                result = await tool.function(*args, **kwargs)
            else:
                result = tool.function(*args, **kwargs)
            
            # 如果结果已经是ToolResponse，直接返回
            if isinstance(result, ToolResponse):
                return result
            
            # 否则包装为ToolResponse
            return ToolResponse(
                success=True,
                data=result,
                response_type=ToolResponseType.TEXT,
                metadata={"tool_name": tool_name, "category": tool.category.value}
            )
            
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}': {e}")
            return ToolResponse(
                success=False,
                data=None,
                response_type=ToolResponseType.ERROR,
                error=str(e),
                metadata={"tool_name": tool_name}
            )
    
    def call_tool_sync(
        self,
        tool_name: str,
        *args,
        **kwargs
    ) -> ToolResponse:
        """同步调用工具"""
        if tool_name not in self._tools:
            return ToolResponse(
                success=False,
                data=None,
                response_type=ToolResponseType.ERROR,
                error=f"Tool '{tool_name}' not found"
            )
        
        tool = self._tools[tool_name]
        
        if tool.is_async:
            return ToolResponse(
                success=False,
                data=None,
                response_type=ToolResponseType.ERROR,
                error=f"Tool '{tool_name}' is async, use call_tool() instead"
            )
        
        self._call_count[tool_name] += 1
        
        try:
            result = tool.function(*args, **kwargs)
            
            if isinstance(result, ToolResponse):
                return result
            
            return ToolResponse(
                success=True,
                data=result,
                response_type=ToolResponseType.TEXT,
                metadata={"tool_name": tool_name, "category": tool.category.value}
            )
            
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}': {e}")
            return ToolResponse(
                success=False,
                data=None,
                response_type=ToolResponseType.ERROR,
                error=str(e),
                metadata={"tool_name": tool_name}
            )
    
    def get_tool(self, tool_name: str) -> Optional[ToolDefinition]:
        """获取工具定义"""
        return self._tools.get(tool_name)
    
    def list_tools(
        self,
        category: Optional[ToolCategory] = None
    ) -> List[ToolDefinition]:
        """列出工具"""
        if category:
            tool_names = self._categories.get(category, [])
            return [self._tools[name] for name in tool_names]
        return list(self._tools.values())
    
    def get_tools_by_category(self) -> Dict[str, List[str]]:
        """按分类获取工具"""
        return {
            cat.value: tools
            for cat, tools in self._categories.items()
        }
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """获取工具统计信息"""
        return {
            "total_tools": len(self._tools),
            "categories": {
                cat.value: len(tools)
                for cat, tools in self._categories.items()
            },
            "call_counts": self._call_count.copy(),
            "most_used": max(self._call_count.items(), key=lambda x: x[1])[0]
            if self._call_count else None
        }
    
    def to_openai_tools(
        self,
        category: Optional[ToolCategory] = None
    ) -> List[Dict[str, Any]]:
        """转换为OpenAI工具格式"""
        tools = self.list_tools(category)
        return [tool.to_openai_format() for tool in tools]
    
    def remove_tool(self, tool_name: str) -> bool:
        """移除工具"""
        if tool_name not in self._tools:
            return False
        
        tool = self._tools[tool_name]
        del self._tools[tool_name]
        
        # 从分类索引中移除
        if tool.category in self._categories:
            self._categories[tool.category].remove(tool_name)
        
        # 移除调用计数
        if tool_name in self._call_count:
            del self._call_count[tool_name]
        
        logger.info(f"Removed tool: {tool_name}")
        return True


# 全局工具管理器
_global_toolkit = Toolkit(name="global", description="Global toolkit")


def get_global_toolkit() -> Toolkit:
    """获取全局工具管理器"""
    return _global_toolkit


def register_global_tool(*args, **kwargs):
    """注册全局工具"""
    return _global_toolkit.register_tool(*args, **kwargs)


def tool(*args, **kwargs):
    """全局工具装饰器"""
    return _global_toolkit.tool(*args, **kwargs)
