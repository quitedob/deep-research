# -*- coding: utf-8 -*-
"""
数据模型和验证模式（Schema/DTO层）
统一的请求/响应数据模型定义，用于API数据验证和序列化
"""

from .base import (
    # 基础响应模型
    BaseResponse,
    SuccessResponse,
    ErrorResponse,
    PaginatedResponse,
)

from .chat import (
    # 聊天相关模型
    ChatItem,
    ChatReq,
    ChatResp,
)

from .research import (
    # 研究相关模型
    ResearchReq,
    ResearchResponse,
    ResearchStreamResponse,
)

from .conversation import (
    # 对话相关模型
    ConversationCreateRequest,
    ConversationSessionResponse,
    ConversationMessageResponse,
)

from .common import (
    # 通用模型
    PaginationParams,
    ListResponse,
)

__all__ = [
    # 基础
    "BaseResponse",
    "SuccessResponse",
    "ErrorResponse",
    "PaginatedResponse",
    # 聊天
    "ChatItem",
    "ChatReq",
    "ChatResp",
    # 研究
    "ResearchReq",
    "ResearchResponse",
    "ResearchStreamResponse",
    # 对话
    "ConversationCreateRequest",
    "ConversationSessionResponse",
    "ConversationMessageResponse",
    # 通用
    "PaginationParams",
    "ListResponse",
]
