# -*- coding: utf-8 -*-
"""
Pydantic Schema Models
用于API请求和响应的数据验证
"""

# 导入所有schema模型
from .base_schema import BaseResponse, BaseRequest
from .chat import ChatItem, ChatReq, ChatResp
from .export import MDExportReq, PPTExportReq, TTSExportReq
from .research import ResearchReq
from .search import ConversationSearchRequest, ConversationSearchResponse
from .share import ShareConversationRequest, ShareConversationResponse, PublicConversationResponse
from .user import UserOnboardingRequest, UserOnboardingResponse, UserPreferencesRequest

__all__ = [
    # 基础schema
    "BaseResponse",
    "BaseRequest",

    # 聊天相关
    "ChatItem",
    "ChatReq",
    "ChatResp",

    # 导出相关
    "MDExportReq",
    "PPTExportReq",
    "TTSExportReq",

    # 研究相关
    "ResearchReq",

    # 搜索相关
    "ConversationSearchRequest",
    "ConversationSearchResponse",

    # 分享相关
    "ShareConversationRequest",
    "ShareConversationResponse",
    "PublicConversationResponse",

    # 用户相关
    "UserOnboardingRequest",
    "UserOnboardingResponse",
    "UserPreferencesRequest",
]