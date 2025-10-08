# -*- coding: utf-8 -*-
"""
安全中间件：请求验证、速率限制、权限检查、输入清理
"""

import re
import time
import hashlib
import secrets
from typing import Dict, List, Optional, Set
from collections import defaultdict
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.config.logging import get_logger
from src.service.auth import decode_token, has_role, TokenError

logger = get_logger("security")

class SecurityMiddleware:
    """安全中间件"""

    def __init__(self):
        # 速率限制存储
        self.rate_limits: Dict[str, List[float]] = defaultdict(list)
        self.blocked_ips: Set[str] = set()
        # CSRF Token存储
        self.csrf_tokens: Dict[str, float] = {}

        # 安全配置
        self.max_requests_per_minute = 60  # 每分钟最大请求数
        self.block_duration = 300  # 封禁持续时间（秒）
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS脚本标签
            r'javascript:',  # JavaScript URL
            r'on\w+\s*=',  # 事件处理器
            r'union\s+select',  # SQL注入
            r';\s*drop\s+table',  # SQL注入
            r'--',  # SQL注释
            r'/\*\*/',  # SQL注释
        ]

    async def validate_request(self, request: Request) -> Optional[Dict]:
        """
        验证请求的安全性

        返回用户claims或None（如果不需要认证）
        """
        # 检查IP是否被封禁
        client_ip = self._get_client_ip(request)
        if client_ip in self.blocked_ips:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="IP地址已被临时封禁"
            )

        # 速率限制检查
        if not self._check_rate_limit(client_ip):
            self.blocked_ips.add(client_ip)
            logger.warning(f"IP {client_ip} 因速率限制被封禁")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后再试"
            )

        # 输入清理和验证
        await self._sanitize_input(request)

        # 认证检查（某些路径不需要认证）
        public_paths = {
            '/api/health',
            '/api/health/',
            '/docs',
            '/redoc',
            '/openapi.json'
        }

        if not any(request.url.path.startswith(path) for path in public_paths):
            return await self._authenticate_request(request)

        return None

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP"""
        # 优先使用X-Forwarded-For头
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            # X-Forwarded-For可能包含多个IP，取第一个
            return x_forwarded_for.split(',')[0].strip()

        # 回退到X-Real-IP
        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip

        # 最后回退到FastAPI的client
        return request.client.host if request.client else "unknown"

    def _check_rate_limit(self, client_ip: str) -> bool:
        """检查速率限制"""
        current_time = time.time()
        window_start = current_time - 60  # 1分钟窗口

        # 清理过期的请求记录
        self.rate_limits[client_ip] = [
            timestamp for timestamp in self.rate_limits[client_ip]
            if timestamp > window_start
        ]

        # 检查请求数量
        if len(self.rate_limits[client_ip]) >= self.max_requests_per_minute:
            return False

        # 记录新请求
        self.rate_limits[client_ip].append(current_time)
        return True

    async def _sanitize_input(self, request: Request):
        """清理和验证输入"""
        # 获取请求体（对于某些请求类型）
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()

                # CSRF保护（对API请求）
                if request.url.path.startswith("/api/"):
                    csrf_token = request.headers.get("X-CSRF-Token")
                    if not csrf_token or csrf_token not in self.csrf_tokens:
                        logger.warning(f"CSRF token验证失败: {request.url.path}")
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="CSRF token验证失败"
                        )

                    # 检查token是否过期（1小时）
                    if time.time() - self.csrf_tokens[csrf_token] > 3600:
                        del self.csrf_tokens[csrf_token]
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="CSRF token已过期"
                        )

                # 检查可疑模式
                body_str = body.decode('utf-8', errors='ignore')
                for pattern in self.suspicious_patterns:
                    if re.search(pattern, body_str, re.IGNORECASE):
                        logger.warning(f"检测到可疑输入模式: {pattern}")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="输入包含无效内容"
                        )

                # 检查文件上传大小（已在其他地方处理，这里是额外验证）
                content_length = len(body)
                if content_length > 100 * 1024 * 1024:  # 100MB
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="请求体过大"
                    )

            except UnicodeDecodeError:
                # 二进制数据，跳过文本检查
                pass

    async def _authenticate_request(self, request: Request) -> Dict:
        """认证请求"""
        # 获取Authorization头
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少认证信息"
            )

        # 检查Bearer token格式
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证格式"
            )

        token = auth_header[7:]  # 移除"Bearer "前缀

        try:
            # 解码token
            claims = decode_token(token)

            # 设置用户上下文
            if "sub" in claims:
                request.state.user_id = claims["sub"]
                request.state.user_role = claims.get("role", "free")

            return claims

        except TokenError as e:
            logger.warning(f"Token验证失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌"
            )

def require_role(required_role: str):
    """角色权限装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取request对象
            request = None
            for arg in args:
                if hasattr(arg, 'state') and hasattr(arg.state, 'user_role'):
                    request = arg
                    break

            if not request:
                # 尝试从kwargs获取
                request = kwargs.get('request')

            if not request or not hasattr(request.state, 'user_role'):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要认证"
                )

            user_role = getattr(request.state, 'user_role', 'free')
            if not has_role({"role": user_role}, required_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要 {required_role} 权限"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

def hash_string(content: str, salt: str = "") -> str:
    """生成内容哈希（用于敏感信息存储）"""
    combined = f"{content}{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()

def validate_password_strength(password: str) -> List[str]:
    """验证密码强度"""
    errors = []

    if len(password) < 8:
        errors.append("密码长度至少8位")

    if not re.search(r'[A-Z]', password):
        errors.append("密码必须包含大写字母")

    if not re.search(r'[a-z]', password):
        errors.append("密码必须包含小写字母")

    if not re.search(r'\d', password):
        errors.append("密码必须包含数字")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("密码必须包含特殊字符")

    return errors

# 全局安全中间件实例
security_middleware = SecurityMiddleware()

async def security_middleware_func(request: Request, call_next):
    """FastAPI安全中间件函数"""
    try:
        # 验证请求
        claims = await security_middleware.validate_request(request)

        # 将用户信息存储在请求状态中
        if claims:
            request.state.user_id = claims.get("sub")
            request.state.user_role = claims.get("role", "free")

        # 处理请求
        response = await call_next(request)

        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # 为GET请求生成CSRF token
        if request.method == "GET" and request.url.path.startswith("/api/"):
            csrf_token = secrets.token_urlsafe(32)
            self.csrf_tokens[csrf_token] = time.time()
            response.headers["X-CSRF-Token"] = csrf_token

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"安全中间件异常: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "内部服务器错误"}
        )

