# -*- coding: utf-8 -*-
"""
Services Layer: 业务逻辑层
提供高级业务操作，封装复杂的业务逻辑
统一的服务架构，所有服务继承BaseService
"""

from .base_service import BaseService
from .auth_service import AuthService, TokenError
from .user_service import UserService
from .admin_service import AdminService
from .quota_service import QuotaService
from .audit_service import AuditService
from .billing_service import BillingService
from .document_service import DocumentService
from .conversation_service import ConversationService
from .research_service import ResearchService
from .session_service import SessionService, session_service, store
from .agent_manager_service import AgentManagerV2

# 便捷函数导出（保持向后兼容）
from .auth_service import (
    get_current_user,
    get_current_active_user,
    get_admin_user,
    get_subscribed_user,
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    has_role,
    log_admin_action,
    log_admin_action_dependency,
    audit_admin_action
)

# Note: audit_service functions moved to auth_service for backward compatibility

__all__ = [
    # 基础服务类
    "BaseService",

    # 业务服务类
    "AuthService",
    "UserService",
    "AdminService",
    "QuotaService",
    "AuditService",
    "BillingService",
    "DocumentService",
    "ConversationService",
    "ResearchService",
    "SessionService",
    "AgentManagerV2",

    # 会话服务实例（向后兼容）
    "session_service",
    "store",

    # 便捷函数（向后兼容）
    "get_current_user",
    "get_current_active_user",
    "get_admin_user",
    "get_subscribed_user",
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_token",
    "has_role",
    "log_admin_action",
    "log_admin_action_dependency",
    "audit_admin_action",

    # 异常类
    "TokenError"
]