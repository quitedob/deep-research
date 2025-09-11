# -*- coding: utf-8 -*-
"""
代码执行工具
提供安全的Python代码执行环境
"""

import sys
import io
import contextlib
import traceback
import ast
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .base_tool import BaseTool, ToolResult
from src.config.logging import get_logger

logger = get_logger("code_executor")


class CodeExecutorTool(BaseTool):
    """Python代码执行工具"""
    
    def __init__(self, timeout: int = 30):
        super().__init__(
            name="code_executor",
            description="执行Python代码并返回结果"
        )
        self.timeout = timeout
        self._setup_safe_globals()
    
    def _setup_safe_globals(self):
        """设置安全的全局变量环境"""
        # 允许的内置函数
        safe_builtins = {
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'chr', 'dict', 
            'dir', 'divmod', 'enumerate', 'filter', 'float', 'format',
            'hex', 'id', 'int', 'isinstance', 'iter', 'len', 'list', 
            'map', 'max', 'min', 'oct', 'ord', 'pow', 'print', 'range',
            'repr', 'reversed', 'round', 'set', 'slice', 'sorted', 'str',
            'sum', 'tuple', 'type', 'zip'
        }
        
        # 创建受限的内置函数字典
        restricted_builtins = {
            name: getattr(__builtins__, name) 
            for name in safe_builtins 
            if hasattr(__builtins__, name)
        }
        
        # 允许的模块
        self.allowed_modules = {
            'math', 'statistics', 'random', 'datetime', 'json', 're',
            'collections', 'itertools', 'functools', 'operator'
        }
        
        self.safe_globals = {
            '__builtins__': restricted_builtins,
            '__name__': '__main__',
        }
        
        # 预导入常用模块
        try:
            import math, statistics, random, datetime, json, re
            import collections, itertools, functools, operator
            
            self.safe_globals.update({
                'math': math,
                'statistics': statistics,
                'random': random,
                'datetime': datetime,
                'json': json,
                're': re,
                'collections': collections,
                'itertools': itertools,
                'functools': functools,
                'operator': operator,
            })
        except ImportError as e:
            logger.warning(f"某些模块导入失败: {e}")
    
    def execute(self, code: str, **kwargs) -> ToolResult:
        """执行Python代码"""
        return self._measure_time(self._execute_code, code, **kwargs)
    
    def _execute_code(self, code: str, **kwargs) -> ToolResult:
        """实际执行代码"""
        try:
            # 验证代码安全性
            security_check = self._check_code_security(code)
            if not security_check["safe"]:
                return ToolResult(
                    success=False,
                    error=f"代码安全检查失败: {security_check['reason']}",
                    metadata={"security_violation": True}
                )
            
            # 捕获输出
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            try:
                # 重定向输出
                sys.stdout = stdout_capture
                sys.stderr = stderr_capture
                
                # 创建本地变量环境
                local_vars = {}
                
                # 执行代码
                exec(code, self.safe_globals.copy(), local_vars)
                
                # 获取输出
                stdout_output = stdout_capture.getvalue()
                stderr_output = stderr_capture.getvalue()
                
                # 获取最后一个表达式的值（如果有）
                last_expr_value = None
                try:
                    # 尝试解析代码为AST
                    tree = ast.parse(code)
                    if tree.body and isinstance(tree.body[-1], ast.Expr):
                        # 最后一行是表达式，尝试获取其值
                        last_expr = ast.Expression(tree.body[-1].value)
                        last_expr_value = eval(compile(last_expr, '<string>', 'eval'), 
                                              self.safe_globals.copy(), local_vars)
                except:
                    # 如果无法获取表达式值，忽略
                    pass
                
                # 构建结果
                result_data = {
                    "stdout": stdout_output,
                    "stderr": stderr_output,
                    "variables": {k: str(v) for k, v in local_vars.items() 
                                 if not k.startswith('_')},
                    "last_expression": str(last_expr_value) if last_expr_value is not None else None
                }
                
                return ToolResult(
                    success=True,
                    data=result_data,
                    metadata={
                        "code_lines": len(code.splitlines()),
                        "variables_count": len(local_vars),
                        "has_output": bool(stdout_output or stderr_output)
                    }
                )
                
            finally:
                # 恢复输出
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            traceback_str = traceback.format_exc()
            
            logger.error(f"代码执行失败: {error_msg}")
            
            return ToolResult(
                success=False,
                error=error_msg,
                metadata={
                    "traceback": traceback_str,
                    "error_type": type(e).__name__
                }
            )
    
    def _check_code_security(self, code: str) -> Dict[str, Any]:
        """检查代码安全性"""
        try:
            # 解析AST
            tree = ast.parse(code)
            
            # 检查危险的AST节点
            dangerous_nodes = []
            
            for node in ast.walk(tree):
                # 检查危险的函数调用
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        if func_name in ['exec', 'eval', 'compile', '__import__', 'open', 'input']:
                            dangerous_nodes.append(f"危险函数调用: {func_name}")
                    elif isinstance(node.func, ast.Attribute):
                        if node.func.attr in ['system', 'popen', 'spawn']:
                            dangerous_nodes.append(f"危险方法调用: {node.func.attr}")
                
                # 检查导入语句
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in self.allowed_modules:
                            dangerous_nodes.append(f"不允许的模块导入: {alias.name}")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module not in self.allowed_modules:
                        dangerous_nodes.append(f"不允许的模块导入: {node.module}")
                
                # 检查属性访问
                elif isinstance(node, ast.Attribute):
                    if node.attr.startswith('_'):
                        dangerous_nodes.append(f"访问私有属性: {node.attr}")
            
            if dangerous_nodes:
                return {
                    "safe": False,
                    "reason": "; ".join(dangerous_nodes[:3])  # 只显示前3个问题
                }
            
            return {"safe": True, "reason": "代码安全检查通过"}
            
        except SyntaxError as e:
            return {
                "safe": False,
                "reason": f"语法错误: {str(e)}"
            }
        except Exception as e:
            return {
                "safe": False,
                "reason": f"代码分析失败: {str(e)}"
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具的schema定义"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "要执行的Python代码"
                    }
                },
                "required": ["code"]
            }
        }


# 创建全局实例
code_executor = CodeExecutorTool() 