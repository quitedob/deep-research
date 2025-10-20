# -*- coding: utf-8 -*-
"""
对话搜索API端点
"""

from typing import List, Optional, dict
import logging
import time

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from src.api.deps import require_auth
from src.sqlmodel.models import User
from src.services.session_service import store

logger = logging.getLogger(__name__)

router = APIRouter()

class ConversationSearchRequest(BaseModel):
    """对话搜索请求"""
    query: str
    session_id: Optional[str] = None
    limit: int = Field(20, le=100, description="返回结果数量限制")
    offset: int = Field(0, ge=0, description="偏移量")
    filters: Optional[dict] = Field(default_factory=dict)

class ConversationSearchResponse(BaseModel):
    """对话搜索响应"""
    total: int
    results: List[dict]
    query: str
    suggestions: List[str] = []
    search_time: float

@router.post("/search/conversations", response_model=ConversationSearchResponse)
async def search_conversations(
    request: ConversationSearchRequest,
    current_user: User = Depends(require_auth)
):
    """
    搜索对话历史

    支持全文搜索、过滤和排序
    """
    try:
        start_time = time.time()

        # 获取所有会话
        sessions = await store.list_sessions()
        all_results = []

        # 解析过滤条件
        filters = request.filters or {}
        date_from = filters.get("date_from")
        date_to = filters.get("date_to")
        role = filters.get("role")
        feedback_status = filters.get("feedback_status")

        # 搜索每个会话
        for session_id in sessions:
            # 如果指定了session_id，只搜索该会话
            if request.session_id and session_id != request.session_id:
                continue

            messages = await store.get_messages(session_id)
            session_title = None

            for msg in messages:
                # 获取会话标题（第一条用户消息）
                if not session_title and msg.get("role") == "user":
                    session_title = msg["content"][:50]

                # 角色过滤
                if role and msg.get("role") != role:
                    continue

                # 简单的文本匹配搜索
                content = msg.get("content", "").lower()
                query_lower = request.query.lower()

                if query_lower in content:
                    # 创建搜索结果片段
                    result_msg = msg.copy()
                    result_msg["session_id"] = session_id
                    result_msg["session_title"] = session_title or f"会话 {session_id[:8]}"

                    # 添加高亮信息
                    content_lower = result_msg["content"].lower()
                    query_index = content_lower.find(query_lower)
                    if query_index != -1:
                        start = max(0, query_index - 50)
                        end = min(len(result_msg["content"]), query_index + len(request.query) + 50)
                        highlight = result_msg["content"][start:end]
                        if start > 0:
                            highlight = "..." + highlight
                        if end < len(result_msg["content"]):
                            highlight = highlight + "..."
                        result_msg["highlight"] = highlight

                    # 计算相关性分数（简单的匹配度）
                    score = content.count(query_lower) * len(request.query) / len(content) if content else 0
                    result_msg["relevance_score"] = score

                    all_results.append(result_msg)

        # 排序结果（按相关性分数）
        all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        # 分页
        total = len(all_results)
        paginated_results = all_results[request.offset:request.offset + request.limit]

        # 生成搜索建议（基于常见词）
        suggestions = []
        if total > 0:
            # 简单的建议生成逻辑
            common_words = ["模型", "API", "配置", "错误", "功能", "系统", "数据", "用户"]
            for word in common_words:
                if word not in request.query and word in request.query:
                    suggestions.append(f"{request.query} {word}")
            suggestions = suggestions[:3]

        search_time = time.time() - start_time

        return ConversationSearchResponse(
            total=total,
            results=paginated_results,
            query=request.query,
            suggestions=suggestions,
            search_time=search_time
        )

    except Exception as e:
        logger.error(f"对话搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/suggestions")
async def get_search_suggestions(
    q: str = Query(..., description="搜索查询前缀"),
    current_user: User = Depends(require_auth)
):
    """
    获取搜索建议

    基于历史搜索和常见模式提供建议
    """
    try:
        # 简单的建议逻辑
        suggestions = []

        # 常见搜索前缀
        common_prefixes = [
            "配置", "模型", "API", "错误", "功能", "系统", "数据", "用户",
            "设置", "问题", "解决", "方法", "代码", "示例", "文档"
        ]

        # 基于输入前缀匹配
        for prefix in common_prefixes:
            if prefix.startswith(q) or q in prefix:
                suggestions.append(prefix)

        # 基于可能的完整查询建议
        if len(q) > 2:
            extended_suggestions = [
                f"{q}配置",
                f"{q}设置",
                f"{q}问题",
                f"{q}解决方案",
                f"{q}示例"
            ]
            suggestions.extend(extended_suggestions)

        # 去重并限制数量
        suggestions = list(set(suggestions))[:10]

        return {"suggestions": suggestions}

    except Exception as e:
        logger.error(f"获取搜索建议失败: {e}")
        return {"suggestions": []}

@router.get("/search/recent")
async def get_recent_searches(
    limit: int = Query(5, le=20, description="返回数量限制"),
    current_user: User = Depends(require_auth)
):
    """
    获取最近的搜索历史

    注意：这是一个简化实现，实际应用中可能需要持久化存储
    """
    try:
        # 这里返回一些默认的"最近搜索"
        # 在实际应用中，应该从数据库或缓存中获取真实的搜索历史
        recent_searches = [
            "API配置",
            "模型设置",
            "错误处理",
            "功能介绍",
            "系统使用"
        ]

        return {"recent_searches": recent_searches[:limit]}

    except Exception as e:
        logger.error(f"获取最近搜索失败: {e}")
        return {"recent_searches": []}