# -*- coding: utf-8 -*-
"""
安全的Python代码执行工具
提供沙盒环境执行代码，支持AST安全检查
"""

import ast
import sys
import io
import os
import contextlib
import subprocess
import tempfile
import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class CodeExecutionResult:
    """代码执行结果"""
    success: bool
    output: str
    error: str = ""
    execution_time: float = 0.0
    variables: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "variables": self.variables or {}
        }

class SecurityChecker:
    """代码安全检查器"""
    
    # 危险的模块和函数
    DANGEROUS_IMPORTS = {
        'os', 'sys', 'subprocess', 'socket', 'urllib', 'http', 'ftplib',
        'smtplib', 'poplib', 'imaplib', 'telnetlib', 'xmlrpc', 'pickle',
        'marshal', 'shelve', 'dbm', 'sqlite3', 'mysql', 'pymongo',
        'ctypes', '__builtin__', 'builtins', 'importlib', 'imp'
    }
    
    DANGEROUS_FUNCTIONS = {
        'exec', 'eval', 'compile', 'open', 'file', 'input', 'raw_input',
        '__import__', 'reload', 'execfile', 'exit', 'quit', 'help'
    }
    
    DANGEROUS_ATTRIBUTES = {
        '__class__', '__bases__', '__subclasses__', '__mro__', '__globals__',
        '__code__', '__func__', '__self__', '__module__', '__dict__'
    }
    
    def __init__(self):
        self.errors = []
        
    def check_code(self, code: str) -> bool:
        """检查代码是否安全"""
        self.errors = []
        
        try:
            tree = ast.parse(code)
            self.visit_node(tree)
            return len(self.errors) == 0
        except SyntaxError as e:
            self.errors.append(f"Syntax error: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Parse error: {e}")
            return False
    
    def visit_node(self, node):
        """访问AST节点"""
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in self.DANGEROUS_IMPORTS:
                    self.errors.append(f"Dangerous import: {alias.name}")
        
        elif isinstance(node, ast.ImportFrom):
            if node.module in self.DANGEROUS_IMPORTS:
                self.errors.append(f"Dangerous import from: {node.module}")
        
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in self.DANGEROUS_FUNCTIONS:
                    self.errors.append(f"Dangerous function call: {node.func.id}")
        
        elif isinstance(node, ast.Attribute):
            if node.attr in self.DANGEROUS_ATTRIBUTES:
                self.errors.append(f"Dangerous attribute access: {node.attr}")
        
        # 递归检查子节点
        for child in ast.iter_child_nodes(node):
            self.visit_node(child)
    
    def get_errors(self) -> List[str]:
        """获取安全检查错误"""
        return self.errors

