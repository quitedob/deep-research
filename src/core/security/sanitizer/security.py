# -*- coding: utf-8 -*-
"""
核心安全处理模块
提供输出安全处理、输入验证等安全相关功能
"""

import re
import html
from typing import Any

def sanitize_model_output(content: str) -> str:
    """
    清理模型输出，移除潜在的安全风险

    Args:
        content: 模型输出的原始内容

    Returns:
        清理后的安全内容
    """
    if not isinstance(content, str):
        content = str(content)

    # HTML转义防止XSS攻击
    content = html.escape(content)

    # 移除潜在的危险代码模式
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',  # script标签
        r'javascript:',                # javascript协议
        r'on\w+\s*=',                 # 事件处理器
        r'<iframe[^>]*>',             # iframe标签
        r'<object[^>]*>',             # object标签
        r'<embed[^>]*>',              # embed标签
    ]

    for pattern in dangerous_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)

    # 限制长度防止过长输出
    max_length = 50000
    if len(content) > max_length:
        content = content[:max_length] + "... [内容过长已截断]"

    return content

def sanitize_user_input(input_text: str) -> str:
    """
    清理用户输入，防止注入攻击

    Args:
        input_text: 用户输入的原始内容

    Returns:
        清理后的安全输入
    """
    if not isinstance(input_text, str):
        input_text = str(input_text)

    # 移除潜在的危险字符
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\n', '\r', '\t']
    for char in dangerous_chars:
        input_text = input_text.replace(char, '')

    # 限制输入长度
    max_length = 10000
    if len(input_text) > max_length:
        input_text = input_text[:max_length]

    return input_text.strip()

def validate_file_content(content: bytes, max_size: int = 50 * 1024 * 1024) -> bool:
    """
    验证文件内容安全性

    Args:
        content: 文件内容
        max_size: 最大文件大小（默认50MB）

    Returns:
        是否安全
    """
    # 检查文件大小
    if len(content) > max_size:
        return False

    # 检查文件头，防止可执行文件
    dangerous_signatures = [
        b'MZ',                    # Windows PE
        b'\x7fELF',              # Linux ELF
        b'\xca\xfe\xba\xbe',     # Java class
        b'\xfe\xed\xfa',         # Mach-O binary
    ]

    for signature in dangerous_signatures:
        if content.startswith(signature):
            return False

    return True

def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除危险字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的安全文件名
    """
    if not isinstance(filename, str):
        filename = str(filename)

    # 移除路径遍历字符
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')

    # 移除危险字符
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        filename = filename.replace(char, '')

    # 限制长度
    max_length = 255
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:max_length-len(ext)-1] + '.' + ext if ext else name[:max_length]

    return filename.strip() or 'untitled'

__all__ = [
    'sanitize_model_output',
    'sanitize_user_input',
    'validate_file_content',
    'sanitize_filename'
]