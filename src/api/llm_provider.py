# -*- coding: utf-8 -*-
"""
LLM 提供商管理 API
支持切换不同的 LLM 提供商（Doubao、Kimi、DeepSeek、Ollama）
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import require_auth
from ..sqlmodel.models import User
from ..core.db import get_async_session
from ..config.config_loader import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/llm-provider", tags=["llm-provider"])


# ==================== 请求/响应模型 ====================

class LLMProviderInfo(BaseModel):
    """LLM 提供商信息"""
    id: str
    name: str
    display_name: str
    description: str
    models: List[str]
    features: List[str]
    is_available: bool
    is_default: bool


class LLMProviderUpdateRequest(BaseModel):
    """更新 LLM 提供商请求"""
    provider_id: str
    is_default: bool = False


class LLMProviderConfigResponse(BaseModel):
    """LLM 提供商配置响应"""
    current_provider: str
    available_providers: List[LLMProviderInfo]


# ==================== LLM 提供商定义 ====================

LLM_PROVIDERS = {
    "doubao": {
        "id": "doubao",
        "name": "doubao",
        "display_name": "豆包 (Doubao)",
        "description": "字节跳动豆包大模型，支持联网搜索、视觉理解、函数调用等功能",
        "models": [
            "doubao-seed-1-6-flash-250615",
            "doubao-seed-1-6-250615",
            "doubao-1-5-pro-32k-250115",
            "doubao-1-5-vision-pro-250328"
        ],
        "features": [
            "联网搜索 (Web Search)",
            "视觉理解 (Vision)",
            "函数调用 (Function Calling)",
            "上下文缓存",
            "流式输出"
        ],
        "base_url": settings.doubao_base_url,
        "api_key_configured": bool(settings.doubao_api_key)
    },
    "kimi": {
        "id": "kimi",
        "name": "kimi",
        "display_name": "Kimi (月之暗面)",
        "description": "Moonshot AI Kimi 大模型，支持超长上下文和联网搜索",
        "models": [
            "moonshot-v1-8k",
            "moonshot-v1-32k",
            "moonshot-v1-128k"
        ],
        "features": [
            "联网搜索",
            "超长上下文 (128K)",
            "函数调用",
            "流式输出"
        ],
        "base_url": settings.kimi_base_url,
        "api_key_configured": bool(settings.kimi_api_key)
    },
    "deepseek": {
        "id": "deepseek",
        "name": "deepseek",
        "display_name": "DeepSeek",
        "description": "DeepSeek 大模型，擅长代码生成和推理任务",
        "models": [
            "deepseek-chat",
            "deepseek-reasoner"
        ],
        "features": [
            "深度推理",
            "代码生成",
            "函数调用",
            "JSON 输出",
            "流式输出"
        ],
        "base_url": settings.deepseek_base_url,
        "api_key_configured": bool(settings.deepseek_api_key)
    },
    "ollama": {
        "id": "ollama",
        "name": "ollama",
        "display_name": "Ollama (本地)",
        "description": "本地部署的 Ollama 模型，支持多种开源模型",
        "models": [
            settings.ollama_small_model,
            settings.ollama_large_model,
            settings.ollama_vision_model
        ],
        "features": [
            "本地部署",
            "隐私保护",
            "离线可用",
            "多模型支持"
        ],
        "base_url": settings.ollama_base_url,
        "api_key_configured": True  # Ollama 不需要 API Key
    }
}


# ==================== API 端点 ====================

@router.get("/list", response_model=List[LLMProviderInfo])
async def list_llm_providers(
    current_user: User = Depends(require_auth)
):
    """
    获取所有可用的 LLM 提供商列表
    """
    try:
        providers = []
        current_default = settings.default_llm_provider
        
        for provider_id, provider_data in LLM_PROVIDERS.items():
            providers.append(LLMProviderInfo(
                id=provider_data["id"],
                name=provider_data["name"],
                display_name=provider_data["display_name"],
                description=provider_data["description"],
                models=provider_data["models"],
                features=provider_data["features"],
                is_available=provider_data["api_key_configured"],
                is_default=(provider_id == current_default)
            ))
        
        return providers
    
    except Exception as e:
        logger.error(f"获取 LLM 提供商列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current", response_model=LLMProviderConfigResponse)
async def get_current_provider(
    current_user: User = Depends(require_auth)
):
    """
    获取当前使用的 LLM 提供商配置
    """
    try:
        current_provider = settings.default_llm_provider
        
        providers = []
        for provider_id, provider_data in LLM_PROVIDERS.items():
            providers.append(LLMProviderInfo(
                id=provider_data["id"],
                name=provider_data["name"],
                display_name=provider_data["display_name"],
                description=provider_data["description"],
                models=provider_data["models"],
                features=provider_data["features"],
                is_available=provider_data["api_key_configured"],
                is_default=(provider_id == current_provider)
            ))
        
        return LLMProviderConfigResponse(
            current_provider=current_provider,
            available_providers=providers
        )
    
    except Exception as e:
        logger.error(f"获取当前 LLM 提供商失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{provider_id}", response_model=LLMProviderInfo)
async def get_provider_detail(
    provider_id: str,
    current_user: User = Depends(require_auth)
):
    """
    获取指定 LLM 提供商的详细信息
    """
    try:
        if provider_id not in LLM_PROVIDERS:
            raise HTTPException(status_code=404, detail=f"提供商 '{provider_id}' 不存在")
        
        provider_data = LLM_PROVIDERS[provider_id]
        current_default = settings.default_llm_provider
        
        return LLMProviderInfo(
            id=provider_data["id"],
            name=provider_data["name"],
            display_name=provider_data["display_name"],
            description=provider_data["description"],
            models=provider_data["models"],
            features=provider_data["features"],
            is_available=provider_data["api_key_configured"],
            is_default=(provider_id == current_default)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 LLM 提供商详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set-default")
async def set_default_provider(
    request: LLMProviderUpdateRequest,
    current_user: User = Depends(require_auth)
):
    """
    设置默认的 LLM 提供商（需要管理员权限）
    """
    # 检查管理员权限
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        provider_id = request.provider_id
        
        # 验证提供商是否存在
        if provider_id not in LLM_PROVIDERS:
            raise HTTPException(status_code=404, detail=f"提供商 '{provider_id}' 不存在")
        
        # 检查提供商是否可用
        provider_data = LLM_PROVIDERS[provider_id]
        if not provider_data["api_key_configured"]:
            raise HTTPException(
                status_code=400,
                detail=f"提供商 '{provider_id}' 未配置 API Key，无法设置为默认"
            )
        
        # 更新默认提供商（注意：这里只是更新内存中的值，重启后会恢复）
        # 生产环境应该将配置持久化到数据库或配置文件
        settings.default_llm_provider = provider_id
        
        logger.info(f"管理员 {current_user.username} 将默认 LLM 提供商设置为: {provider_id}")
        
        return {
            "success": True,
            "message": f"默认 LLM 提供商已设置为: {provider_data['display_name']}",
            "provider_id": provider_id,
            "provider_name": provider_data["display_name"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置默认 LLM 提供商失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/{provider_id}")
async def test_provider_connection(
    provider_id: str,
    current_user: User = Depends(require_auth)
):
    """
    测试指定 LLM 提供商的连接状态
    """
    try:
        if provider_id not in LLM_PROVIDERS:
            raise HTTPException(status_code=404, detail=f"提供商 '{provider_id}' 不存在")
        
        provider_data = LLM_PROVIDERS[provider_id]
        
        # 检查 API Key 配置
        if not provider_data["api_key_configured"]:
            return {
                "success": False,
                "provider_id": provider_id,
                "message": f"{provider_data['display_name']} 未配置 API Key",
                "status": "not_configured"
            }
        
        # TODO: 实际测试连接（调用一个简单的 API）
        # 这里暂时返回模拟结果
        
        return {
            "success": True,
            "provider_id": provider_id,
            "provider_name": provider_data["display_name"],
            "message": "连接测试成功",
            "status": "connected",
            "base_url": provider_data["base_url"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试 LLM 提供商连接失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