class SecurePythonExecutor:
    """安全的Python代码执行器"""
    
    def __init__(self, timeout: int = 30, memory_limit_mb: int = 100):
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb
        self.security_checker = SecurityChecker()
        
        # 允许的安全模块
        self.SAFE_MODULES = {
            'math', 'random', 'datetime', 'time', 'json', 'csv', 'base64',
            'hashlib', 'uuid', 'itertools', 'functools', 'collections',
            'operator', 'string', 're', 'copy', 'decimal', 'fractions'
        }
        
        # 允许的数据科学模块（如果安装）
        self.DATA_SCIENCE_MODULES = {
            'numpy', 'pandas', 'matplotlib', 'seaborn', 'plotly', 'scipy',
            'sklearn', 'statsmodels', 'sympy'
        }
        
    def _create_safe_globals(self) -> Dict[str, Any]:
        """创建安全的全局环境"""
        safe_builtins = {
            'abs', 'all', 'any', 'bin', 'bool', 'bytearray', 'bytes',
            'chr', 'complex', 'dict', 'dir', 'divmod', 'enumerate',
            'filter', 'float', 'format', 'frozenset', 'getattr',
            'hasattr', 'hash', 'hex', 'id', 'int', 'isinstance',
            'issubclass', 'iter', 'len', 'list', 'map', 'max', 'min',
            'next', 'oct', 'ord', 'pow', 'print', 'range', 'repr',
            'reversed', 'round', 'set', 'setattr', 'slice', 'sorted',
            'str', 'sum', 'tuple', 'type', 'vars', 'zip'
        }
        
        # 创建受限的builtins
        restricted_builtins = {}
        for name in safe_builtins:
            if hasattr(__builtins__, name):
                restricted_builtins[name] = getattr(__builtins__, name)
        
        # 添加安全的模块
        safe_globals = {
            '__builtins__': restricted_builtins,
            '__name__': '__main__',
            '__doc__': None,
        }
        
        # 动态导入安全模块
        for module_name in self.SAFE_MODULES | self.DATA_SCIENCE_MODULES:
            try:
                module = __import__(module_name)
                safe_globals[module_name] = module
            except ImportError:
                # 模块未安装，跳过
                pass
        
        return safe_globals
    
    async def execute_code(self, code: str, context_vars: Dict[str, Any] = None) -> CodeExecutionResult:
        """执行Python代码"""
        start_time = time.time()
        
        # 安全检查
        if not self.security_checker.check_code(code):
            return CodeExecutionResult(
                success=False,
                output="",
                error=f"Security check failed: {'; '.join(self.security_checker.get_errors())}",
                execution_time=time.time() - start_time
            )
        
        # 准备执行环境
        safe_globals = self._create_safe_globals()
        
        # 添加上下文变量
        if context_vars:
            safe_globals.update(context_vars)
        
        # 捕获输出
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            # 在线程池中执行代码（避免阻塞事件循环）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._execute_in_thread,
                code,
                safe_globals,
                stdout_capture,
                stderr_capture
            )
            
            execution_time = time.time() - start_time
            
            if result['success']:
                return CodeExecutionResult(
                    success=True,
                    output=result['output'],
                    error="",
                    execution_time=execution_time,
                    variables=result['variables']
                )
            else:
                return CodeExecutionResult(
                    success=False,
                    output=result['output'],
                    error=result['error'],
                    execution_time=execution_time
                )
                
        except asyncio.TimeoutError:
            return CodeExecutionResult(
                success=False,
                output="",
                error=f"Execution timeout after {self.timeout} seconds",
                execution_time=self.timeout
            )
        except Exception as e:
            return CodeExecutionResult(
                success=False,
                output="",
                error=f"Execution error: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _execute_in_thread(self, code: str, safe_globals: Dict[str, Any], 
                          stdout_capture: io.StringIO, stderr_capture: io.StringIO) -> Dict[str, Any]:
        """在线程中执行代码"""
        try:
            # 重定向输出
            with contextlib.redirect_stdout(stdout_capture), \
                 contextlib.redirect_stderr(stderr_capture):
                
                # 执行代码
                exec(code, safe_globals, safe_globals)
            
            # 提取用户定义的变量
            user_variables = {}
            for name, value in safe_globals.items():
                if not name.startswith('__') and name not in self.SAFE_MODULES | self.DATA_SCIENCE_MODULES:
                    try:
                        # 尝试序列化变量（排除不可序列化的对象）
                        str(value)
                        user_variables[name] = value
                    except:
                        user_variables[name] = f"<{type(value).__name__} object>"
            
            return {
                'success': True,
                'output': stdout_capture.getvalue(),
                'error': stderr_capture.getvalue(),
                'variables': user_variables
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': stdout_capture.getvalue(),
                'error': str(e),
                'variables': {}
            }

