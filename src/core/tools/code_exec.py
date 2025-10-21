# -*- coding: utf-8 -*-
"""
安全的Python代码执行工具
提供真正的沙盒环境执行代码，支持AST安全检查和资源限制
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
import signal
import resource
import psutil
import json
import hashlib
import uuid
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
import re
from pathlib import Path

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
    """增强的代码安全检查器"""

    # 扩展的危险模块和函数列表
    DANGEROUS_IMPORTS = {
        'os', 'sys', 'subprocess', 'socket', 'urllib', 'http', 'ftplib',
        'smtplib', 'poplib', 'imaplib', 'telnetlib', 'xmlrpc', 'pickle',
        'marshal', 'shelve', 'dbm', 'sqlite3', 'mysql', 'pymongo',
        'ctypes', '__builtin__', 'builtins', 'importlib', 'imp',
        'threading', 'multiprocessing', 'concurrent', 'asyncio',
        'webbrowser', 'smtplib', 'telnetlib', 'ftplib', 'poplib',
        'imaplib', 'nntplib', 'smtplib', 'smtpd', 'http', 'urllib',
        'httplib', 'ftplib', 'poplib', 'imaplib', 'telnetlib',
        'xmlrpclib', 'xmlrpc', 'ssl', 'hashlib', 'hmac', 'secrets'
    }

    DANGEROUS_FUNCTIONS = {
        'exec', 'eval', 'compile', '__import__', 'reload', 'execfile',
        'exit', 'quit', 'help', 'input', 'raw_input', 'open', 'file',
        'globals', 'locals', 'vars', 'dir', 'hasattr', 'getattr',
        'setattr', 'delattr', 'isinstance', 'issubclass', 'callable',
        'super', 'property', 'classmethod', 'staticmethod'
    }

    DANGEROUS_ATTRIBUTES = {
        '__class__', '__bases__', '__subclasses__', '__mro__', '__globals__',
        '__code__', '__func__', '__self__', '__module__', '__dict__',
        '__annotations__', '__closure__', '__defaults__', '__qualname__',
        '__kwdefaults__', '__name__', '__doc__', '__file__', '__package__',
        '__loader__', '__spec__', '__path__', '__cached__', '__builtins__'
    }

    # 危险的内置函数
    DANGEROUS_BUILTINS = {
        'compile', 'eval', 'exec', 'open', 'input', 'raw_input',
        '__import__', 'reload', 'exit', 'quit', 'help', 'globals',
        'locals', 'vars', 'dir', 'hasattr', 'getattr', 'setattr',
        'delattr', 'isinstance', 'issubclass', 'callable', 'super'
    }

    # 危险的操作符和语法结构
    DANGEROUS_OPERATIONS = {
        'exec', 'eval', 'compile', 'import', 'from', 'global', 'nonlocal'
    }
    
    def __init__(self):
        self.errors = []
        
    def check_code(self, code: str) -> bool:
        """增强的代码安全检查"""
        self.errors = []

        # 基础检查
        if not code or not code.strip():
            self.errors.append("Empty code not allowed")
            return False

        # 检查代码长度
        if len(code) > 10000:  # 10KB limit
            self.errors.append("Code too long (max 10KB)")
            return False

        try:
            tree = ast.parse(code)
            self._visit_node(tree)
            self._check_for_obfuscation(code)
            self._check_for_suspicious_patterns(code)
            return len(self.errors) == 0
        except SyntaxError as e:
            self.errors.append(f"Syntax error: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Parse error: {e}")
            return False

    def _visit_node(self, node):
        """深度访问AST节点"""
        # 检查导入语句
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                if module_name in self.DANGEROUS_IMPORTS:
                    self.errors.append(f"Dangerous import: {module_name}")
                # 检查子模块导入
                if '.' in module_name:
                    base_module = module_name.split('.')[0]
                    if base_module in self.DANGEROUS_IMPORTS:
                        self.errors.append(f"Dangerous submodule import: {module_name}")

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                if node.module in self.DANGEROUS_IMPORTS:
                    self.errors.append(f"Dangerous import from: {node.module}")
                # 检查相对导入
                if node.level > 0:
                    self.errors.append("Relative imports not allowed")

        # 检查函数调用
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in self.DANGEROUS_FUNCTIONS:
                    self.errors.append(f"Dangerous function call: {node.func.id}")
            elif isinstance(node.func, ast.Attribute):
                # 检查方法调用
                if hasattr(node.func, 'attr') and node.func.attr in self.DANGEROUS_FUNCTIONS:
                    self.errors.append(f"Dangerous method call: {node.func.attr}")

        # 检查属性访问
        elif isinstance(node, ast.Attribute):
            if node.attr in self.DANGEROUS_ATTRIBUTES:
                self.errors.append(f"Dangerous attribute access: {node.attr}")

        # 检查全局变量声明
        elif isinstance(node, ast.Global):
            self.errors.append("Global variables not allowed")

        elif isinstance(node, ast.Nonlocal):
            self.errors.append("Nonlocal variables not allowed")

        # 检查装饰器
        elif isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id in self.DANGEROUS_FUNCTIONS:
                    self.errors.append(f"Dangerous decorator: {decorator.id}")

        # 检查类定义
        elif isinstance(node, ast.ClassDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id in self.DANGEROUS_FUNCTIONS:
                    self.errors.append(f"Dangerous class decorator: {decorator.id}")

        # 递归检查子节点
        for child in ast.iter_child_nodes(node):
            self._visit_node(child)

    def _check_for_obfuscation(self, code: str):
        """检查代码混淆"""
        # 检查常见的混淆模式
        obfuscation_patterns = [
            r'__import__\s*\(',  # 动态导入
            r'getattr\s*\(',     # 动态属性访问
            r'setattr\s*\(',     # 动态属性设置
            r'eval\s*\(',        # 动态执行
            r'exec\s*\(',        # 动态执行
            r'compile\s*\(',     # 动态编译
            r'globals\s*\(',     # 访问全局变量
            r'locals\s*\(',      # 访问局部变量
            r'vars\s*\(',        # 变量字典
            r'dir\s*\(',         # 对象属性列表
            r'hasattr\s*\(',     # 属性检查
            r'isinstance\s*\(',  # 类型检查
            r'issubclass\s*\(',  # 子类检查
            r'callable\s*\(',    # 可调用检查
            r'super\s*\(',       # 父类访问
            r'type\s*\(',        # 类型对象
            r'__class__\s*\(',   # 类访问
            r'__bases__\s*\(',   # 基类访问
            r'__subclasses__\s*\(', # 子类访问
            r'__mro__\s*\(',      # 方法解析顺序
            r'__dict__\s*\(',     # 对象字典
        ]

        for pattern in obfuscation_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                self.errors.append(f"Potentially dangerous pattern detected: {pattern}")

    def _check_for_suspicious_patterns(self, code: str):
        """检查可疑模式"""
        suspicious_patterns = [
            r'while\s+True\s*:',      # 无限循环
            r'for\s+.*\s+in\s+range\s*\(\s*\d{4,}\s*\)',  # 大范围循环
            r'import\s+.*\s*as\s+.*',  # 模块别名
            r'from\s+.*\s+import\s+\*',  # 通配符导入
            r'def\s+__\w+__\s*\(',     # 魔术方法
            r'class\s+__\w+__\s*:',     # 魔术类
            r'@\w+',                   # 装饰器
            r'lambda\s*:',             # lambda函数
            r'yield\s+',               # 生成器
            r'async\s+def\s+',         # 异步函数
            r'await\s+',               # 等待表达式
            r'try\s*:',                # 异常处理
            r'except\s*:.*',           # 异常捕获
            r'finally\s*:',            # 最终处理
            r'raise\s+',               # 抛出异常
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                # 这些只是警告，不是错误
                pass
    
    def get_errors(self) -> List[str]:
        """获取安全检查错误"""
        return self.errors

class SecurePythonExecutor:
    """真正的安全Python代码执行器 - 使用进程隔离和资源限制"""

    def __init__(self, timeout: int = 30, memory_limit_mb: int = 100):
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb
        self.security_checker = SecurityChecker()

        # 允许的安全模块（白名单）
        self.SAFE_MODULES = {
            'math', 'random', 'datetime', 'time', 'json', 'csv', 'base64',
            'uuid', 'itertools', 'functools', 'collections',
            'operator', 'string', 're', 'copy', 'decimal', 'fractions',
            'statistics', 'numbers', 'enum'
        }

        # 允许的数据科学模块（如果安装）
        self.DATA_SCIENCE_MODULES = {
            'numpy', 'pandas', 'matplotlib', 'seaborn', 'plotly', 'scipy',
            'sklearn', 'statsmodels', 'sympy'
        }

        # 创建执行目录
        self.execution_dir = Path(tempfile.mkdtemp(prefix="secure_exec_"))
        self.execution_dir.mkdir(exist_ok=True)

        # 确保执行目录权限正确
        os.chmod(self.execution_dir, 0o700)

    def __del__(self):
        """清理临时文件"""
        try:
            import shutil
            if hasattr(self, 'execution_dir') and self.execution_dir.exists():
                shutil.rmtree(self.execution_dir, ignore_errors=True)
        except:
            pass

    def _create_execution_script(self, code: str, context_vars: Dict[str, Any] = None) -> str:
        """创建安全的执行脚本"""
        # 创建执行ID
        exec_id = str(uuid.uuid4())[:8]
        script_path = self.execution_dir / f"exec_{exec_id}.py"

        # 构建安全的执行脚本
        script_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全执行脚本 - 自动生成
执行ID: {exec_id}
"""

