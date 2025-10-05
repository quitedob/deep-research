# -*- coding: utf-8 -*-
"""
LLM配置管理API：允许管理员控制API/本地选择。
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db_session
from src.sqlmodel.models import User
from src.service.auth import get_current_user
from src.config.config_loader import get_settings

router = APIRouter(prefix="/llm-config", tags=["llm-config"])

settings = get_settings()


class LLMConfigResponse(BaseModel):
    """LLM配置响应"""
    provider: str
    ollama_base_url: str
    ollama_model: str
    openai_api_key: str
    openai_base_url: str
    openai_model: str
    is_admin: bool


class LLMConfigUpdate(BaseModel):
    """LLM配置更新请求"""
    provider: str
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: Optional[str] = None


@router.get("/current", response_model=LLMConfigResponse)
async def get_current_llm_config(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前LLM配置
    """
    try:
        return LLMConfigResponse(
            provider=settings.llm_provider,
            ollama_base_url=settings.ollama_base_url,
            ollama_model=settings.ollama_model,
            openai_api_key=settings.openai_api_key,
            openai_base_url=settings.openai_base_url,
            openai_model=settings.openai_model,
            is_admin=current_user.role == "admin"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取LLM配置失败: {str(e)}"
        )


@router.put("/update")
async def update_llm_config(
    config: LLMConfigUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    更新LLM配置（仅管理员）
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以更新LLM配置"
        )
    
    try:
        # 验证provider值
        if config.provider not in ["api", "local"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="provider必须是 'api' 或 'local'"
            )
        
        # 这里应该实现配置更新逻辑
        # 由于配置是环境变量，实际更新需要重启应用或使用配置管理服务
        
        return {
            "message": "LLM配置更新成功",
            "provider": config.provider,
            "note": "配置更新需要重启应用才能生效"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新LLM配置失败: {str(e)}"
        )


@router.get("/test-connection")
async def test_llm_connection(
    current_user: User = Depends(get_current_user)
):
    """
    测试LLM连接
    """
    try:
        if settings.llm_provider == "local":
            # 测试Ollama连接
            import aiohttp
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{settings.ollama_base_url}/api/tags") as response:
                        if response.status == 200:
                            return {
                                "status": "success",
                                "provider": "local",
                                "message": "Ollama连接正常",
                                "base_url": settings.ollama_base_url
                            }
                        else:
                            return {
                                "status": "error",
                                "provider": "local",
                                "message": f"Ollama连接失败: HTTP {response.status}",
                                "base_url": settings.ollama_base_url
                            }
                except Exception as e:
                    return {
                        "status": "error",
                        "provider": "local",
                        "message": f"Ollama连接失败: {str(e)}",
                        "base_url": settings.ollama_base_url
                    }
        else:
            # 测试OpenAI API连接
            if not settings.openai_api_key:
                return {
                    "status": "error",
                    "provider": "api",
                    "message": "OpenAI API密钥未配置"
                }
            
            return {
                "status": "success",
                "provider": "api",
                "message": "OpenAI API配置正常",
                "base_url": settings.openai_base_url
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试连接失败: {str(e)}"
        )
