#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量嵌入API端点
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from src.core.rag.embedding_cache import get_embedding_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/embedding", tags=["embedding"])


class EmbedRequest(BaseModel):
    """嵌入请求"""
    text: str = Field(..., description="要嵌入的文本")
    provider: Optional[str] = Field(None, description="嵌入提供商")
    model: Optional[str] = Field(None, description="嵌入模型")


class EmbedBatchRequest(BaseModel):
    """批量嵌入请求"""
    texts: List[str] = Field(..., description="要嵌入的文本列表")
    provider: Optional[str] = Field(None, description="嵌入提供商")
    model: Optional[str] = Field(None, description="嵌入模型")


class EmbedResponse(BaseModel):
    """嵌入响应"""
    success: bool
    embedding: Optional[List[float]] = None
    dimension: Optional[int] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    cached: Optional[bool] = None
    error: Optional[str] = None


class EmbedBatchResponse(BaseModel):
    """批量嵌入响应"""
    success: bool
    embeddings: Optional[List[List[float]]] = None
    count: Optional[int] = None
    dimension: Optional[int] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    error: Optional[str] = None


@router.post("/embed", response_model=EmbedResponse)
async def embed_text(request: EmbedRequest):
    """
    嵌入单个文本
    
    支持的提供商：dashscope, openai, ollama
    """
    try:
        # 获取嵌入服务
        service = get_embedding_service(
            provider=request.provider,
            model=request.model
        )
        
        # 检查缓存
        cache_stats_before = service.get_cache_stats()
        hits_before = cache_stats_before["cache_hits"]
        
        # 执行嵌入
        embedding = await service.embed_text(request.text)
        
        # 检查是否使用了缓存
        cache_stats_after = service.get_cache_stats()
        hits_after = cache_stats_after["cache_hits"]
        cached = hits_after > hits_before
        
        return EmbedResponse(
            success=True,
            embedding=embedding,
            dimension=len(embedding),
            provider=service.provider,
            model=service.model,
            cached=cached
        )
        
    except Exception as e:
        logger.error(f"Embedding failed: {e}", exc_info=True)
        return EmbedResponse(
            success=False,
            error=str(e)
        )


@router.post("/embed/batch", response_model=EmbedBatchResponse)
async def embed_batch(request: EmbedBatchRequest):
    """
    批量嵌入文本
    
    支持的提供商：dashscope, openai, ollama
    """
    try:
        # 获取嵌入服务
        service = get_embedding_service(
            provider=request.provider,
            model=request.model
        )
        
        # 执行批量嵌入
        embeddings = await service.embed_batch(request.texts)
        
        return EmbedBatchResponse(
            success=True,
            embeddings=embeddings,
            count=len(embeddings),
            dimension=len(embeddings[0]) if embeddings else 0,
            provider=service.provider,
            model=service.model
        )
        
    except Exception as e:
        logger.error(f"Batch embedding failed: {e}", exc_info=True)
        return EmbedBatchResponse(
            success=False,
            error=str(e)
        )


@router.get("/cache/stats")
async def get_cache_stats():
    """获取缓存统计"""
    try:
        service = get_embedding_service()
        stats = service.get_cache_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache():
    """清空嵌入缓存"""
    try:
        service = get_embedding_service()
        service.clear_cache()
        
        return {
            "success": True,
            "message": "Embedding cache cleared"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))