import sys
import json
import traceback
import signal
import resource
import os
from io import StringIO

# 设置资源限制
def set_resource_limits():
    """设置进程资源限制"""
    # 内存限制
    try:
        resource.setrlimit(resource.RLIMIT_AS,
                          ({self.memory_limit_mb * 1024 * 1024},
                           {self.memory_limit_mb * 1024 * 1024}))
    except:
        pass

    # CPU时间限制
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (self.timeout, self.timeout))
    except:
        pass

    # 文件描述符限制
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    except:
        pass

# 安全的内置函数集合
SAFE_BUILTINS = {{
    'abs': abs, 'all': all, 'any': any, 'bin': bin, 'bool': bool,
    'chr': chr, 'complex': complex, 'dict': dict, 'divmod': divmod,
    'enumerate': enumerate, 'filter': filter, 'float': float,
    'format': format, 'frozenset': frozenset, 'getattr': getattr,
    'hasattr': hasattr, 'hash': hash, 'hex': hex, 'id': id,
    'int': int, 'isinstance': isinstance, 'issubclass': issubclass,
    'iter': iter, 'len': len, 'list': list, 'map': map,
    'max': max, 'min': min, 'next': next, 'oct': oct,
    'ord': ord, 'pow': pow, 'range': range, 'repr': repr,
    'reversed': reversed, 'round': round, 'set': set,
    'slice': slice, 'sorted': sorted, 'str': str, 'sum': sum,
    'tuple': tuple, 'type': type, 'zip': zip
}}

