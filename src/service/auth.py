# -*- coding: utf-8 -*-
"""
AuthService：密码哈希、JWT 颁发/校验、RBAC 角色、安全策略。
增强实现：支持密码强度验证、JWT刷新令牌、多因子认证准备。
"""

from __future__ import annotations

import os
import re
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Literal, Dict, List, Tuple

from jose import jwt, JWTError
from passlib.context import CryptContext

from src.config.logging import get_logger

logger = get_logger("auth")

# 密码上下文配置
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # 增加bcrypt轮数以提高安全性
)

# 密码策略配置
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPER = True
PASSWORD_REQUIRE_LOWER = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = True

# JWT配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me-please")
JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", "dev-refresh-secret-change-me-please")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return pwd_context.verify(password, password_hash)

def validate_password_strength(password: str) -> List[str]:
    """验证密码强度"""
    errors = []

    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f"密码长度至少{PASSWORD_MIN_LENGTH}位")

    if PASSWORD_REQUIRE_UPPER and not re.search(r'[A-Z]', password):
        errors.append("密码必须包含大写字母")

    if PASSWORD_REQUIRE_LOWER and not re.search(r'[a-z]', password):
        errors.append("密码必须包含小写字母")

    if PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', password):
        errors.append("密码必须包含数字")

    if PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("密码必须包含特殊字符")

    # 检查常见弱密码
    weak_passwords = ["password", "123456", "qwerty", "admin", "user"]
    if password.lower() in weak_passwords:
        errors.append("密码过于简单，请选择更复杂的密码")

    return errors

def generate_secure_token(length: int = 32) -> str:
    """生成安全令牌"""
    return secrets.token_urlsafe(length)

def hash_sensitive_data(data: str, salt: str = None) -> str:
    """对敏感数据进行哈希处理"""
    if salt is None:
        salt = secrets.token_hex(16)

    combined = f"{data}{salt}"
    return hashlib.sha256(combined.encode()).hexdigest(), salt

def create_access_token(*, sub: str, role: str, expires_minutes: int = None) -> str:
    """创建访问令牌"""
    if expires_minutes is None:
        expires_minutes = JWT_ACCESS_TOKEN_EXPIRE_MINUTES

    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes)

    payload = {
        "sub": sub,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "type": "access",
        "jti": generate_secure_token(16)  # JWT ID，防止重放攻击
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def create_refresh_token(*, sub: str, role: str) -> str:
    """创建刷新令牌"""
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": sub,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "type": "refresh",
        "jti": generate_secure_token(16)
    }

    return jwt.encode(payload, JWT_REFRESH_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_token(token: str, token_type: str = "access") -> dict:
    """解码令牌"""
    try:
        secret = JWT_SECRET_KEY if token_type == "access" else JWT_REFRESH_SECRET_KEY
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])

        # 验证令牌类型
        if payload.get("type") != token_type:
            raise TokenError("无效的令牌类型")

        # 检查是否过期
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
            raise TokenError("令牌已过期")

        return payload

    except JWTError as e:
        logger.warning(f"JWT解码失败: {str(e)}")
        raise TokenError(str(e))
    except Exception as e:
        logger.error(f"令牌解码异常: {str(e)}")
        raise TokenError("令牌解码失败")

def refresh_access_token(refresh_token: str) -> Tuple[str, str]:
    """使用刷新令牌生成新的访问令牌"""
    try:
        # 验证刷新令牌
        payload = decode_token(refresh_token, "refresh")
        sub = payload.get("sub")
        role = payload.get("role")

        if not sub or not role:
            raise TokenError("无效的刷新令牌")

        # 生成新的令牌对
        new_access_token = create_access_token(sub=sub, role=role)
        new_refresh_token = create_refresh_token(sub=sub, role=role)

        logger.info(f"用户 {sub} 刷新了访问令牌")
        return new_access_token, new_refresh_token

    except TokenError:
        raise
    except Exception as e:
        logger.error(f"令牌刷新异常: {str(e)}")
        raise TokenError("令牌刷新失败")

class TokenError(Exception):
    """令牌错误"""
    pass

def has_role(claims: dict, required: Literal["free", "subscribed", "admin"]) -> bool:
    """检查用户是否有指定角色权限"""
    user_role = claims.get("role", "free")
    role_hierarchy = {
        "free": 0,
        "subscribed": 1,
        "admin": 2
    }

    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required, 0)

    return user_level >= required_level

def get_user_permissions(role: str) -> List[str]:
    """获取用户角色的权限列表"""
    permissions = {
        "free": [
            "read:health",
            "read:documents",
            "create:document_upload",
            "read:search"
        ],
        "subscribed": [
            "read:health",
            "read:documents",
            "create:document_upload",
            "read:search",
            "create:conversation",
            "read:conversation",
            "create:evidence",
            "read:evidence"
        ],
        "admin": [
            "read:health",
            "read:documents",
            "create:document_upload",
            "read:search",
            "create:conversation",
            "read:conversation",
            "create:evidence",
            "read:evidence",
            "admin:users",
            "admin:system",
            "admin:metrics",
            "admin:config"
        ]
    }

    return permissions.get(role, permissions["free"])

def has_permission(user_role: str, required_permission: str) -> bool:
    """检查用户是否有指定权限"""
    user_permissions = get_user_permissions(user_role)
    return required_permission in user_permissions

def log_security_event(event_type: str, user_id: str = None, details: Dict = None):
    """记录安全事件"""
    event_data = {
        "event_type": event_type,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details or {}
    }

    logger.warning("安全事件", extra=event_data)

# 便捷函数
def get_current_user_permissions(request) -> List[str]:
    """获取当前用户的权限列表"""
    user_role = getattr(request.state, 'user_role', 'free')
    return get_user_permissions(user_role)

# FastAPI依赖函数
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    获取当前用户信息的FastAPI依赖函数
    从Authorization header中提取JWT token并验证
    """
    try:
        token = credentials.credentials
        payload = decode_token(token, "access")
        
        user_id = payload.get("sub")
        user_role = payload.get("role", "free")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "id": user_id,
            "role": user_role,
            "permissions": get_user_permissions(user_role)
        }
        
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"获取当前用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """获取当前活跃用户（可以在这里添加额外的检查）"""
    # 这里可以添加用户状态检查，比如是否被禁用等
    return current_user

async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """获取管理员用户"""
    if not has_role(current_user, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

async def get_subscribed_user(current_user: dict = Depends(get_current_user)) -> dict:
    """获取订阅用户"""
    if not has_role(current_user, "subscribed"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要订阅用户权限"
        )
    return current_user


