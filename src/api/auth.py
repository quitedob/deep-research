# -*- coding: utf-8 -*-
"""
Auth API：/api/auth/register、/api/auth/login、/api/auth/me
最小可用：OAuth2 密码模式 + JWT；依赖数据库。
遵循 api->service->dao 架构规范
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db_session
from src.services.auth_service import AuthService
from src.dao.users import UsersDAO


router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class RegisterReq(BaseModel):
    username: str
    email: str
    password: str


class TokenResp(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterResp(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    email: str
    role: str


class MeResp(BaseModel):
    id: int
    username: str
    email: str
    role: str


async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db_session)) -> dict:
    try:
        auth_service = AuthService(session)
        return await auth_service.decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")


@router.post("/register", response_model=RegisterResp)
async def register(payload: RegisterReq, session: AsyncSession = Depends(get_db_session)):
    """用户注册 - 通过AuthService处理业务逻辑"""
    auth_service = AuthService(session)

    # 检查用户名是否已存在
    dao = UsersDAO(session)
    exist = await dao.get_by_username(payload.username)
    if exist:
        raise HTTPException(status_code=400, detail="username exists")

    # 验证密码强度
    password_errors = await auth_service.validate_password_strength(payload.password)
    if password_errors:
        raise HTTPException(status_code=400, detail=f"密码不符合要求: {', '.join(password_errors)}")

    # 哈希密码并创建用户
    password_hash = await auth_service.hash_password(payload.password)
    user = await dao.create(username=payload.username, email=payload.email, password_hash=password_hash)
    await session.commit()

    # 注册成功后自动生成token
    token = await auth_service.create_access_token(sub=str(user.id), role=user.role)

    return RegisterResp(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        email=user.email,
        role=user.role
    )


@router.post("/login", response_model=TokenResp)
async def login(form: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_db_session)):
    """用户登录 - 通过AuthService处理业务逻辑"""
    auth_service = AuthService(session)

    # 获取用户信息
    dao = UsersDAO(session)
    user = await dao.get_by_username(form.username)
    if not user:
        raise HTTPException(status_code=400, detail="incorrect username or password")

    # 验证密码
    if not await auth_service.verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=400, detail="incorrect username or password")

    # 生成token
    token = await auth_service.create_access_token(sub=str(user.id), role=user.role)
    return TokenResp(access_token=token)


@router.get("/me", response_model=MeResp)
async def me(claims: dict = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    """获取当前用户信息 - 通过DAO获取数据"""
    dao = UsersDAO(session)
    user = await dao.get_by_id(int(claims.get("sub")))
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return MeResp(id=user.id, username=user.username, email=user.email, role=user.role)