class JupyterStyleExecutor:
    """Jupyter样式的代码执行器（支持魔法命令）"""
    
    def __init__(self):
        self.executor = SecurePythonExecutor()
        self.notebook_globals = {}
        self.cell_counter = 0
        
    async def execute_cell(self, code: str) -> CodeExecutionResult:
        """执行一个代码单元"""
        self.cell_counter += 1
        
        # 处理魔法命令
        processed_code = self._process_magic_commands(code)
        
        # 执行代码，传入之前的全局变量
        result = await self.executor.execute_code(processed_code, self.notebook_globals)
        
        # 更新全局变量
        if result.success and result.variables:
            self.notebook_globals.update(result.variables)
        
        return result
    
    def _process_magic_commands(self, code: str) -> str:
        """处理魔法命令"""
        lines = code.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            
            # 处理 %matplotlib 魔法命令
            if line.startswith('%matplotlib'):
                processed_lines.append("import matplotlib.pyplot as plt")
                processed_lines.append("plt.ion()  # 交互模式")
                continue
            
            # 处理 %time 魔法命令
            if line.startswith('%time '):
                code_to_time = line[6:]
                processed_lines.append(f"import time")
                processed_lines.append(f"_start_time = time.time()")
                processed_lines.append(code_to_time)
                processed_lines.append(f"print(f'执行时间: {{time.time() - _start_time:.4f}} 秒')")
                continue
            
            # 处理 %timeit 魔法命令
            if line.startswith('%timeit '):
                code_to_time = line[8:]
                processed_lines.append(f"import timeit")
                processed_lines.append(f"_result = timeit.timeit(lambda: {code_to_time}, number=1000)")
                processed_lines.append(f"print(f'平均执行时间: {{_result/1000:.6f}} 秒')")
                continue
            
            # 处理 ! shell 命令（安全限制）
            if line.startswith('!'):
                shell_cmd = line[1:].strip()
                if self._is_safe_shell_command(shell_cmd):
                    processed_lines.append(f"import subprocess")
                    processed_lines.append(f"print(subprocess.run(['{shell_cmd}'], capture_output=True, text=True, timeout=10).stdout)")
                else:
                    processed_lines.append(f"print('Shell command not allowed for security reasons')")
                continue
            
            processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _is_safe_shell_command(self, cmd: str) -> bool:
        """检查shell命令是否安全"""
        # 只允许一些安全的命令
        safe_commands = {'ls', 'pwd', 'echo', 'date', 'whoami', 'uname'}
        command_word = cmd.split()[0] if cmd.split() else ""
        return command_word in safe_commands
    
    def reset_environment(self):
        """重置执行环境"""
        self.notebook_globals = {}
        self.cell_counter = 0

class CodeExecutorService:
    """代码执行服务"""
    
    def __init__(self):
        self.simple_executor = SecurePythonExecutor()
        self.jupyter_executor = JupyterStyleExecutor()
        
    async def execute_simple(self, code: str, context: Dict[str, Any] = None) -> CodeExecutionResult:
        """执行简单代码"""
        return await self.simple_executor.execute_code(code, context)
    
    async def execute_notebook_cell(self, code: str) -> CodeExecutionResult:
        """执行笔记本样式的代码单元"""
        return await self.jupyter_executor.execute_cell(code)
    
    def reset_notebook(self):
        """重置笔记本环境"""
        self.jupyter_executor.reset_environment()
    
    async def validate_code(self, code: str) -> Dict[str, Any]:
        """验证代码安全性"""
        checker = SecurityChecker()
        is_safe = checker.check_code(code)
        
        return {
            "is_safe": is_safe,
            "errors": checker.get_errors(),
            "warnings": self._get_code_warnings(code)
        }
    
    def _get_code_warnings(self, code: str) -> List[str]:
        """获取代码警告"""
        warnings = []
        
        # 检查是否有潜在的性能问题
        if 'while True:' in code:
            warnings.append("检测到无限循环，请确保有适当的退出条件")
        
        if re.search(r'for.*in.*range\(\d{4,}\)', code):
            warnings.append("检测到大范围循环，可能影响性能")
        
        if 'sleep(' in code:
            warnings.append("检测到sleep调用，可能导致执行超时")
        
        return warnings
    
    def get_available_modules(self) -> Dict[str, List[str]]:
        """获取可用的模块列表"""
        safe_modules = list(self.simple_executor.SAFE_MODULES)
        data_modules = []
        
        # 检查数据科学模块是否可用
        for module_name in self.simple_executor.DATA_SCIENCE_MODULES:
            try:
                __import__(module_name)
                data_modules.append(module_name)
            except ImportError:
                pass
        
        return {
            "safe_modules": safe_modules,
            "data_science_modules": data_modules,
            "total_available": len(safe_modules) + len(data_modules)
        }

# 全局代码执行服务实例
_code_executor_service = None

def get_code_executor_service() -> CodeExecutorService:
    """获取全局代码执行服务实例"""
    global _code_executor_service
    if _code_executor_service is None:
        _code_executor_service = CodeExecutorService()
    return _code_executor_service

# 工具函数
async def execute_python_code(code: str, context: Dict[str, Any] = None) -> CodeExecutionResult:
    """快速执行Python代码"""
    service = get_code_executor_service()
    return await service.execute_simple(code, context)

def validate_python_code(code: str) -> Dict[str, Any]:
    """快速验证Python代码"""
    service = get_code_executor_service()
    return asyncio.run(service.validate_code(code))
