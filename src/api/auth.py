# -*- coding: utf-8 -*-
"""
Auth API：/api/auth/register、/api/auth/login、/api/auth/me
最小可用：OAuth2 密码模式 + JWT；依赖数据库。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db_session
from src.dao.users import UsersDAO
from src.service.auth import hash_password, verify_password, create_access_token, decode_token


router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class RegisterReq(BaseModel):
    username: str
    email: str
    password: str


class TokenResp(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResp(BaseModel):
    id: int
    username: str
    email: str
    role: str


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")


@router.post("/register", response_model=MeResp)
async def register(payload: RegisterReq, session: AsyncSession = Depends(get_db_session)):
    dao = UsersDAO(session)
    exist = await dao.get_by_username(payload.username)
    if exist:
        raise HTTPException(status_code=400, detail="username exists")
    ph = hash_password(payload.password)
    user = await dao.create(username=payload.username, email=payload.email, password_hash=ph)
    await session.commit()
    return MeResp(id=user.id, username=user.username, email=user.email, role=user.role)


@router.post("/login", response_model=TokenResp)
async def login(form: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_db_session)):
    dao = UsersDAO(session)
    user = await dao.get_by_username(form.username)
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=400, detail="incorrect username or password")
    token = create_access_token(sub=str(user.id), role=user.role)
    return TokenResp(access_token=token)


@router.get("/me", response_model=MeResp)
async def me(claims: dict = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    dao = UsersDAO(session)
    user = await dao.get_by_id(int(claims.get("sub")))
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return MeResp(id=user.id, username=user.username, email=user.email, role=user.role)


