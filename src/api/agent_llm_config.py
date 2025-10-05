# -*- coding: utf-8 -*-
"""
智能体 LLM 配置管理 API
管理员可以为每个智能体配置使用的 LLM 模型
"""
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import require_auth, require_admin
from ..sqlmodel.models import User
from ..database import get_async_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent-llm-config", tags=["agent-llm-config"])


# ==================== 请求/响应模型 ====================

class AgentLLMConfig(BaseModel):
    """智能体 LLM 配置"""
    agent_id: str
    agent_name: str
    llm_provider: str  # doubao, kimi, deepseek, ollama
    model_name: str
    description: Optional[str] = None


class UpdateAgentLLMRequest(BaseModel):
    """更新智能体 LLM 配置请求"""
    agent_id: str
    llm_provider: str
    model_name: Optional[str] = None


class BatchUpdateRequest(BaseModel):
    """批量更新请求"""
    configs: list[UpdateAgentLLMRequest]


# ==================== 智能体配置存储 ====================

# 默认智能体 LLM 配置
DEFAULT_AGENT_LLM_CONFIGS = {
    "research_coordinator": {
        "agent_name": "研究协调员",
        "llm_provider": "doubao",
        "model_name": "doubao-seed-1-6-flash-250615",
        "description": "协调整个研究流程"
    },
    "web_searcher": {
        "agent_name": "网络搜索专家",
        "llm_provider": "doubao",  # 默认使用 Doubao 联网搜索
        "model_name": "doubao-seed-1-6-flash-250615",
        "description": "执行联网搜索任务"
    },
    "data_analyst": {
        "agent_name": "数据分析师",
        "llm_provider": "deepseek",
        "model_name": "deepseek-chat",
        "description": "分析和处理数据"
    },
    "report_writer": {
        "agent_name": "报告撰写员",
        "llm_provider": "kimi",
        "model_name": "moonshot-v1-8k",
        "description": "撰写研究报告"
    },
    "code_expert": {
        "agent_name": "代码专家",
        "llm_provider": "deepseek",
        "model_name": "deepseek-chat",
        "description": "处理代码相关任务"
    },
    "vision_analyst": {
        "agent_name": "视觉分析师",
        "llm_provider": "doubao",
        "model_name": "doubao-1-5-vision-pro-250328",
        "description": "处理图像和视觉任务"
    }
}

# 全局配置存储（实际应用中应该存储在数据库）
_agent_llm_configs = DEFAULT_AGENT_LLM_CONFIGS.copy()


# ==================== API 端点 ====================

@router.get("/configs")
async def get_all_agent_configs(
    current_user: User = Depends(require_admin)
):
    """获取所有智能体的 LLM 配置"""
    try:
        configs = []
        for agent_id, config in _agent_llm_configs.items():
            configs.append({
                "agent_id": agent_id,
                **config
            })
        
        return {
            "success": True,
            "configs": configs,
            "total": len(configs)
        }
    
    except Exception as e:
        logger.error(f"获取智能体配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configs/{agent_id}")
