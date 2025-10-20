# -*- coding: utf-8 -*-
"""
对话分享API端点
"""

from typing import List, Optional
import logging
import secrets
import hashlib
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.api.deps import require_auth
from src.sqlmodel.models import User
from src.services.session_service import store

logger = logging.getLogger(__name__)

router = APIRouter()

class ShareConversationRequest(BaseModel):
    """对话分享请求"""
    session_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    expire_days: int = Field(30, ge=1, le=365, description="分享链接有效期（天）")

class ShareConversationResponse(BaseModel):
    """对话分享响应"""
    share_id: str
    public_url: str
    title: str
    expires_at: str
    created_at: str

class PublicConversationResponse(BaseModel):
    """公开对话响应"""
    share_id: str
    title: str
    description: Optional[str]
    messages: List[dict]
    created_at: str
    expires_at: str
    view_count: int

# 简单的内存存储（实际应用中应使用数据库）
_conversation_shares = {}

@router.post("/share/conversation", response_model=ShareConversationResponse)
async def share_conversation(
    request: ShareConversationRequest,
    current_user: User = Depends(require_auth)
):
    """
    创建对话分享链接

    生成公开链接，允许他人查看对话内容
    """
    try:
        # 验证会话是否存在
        messages = await store.get_messages(request.session_id)
        if not messages:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 生成唯一的分享ID
        share_id = secrets.token_urlsafe(16)

        # 设置过期时间
        expires_at = datetime.utcnow() + timedelta(days=request.expire_days)

        # 获取会话标题
        title = request.title
        if not title:
            # 使用第一条用户消息作为标题
            for msg in messages:
                if msg.get("role") == "user":
                    title = msg["content"][:50] + ("..." if len(msg["content"]) > 50 else "")
                    break
        if not title:
            title = f"对话分享 {share_id[:8]}"

        # 创建分享记录
        share_record = {
            "share_id": share_id,
            "session_id": request.session_id,
            "owner_user_id": current_user.id,
            "title": title,
            "description": request.description,
            "messages": messages,  # 存储消息快照
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "view_count": 0,
            "is_active": True
        }

        # 存储分享记录（实际应用中应使用数据库）
        _conversation_shares[share_id] = share_record

        # 生成公开URL
        public_url = f"/public/conversation/{share_id}"

        logger.info(f"用户 {current_user.id} 创建了对话分享: {share_id}")

        return ShareConversationResponse(
            share_id=share_id,
            public_url=public_url,
            title=title,
            expires_at=expires_at.isoformat(),
            created_at=share_record["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建对话分享失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/share/my-shares")
async def get_my_shares(
    current_user: User = Depends(require_auth)
):
    """
    获取我的对话分享列表

    显示当前用户创建的所有分享链接
    """
    try:
        my_shares = []
        current_time = datetime.utcnow()

        for share_id, share in _conversation_shares.items():
            if share.get("owner_user_id") == current_user.id:
                # 检查是否过期
                expires_at = datetime.fromisoformat(share["expires_at"])
                is_expired = current_time > expires_at

                share_info = {
                    "share_id": share_id,
                    "title": share["title"],
                    "public_url": f"/public/conversation/{share_id}",
                    "created_at": share["created_at"],
                    "expires_at": share["expires_at"],
                    "view_count": share.get("view_count", 0),
                    "is_expired": is_expired,
                    "is_active": share.get("is_active", False) and not is_expired
                }
                my_shares.append(share_info)

        # 按创建时间倒序排列
        my_shares.sort(key=lambda x: x["created_at"], reverse=True)

        return {"shares": my_shares}

    except Exception as e:
        logger.error(f"获取分享列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/share/{share_id}")
async def delete_share(
    share_id: str,
    current_user: User = Depends(require_auth)
):
    """
    删除对话分享链接

    立即失效分享链接
    """
    try:
        if share_id not in _conversation_shares:
            raise HTTPException(status_code=404, detail="分享不存在")

        share = _conversation_shares[share_id]
        if share.get("owner_user_id") != current_user.id:
            raise HTTPException(status_code=403, detail="无权限删除此分享")

        # 删除分享记录
        del _conversation_shares[share_id]

        logger.info(f"用户 {current_user.id} 删除了对话分享: {share_id}")

        return {"message": "分享链接已删除"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除分享失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 公开访问端点（不需要认证）
@router.get("/public/conversation/{share_id}", response_model=PublicConversationResponse)
async def get_public_conversation(share_id: str):
    """
    获取公开对话内容

    通过分享链接访问对话内容
    """
    try:
        if share_id not in _conversation_shares:
            raise HTTPException(status_code=404, detail="分享不存在或已过期")

        share = _conversation_shares[share_id]

        # 检查分享是否有效
        if not share.get("is_active", False):
            raise HTTPException(status_code=403, detail="分享已失效")

        # 检查是否过期
        expires_at = datetime.fromisoformat(share["expires_at"])
        current_time = datetime.utcnow()
        if current_time > expires_at:
            raise HTTPException(status_code=403, detail="分享已过期")

        # 增加访问计数
        share["view_count"] = share.get("view_count", 0) + 1

        return PublicConversationResponse(
            share_id=share_id,
            title=share["title"],
            description=share.get("description"),
            messages=share["messages"],
            created_at=share["created_at"],
            expires_at=share["expires_at"],
            view_count=share["view_count"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取公开对话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))