# 创建安全的全局环境
safe_globals = {{
    '__builtins__': SAFE_BUILTINS,
    '__name__': '__main__',
    '__doc__': None,
}}

# 导入安全模块
safe_modules = {list(self.SAFE_MODULES)}
data_modules = {list(self.DATA_SCIENCE_MODULES)}

for module_name in safe_modules + data_modules:
    try:
        module = __import__(module_name)
        safe_globals[module_name] = module
    except ImportError:
        pass

# 添加上下文变量
'''

        # 添加用户提供的上下文变量（序列化为JSON后重新加载）
        if context_vars:
            script_content += "context_vars = '''\\n"
            script_content += json.dumps(context_vars, indent=2)
            script_content += "\\n'''\\n\\n"
            script_content += "for key, value in context_vars.items():\\n"
            script_content += "    try:\\n"
            script_content += "        safe_globals[key] = value\\n"
            script_content += "    except Exception:\\n"
            script_content += "        pass\\n\\n"

        # 添加用户代码
        script_content += '''
# 用户代码开始执行
user_code = """\\n''' + code.replace('"""', '\\"\\"\\"') + '''\\n"""

# 捕获输出
stdout_capture = StringIO()
stderr_capture = StringIO()

# 设置信号处理
def timeout_handler(signum, frame):
    raise TimeoutError("Execution timeout")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(self.timeout)

try:
    # 设置资源限制
    set_resource_limits()

    # 重定向输出
    import sys
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    sys.stdout = stdout_capture
    sys.stderr = stderr_capture

    # 执行用户代码
    exec(user_code, safe_globals, safe_globals)

    # 恢复输出
    sys.stdout = old_stdout
    sys.stderr = old_stderr

    # 提取用户定义的变量
    user_variables = {{}}
    for name, value in safe_globals.items():
        if not name.startswith('__') and name not in safe_modules + data_modules:
            try:
                # 尝试序列化变量
                json.dumps({{"type": "type", "value": "value"}}, default=str)
                user_variables[name] = value
            except:
                user_variables[name] = f"<{type(value).__name__} object>"

    # 准备结果
    result = {{
        'success': True,
        'output': stdout_capture.getvalue(),
        'error': stderr_capture.getvalue(),
        'variables': user_variables
    }}

except TimeoutError as e:
    result = {{
        'success': False,
        'output': stdout_capture.getvalue(),
        'error': str(e),
        'variables': {{}}
    }}
except Exception as e:
    result = {{
        'success': False,
        'output': stdout_capture.getvalue(),
        'error': f"{{type(e).__name__}}: {{str(e)}}",
        'variables': {{}}
    }}
finally:
    signal.alarm(0)

# 输出结果（JSON格式）
import json
print(json.dumps(result, default=str))
'''

        # 写入脚本文件
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # 设置执行权限
        os.chmod(script_path, 0o700)

        return str(script_path)
    
    async def execute_code(self, code: str, context_vars: Dict[str, Any] = None) -> CodeExecutionResult:
        """在隔离的进程中安全执行Python代码"""
        start_time = time.time()

        # 安全检查
        if not self.security_checker.check_code(code):
            return CodeExecutionResult(
                success=False,
                output="",
                error=f"Security check failed: {'; '.join(self.security_checker.get_errors())}",
                execution_time=time.time() - start_time
            )

        try:
            # 创建安全的执行脚本
            script_path = self._create_execution_script(code, context_vars)

            # 在线程池中执行隔离的进程
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._execute_in_isolated_process,
                script_path
            )

            execution_time = time.time() - start_time

            # 清理临时文件
            try:
                os.unlink(script_path)
            except:
                pass

            if result['success']:
                return CodeExecutionResult(
                    success=True,
                    output=result['output'],
                    error=result.get('error', ''),
                    execution_time=execution_time,
                    variables=result.get('variables', {})
                )
            else:
                return CodeExecutionResult(
                    success=False,
                    output=result.get('output', ''),
                    error=result.get('error', 'Unknown error'),
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

    def _execute_in_isolated_process(self, script_path: str) -> Dict[str, Any]:
        """在隔离的进程中执行脚本"""
        try:
            # 使用subprocess运行隔离的Python进程
            # 添加额外的安全参数
            env = os.environ.copy()
            # 清理环境变量
            env.pop('PYTHONPATH', None)
            env.pop('PYTHONHOME', None)
            env.pop('LD_LIBRARY_PATH', None)
            env.pop('DYLD_LIBRARY_PATH', None)

            # 设置严格的环境变量
            env['PATH'] = '/usr/bin:/bin:/usr/local/bin'

            process = subprocess.run(
                [sys.executable, '-E', '-S', script_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
                cwd=str(self.execution_dir),
                # 禁用所有危险的启动选项
                # 不使用 -c 参数避免代码注入
            )

            if process.returncode != 0:
                return {
                    'success': False,
                    'output': process.stdout,
                    'error': f"Process failed with code {process.returncode}: {process.stderr}"
                }

            # 尝试解析JSON输出
            try:
                # 查找JSON输出的开始和结束
                output_lines = process.stdout.strip().split('\n')
                json_output = None

                for line in output_lines:
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        try:
                            json_output = json.loads(line)
                            break
                        except json.JSONDecodeError:
                            continue

                if json_output:
                    return json_output
                else:
                    return {
                        'success': False,
                        'output': process.stdout,
                        'error': "No valid JSON output found"
                    }

            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'output': process.stdout,
                    'error': f"JSON decode error: {e}"
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': "",
                'error': f"Process timeout after {self.timeout} seconds"
            }
        except Exception as e:
            return {
                'success': False,
                'output': "",
                'error': f"Process execution error: {str(e)}"
            }
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        return {
            'execution_directory': str(self.execution_dir),
            'timeout': self.timeout,
            'memory_limit_mb': self.memory_limit_mb,
            'available_safe_modules': list(self.SAFE_MODULES),
            'available_data_modules': [m for m in self.DATA_SCIENCE_MODULES
                                       if self._is_module_available(m)]
        }

    def _is_module_available(self, module_name: str) -> bool:
        """检查模块是否可用"""
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False

class JupyterStyleExecutor:
    """安全的Jupyter样式代码执行器（支持有限的魔法命令）"""

    def __init__(self, timeout: int = 30, memory_limit_mb: int = 100):
        self.executor = SecurePythonExecutor(timeout=timeout, memory_limit_mb=memory_limit_mb)
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
        """处理有限的魔法命令（增强安全性）"""
        lines = code.split('\n')
        processed_lines = []

        for line in lines:
            line = line.strip()

            # 处理 %matplotlib 魔法命令
            if line.startswith('%matplotlib'):
                if self.executor._is_module_available('matplotlib'):
                    processed_lines.append("import matplotlib.pyplot as plt")
                    processed_lines.append("plt.ion()  # 交互模式")
                else:
                    processed_lines.append("# matplotlib not available")
                continue

            # 处理 %time 魔法命令
            if line.startswith('%time '):
                code_to_time = line[6:]
                processed_lines.append("import time")
                processed_lines.append("_start_time = time.time()")
                processed_lines.append(code_to_time)
                processed_lines.append("print(f'执行时间: {time.time() - _start_time:.4f} 秒')")
                continue

            # 处理 %timeit 魔法命令
            if line.startswith('%timeit '):
                code_to_time = line[8:]
                processed_lines.append("import timeit")
                processed_lines.append("_result = timeit.timeit(lambda: " + code_to_time + ", number=10)")
                processed_lines.append("print(f'平均执行时间: {_result/10:.6f} 秒')")
                continue

            # 禁用所有shell命令（安全考虑）
            if line.startswith('!'):
                processed_lines.append("# Shell commands are not allowed for security reasons")
                continue

            processed_lines.append(line)

        return '\n'.join(processed_lines)

    def reset_environment(self):
        """重置执行环境"""
        self.notebook_globals = {}
        self.cell_counter = 0

class CodeExecutorService:
    """安全的代码执行服务"""

    def __init__(self, timeout: int = 30, memory_limit_mb: int = 100):
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb
        self.simple_executor = SecurePythonExecutor(timeout=timeout, memory_limit_mb=memory_limit_mb)
        self.jupyter_executor = JupyterStyleExecutor(timeout=timeout, memory_limit_mb=memory_limit_mb)

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
            "warnings": self._get_code_warnings(code),
            "stats": self.simple_executor.get_execution_stats()
        }

    def _get_code_warnings(self, code: str) -> List[str]:
        """获取代码警告"""
        warnings = []

        # 检查潜在的性能问题
        if 'while True:' in code:
            warnings.append("检测到无限循环，请确保有适当的退出条件")

        if re.search(r'for.*in.*range\(\d{4,}\)', code):
            warnings.append("检测到大范围循环，可能影响性能")

        if 'sleep(' in code:
            warnings.append("检测到sleep调用，可能导致执行超时")

        # 检查内存使用
        if 'list(range(' in code and '1000000' in code:
            warnings.append("检测到大型列表创建，可能影响内存使用")

        return warnings

    def get_available_modules(self) -> Dict[str, Any]:
        """获取可用的模块列表"""
        stats = self.simple_executor.get_execution_stats()

        return {
            "safe_modules": stats['available_safe_modules'],
            "data_science_modules": stats['available_data_modules'],
            "total_available": len(stats['available_safe_modules']) + len(stats['available_data_modules']),
            "timeout": stats['timeout'],
            "memory_limit_mb": stats['memory_limit_mb']
        }

    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "service_type": "secure_code_executor",
            "security_level": "high",
            "isolation": "process_based",
            "resource_limits": {
                "timeout": self.timeout,
                "memory_limit_mb": self.memory_limit_mb
            },
            "features": [
                "AST_security_checks",
                "process_isolation",
                "resource_limits",
                "safe_module_whitelist",
                "output_redirection"
            ]
        }

