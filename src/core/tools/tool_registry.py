# -*- coding: utf-8 -*-
"""
工具注册表 - 管理所有可用工具
"""
import logging
from typing import Dict, Optional, List

from .base_tool import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        logger.info("Tool Registry initialized")
    
    def register_tool(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def unregister_tool(self, tool_name: str):
        """注销工具"""
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self._tools.keys())
    
    def get_tool_schemas(self) -> List[Dict]:
        """获取所有工具的 schema"""
        return [tool.get_schema() for tool in self._tools.values()]


# 全局工具注册表实例
_tool_registry = None


def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
