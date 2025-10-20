# -*- coding: utf-8 -*-
"""
历史记录API端点
"""

import logging

from fastapi import APIRouter, HTTPException

from src.services.session_service import store

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/histories")
async def list_histories():
    """获取历史会话列表"""
    try:
        sessions = await store.list_sessions()
        items = []
        for sid in sessions:
            msgs = await store.get_messages(sid)
            # 标题来源：第一条用户消息或 session_id 简短形式
            title = None
            for m in msgs:
                if m.get("role") == "user" and m.get("content"):
                    title = m["content"][:24]
                    break
            if not title:
                title = f"会话 {sid[:8]}"
            items.append({"session_id": sid, "title": title})
        return items
    except Exception as e:
        logger.error(f"获取历史记录列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/histories/{session_id}")
async def get_history_messages(session_id: str):
    """获取指定会话的消息历史"""
    try:
        return await store.get_messages(session_id)
    except Exception as e:
        logger.error(f"获取会话消息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/histories")
async def delete_all_histories():
    """删除所有历史记录"""
    try:
        await store.clear_all()
        return {"ok": True}
    except Exception as e:
        logger.error(f"删除历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))