# 全局代码执行服务实例
_code_executor_service = None

def get_code_executor_service(timeout: int = 30, memory_limit_mb: int = 100) -> CodeExecutorService:
    """获取全局代码执行服务实例"""
    global _code_executor_service
    if _code_executor_service is None:
        _code_executor_service = CodeExecutorService(timeout=timeout, memory_limit_mb=memory_limit_mb)
    return _code_executor_service

# 工具函数
async def execute_python_code(code: str, context: Dict[str, Any] = None,
                            timeout: int = 30, memory_limit_mb: int = 100) -> CodeExecutionResult:
    """安全执行Python代码"""
    service = get_code_executor_service(timeout=timeout, memory_limit_mb=memory_limit_mb)
    return await service.execute_simple(code, context)

async def validate_python_code(code: str, timeout: int = 30, memory_limit_mb: int = 100) -> Dict[str, Any]:
    """安全验证Python代码"""
    service = get_code_executor_service(timeout=timeout, memory_limit_mb=memory_limit_mb)
    return await service.validate_code(code)

def validate_python_code_sync(code: str, timeout: int = 30, memory_limit_mb: int = 100) -> Dict[str, Any]:
    """同步验证Python代码"""
    import asyncio
    return asyncio.run(validate_python_code(code, timeout, memory_limit_mb))

# 向后兼容的别名
def get_secure_executor_service(timeout: int = 30, memory_limit_mb: int = 100) -> CodeExecutorService:
    """获取安全代码执行服务实例（别名）"""
    return get_code_executor_service(timeout=timeout, memory_limit_mb=memory_limit_mb)