async def get_agent_config(
    agent_id: str,
    current_user: User = Depends(require_auth)
):
    """获取指定智能体的 LLM 配置"""
    try:
        if agent_id not in _agent_llm_configs:
            raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 不存在")
        
        config = _agent_llm_configs[agent_id]
        return {
            "success": True,
            "agent_id": agent_id,
            **config
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取智能体配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/configs/{agent_id}")
async def update_agent_config(
    agent_id: str,
    request: UpdateAgentLLMRequest,
    current_user: User = Depends(require_admin)
):
    """更新指定智能体的 LLM 配置"""
    try:
        if agent_id not in _agent_llm_configs:
            raise HTTPException(status_code=404, detail=f"智能体 {agent_id} 不存在")
        
        # 更新配置
        _agent_llm_configs[agent_id]["llm_provider"] = request.llm_provider
        if request.model_name:
            _agent_llm_configs[agent_id]["model_name"] = request.model_name
        
        logger.info(f"更新智能体 {agent_id} 的 LLM 配置: {request.llm_provider}")
        
        return {
            "success": True,
            "message": f"智能体 {agent_id} 的 LLM 配置已更新",
            "agent_id": agent_id,
            **_agent_llm_configs[agent_id]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新智能体配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/configs/batch-update")
async def batch_update_configs(
    request: BatchUpdateRequest,
    current_user: User = Depends(require_admin)
):
    """批量更新智能体 LLM 配置"""
    try:
        updated = []
        failed = []
        
        for config in request.configs:
            try:
                if config.agent_id not in _agent_llm_configs:
                    failed.append({
                        "agent_id": config.agent_id,
                        "error": "智能体不存在"
                    })
                    continue
                
                _agent_llm_configs[config.agent_id]["llm_provider"] = config.llm_provider
                if config.model_name:
                    _agent_llm_configs[config.agent_id]["model_name"] = config.model_name
                
                updated.append(config.agent_id)
            
            except Exception as e:
                failed.append({
                    "agent_id": config.agent_id,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "message": f"成功更新 {len(updated)} 个智能体配置",
            "updated": updated,
            "failed": failed
        }
    
    except Exception as e:
        logger.error(f"批量更新智能体配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-providers")
async def get_available_providers(
    current_user: User = Depends(require_auth)
):
    """获取可用的 LLM 提供商和模型"""
    try:
        from ..config.config_loader import get_settings
        settings = get_settings()
        
        providers = {
            "doubao": {
                "name": "豆包 (Doubao)",
                "models": [
                    {
                        "id": "doubao-seed-1-6-flash-250615",
                        "name": "Doubao-Seed-1.6-Flash",
                        "description": "快速响应，支持联网搜索",
                        "features": ["联网搜索", "函数调用", "上下文缓存"]
                    },
                    {
                        "id": "doubao-1-5-vision-pro-250328",
                        "name": "Doubao-1.5-Vision-Pro",
                        "description": "视觉理解模型",
                        "features": ["视觉理解", "图文混排", "视频理解"]
                    }
                ],
                "available": bool(settings.doubao_api_key)
            },
            "kimi": {
                "name": "Kimi (月之暗面)",
                "models": [
                    {
                        "id": "moonshot-v1-8k",
                        "name": "Moonshot-v1-8k",
                        "description": "标准上下文模型",
                        "features": ["联网搜索", "函数调用"]
                    },
                    {
                        "id": "moonshot-v1-128k",
                        "name": "Moonshot-v1-128k",
                        "description": "超长上下文模型",
                        "features": ["超长上下文", "联网搜索"]
                    }
                ],
                "available": bool(settings.kimi_api_key)
            },
            "deepseek": {
                "name": "DeepSeek",
                "models": [
                    {
                        "id": "deepseek-chat",
                        "name": "DeepSeek-Chat",
                        "description": "通用对话模型",
                        "features": ["深度推理", "代码生成"]
                    }
                ],
                "available": bool(settings.deepseek_api_key)
            },
            "ollama": {
                "name": "Ollama (本地)",
                "models": [
                    {
                        "id": settings.ollama_small_model,
                        "name": settings.ollama_small_model,
                        "description": "轻量级本地模型",
                        "features": ["本地部署", "隐私保护"]
                    },
                    {
                        "id": settings.ollama_large_model,
                        "name": settings.ollama_large_model,
                        "description": "大型本地模型",
                        "features": ["本地部署", "强大推理"]
                    }
                ],
                "available": True
            }
        }
        
        return {
            "success": True,
            "providers": providers
        }
    
    except Exception as e:
        logger.error(f"获取可用提供商失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-defaults")
async def reset_to_defaults(
    current_user: User = Depends(require_admin)
):
    """重置所有智能体配置为默认值"""
    try:
        global _agent_llm_configs
        _agent_llm_configs = DEFAULT_AGENT_LLM_CONFIGS.copy()
        
        logger.info("智能体 LLM 配置已重置为默认值")
        
        return {
            "success": True,
            "message": "所有智能体配置已重置为默认值",
            "configs": [
                {"agent_id": agent_id, **config}
                for agent_id, config in _agent_llm_configs.items()
            ]
        }
    
    except Exception as e:
        logger.error(f"重置配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_agent_llm_config(agent_id: str) -> Dict[str, Any]:
    """
    获取智能体的 LLM 配置（供其他模块调用）
    
    Args:
        agent_id: 智能体 ID
    
    Returns:
        LLM 配置字典
    """
    return _agent_llm_configs.get(agent_id, {
        "llm_provider": "doubao",
        "model_name": "doubao-seed-1-6-flash-250615"
    })
