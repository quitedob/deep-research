# -*- coding: utf-8 -*-
"""
认证与用户管理路由：注册/登录/用户信息  # 模块说明
"""
import hashlib  # 哈希
import hmac  # HMAC
import os  # 环境
import time  # 时间戳
from typing import Optional  # 类型
from fastapi import APIRouter, HTTPException, Header  # 路由
from pydantic import BaseModel  # 模型
from src.server.db import init_db, create_user, get_user_by_username  # DB

router = APIRouter(prefix="/api", tags=["用户与认证"])  # 路由器

SECRET = os.getenv("AUTH_SECRET", "agentwork-secret")  # 签名密钥


def sha256(text: str) -> str:
    """计算字符串SHA256"""  # 函数说明
    return hashlib.sha256(text.encode("utf-8")).hexdigest()  # 返回哈希


def sign_token(username: str, ttl_seconds: int = 7 * 24 * 3600) -> str:
    """签发简易Token：username|exp|sig"""  # 函数说明
    exp = int(time.time()) + ttl_seconds  # 过期时间
    msg = f"{username}|{exp}"  # 消息体
    sig = hmac.new(SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()  # 计算签名
    return f"{msg}|{sig}"  # 拼接token


def verify_token(token: str) -> Optional[str]:
    """验证Token并返回用户名"""  # 函数说明
    try:  # 保护
        username, exp_str, sig = token.split("|")  # 拆分
        msg = f"{username}|{exp_str}"  # 重建消息
        good = hmac.new(SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()  # 计算签名
        if not hmac.compare_digest(good, sig):  # 比较签名
            return None  # 无效
        if int(exp_str) < int(time.time()):  # 检查过期
            return None  # 过期
        return username  # 返回用户名
    except Exception:
        return None  # 解析失败


class RegisterRequest(BaseModel):
    username: str  # 用户名
    password: str  # 密码


class LoginRequest(BaseModel):
    username: str  # 用户名
    password: str  # 密码


@router.on_event("startup")
async def _ensure_admin():
    """应用启动时初始化数据库并创建默认管理员（admin/root123456）"""  # 函数说明
    default_hash = sha256("root123456")  # 计算默认密码哈希
    init_db(default_admin_password_hash=default_hash)  # 初始化DB


@router.post("/register")
async def register(req: RegisterRequest):
    """注册新用户（用户名唯一）"""  # 函数说明
    if not req.username or not req.password:  # 校验
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")  # 抛错
    if get_user_by_username(req.username):  # 重复检查
        raise HTTPException(status_code=400, detail="用户名已存在")  # 抛错
    user_id = create_user(req.username, sha256(req.password))  # 创建用户
    token = sign_token(req.username)  # 签发Token
    return {"user_id": user_id, "username": req.username, "token": token}  # 返回


@router.post("/login")
async def login(req: LoginRequest):
    """用户登录，返回签名Token"""  # 函数说明
    user = get_user_by_username(req.username)  # 查询用户
    if not user:  # 不存在
        raise HTTPException(status_code=401, detail="用户名或密码错误")  # 抛错
    if sha256(req.password) != user["password_hash"]:  # 校验密码
        raise HTTPException(status_code=401, detail="用户名或密码错误")  # 抛错
    token = sign_token(req.username)  # 签发Token
    return {"user_id": user["id"], "username": user["username"], "role": user["role"], "token": token}  # 返回


@router.get("/me")
async def me(authorization: Optional[str] = Header(default=None)):
    """根据Token返回当前用户信息"""  # 函数说明
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权")  # 抛错
    token = authorization.split(" ", 1)[1]  # 提取token
    username = verify_token(token)  # 验证
    if not username:  # 验证失败
        raise HTTPException(status_code=401, detail="Token 无效或已过期")  # 抛错
    user = get_user_by_username(username)  # 查询用户
    return {"user_id": user["id"], "username": user["username"], "role": user["role"]}  # 返回


