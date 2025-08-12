# -*- coding: utf-8 -*-
"""
后台管理路由：监控用户、聊天记录、使用统计  # 模块说明
"""
from typing import Optional  # 类型
from fastapi import APIRouter, HTTPException, Header  # FastAPI
from src.server.routers.auth import verify_token  # Token校验
from src.server.db import list_recent_chats, usage_summary  # DB函数

router = APIRouter(prefix="/api/admin", tags=["后台管理"])  # 路由器


def _require_admin(authorization: Optional[str]) -> None:
    """校验管理员权限（基于 Token + 角色）"""  # 函数说明
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权")  # 抛错
    username = verify_token(authorization.split(" ", 1)[1])  # 验证Token
    if username != "admin":  # 简易管理员判断
        raise HTTPException(status_code=403, detail="无权限")  # 抛错


@router.get("/chat_logs")
async def admin_chat_logs(authorization: Optional[str] = Header(default=None)):
    """获取最近聊天记录（默认50条）"""  # 函数说明
    _require_admin(authorization)  # 权限校验
    return {"items": list_recent_chats(50)}  # 返回数据


@router.get("/usage")
async def admin_usage(authorization: Optional[str] = Header(default=None)):
    """获取使用统计概览"""  # 函数说明
    _require_admin(authorization)  # 权限校验
    return usage_summary()  # 返回统计


