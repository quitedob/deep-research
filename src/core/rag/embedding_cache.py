#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量嵌入缓存 - 集成AgentScope的EmbeddingCache
支持DashScope, OpenAI, Ollama embedding
"""
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import hashlib
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """缓存配置"""
    enable_cache: bool = True
    cache_ttl_hours: int = 24
    max_cache_size: int = 10000
    cache_backend: str = "memory"  # memory, redis, disk


class EmbeddingCache:
    """向量嵌入缓存"""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
    def _generate_cache_key(self, text: str, model: str) -> str:
        """生成缓存键"""
        content = f"{model}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, text: str, model: str) -> Optional[List[float]]:
        """从缓存获取嵌入向量"""
        if not self.config.enable_cache:
            return None
        
        cache_key = self._generate_cache_key(text, model)
        
        if cache_key in self._memory_cache:
            cache_entry = self._memory_cache[cache_key]
            
            # 检查是否过期
            if self._is_expired(cache_entry):
                del self._memory_cache[cache_key]
                self._cache_misses += 1
                return None
            
            self._cache_hits += 1
            return cache_entry["embedding"]
        
        self._cache_misses += 1
        return None
    
    def set(self, text: str, model: str, embedding: List[float]) -> None:
        """设置缓存"""
        if not self.config.enable_cache:
            return
        
        # 检查缓存大小限制
        if len(self._memory_cache) >= self.config.max_cache_size:
            self._evict_oldest()
        
        cache_key = self._generate_cache_key(text, model)
        self._memory_cache[cache_key] = {
            "embedding": embedding,
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "text_length": len(text)
        }
    
    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """检查缓存是否过期"""
        timestamp = datetime.fromisoformat(cache_entry["timestamp"])
        expiry_time = timestamp + timedelta(hours=self.config.cache_ttl_hours)
        return datetime.now() > expiry_time
    
    def _evict_oldest(self) -> None:
        """驱逐最旧的缓存项"""
        if not self._memory_cache:
            return
        
        oldest_key = min(
            self._memory_cache.keys(),
            key=lambda k: self._memory_cache[k]["timestamp"]
        )
        del self._memory_cache[oldest_key]
        logger.debug(f"Evicted oldest cache entry: {oldest_key}")
    
    def clear(self) -> None:
        """清空缓存"""
        self._memory_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info("Embedding cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            "cache_size": len(self._memory_cache),
            "max_cache_size": self.config.max_cache_size,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": hit_rate,
            "enabled": self.config.enable_cache
        }


class EnhancedEmbeddingService:
    """增强的嵌入服务 - 支持多种embedding模型"""
    
    def __init__(
        self,
        provider: str = "dashscope",
        model: str = "text-embedding-v3",
        cache_config: Optional[CacheConfig] = None
    ):
        self.provider = provider
        self.model = model
        self.cache = EmbeddingCache(cache_config)
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """初始化embedding客户端"""
        try:
            if self.provider == "dashscope":
                from src.config import get_settings
                settings = get_settings()
                
                # DashScope embedding
                import dashscope
                dashscope.api_key = settings.dashscope_api_key
                self._client = dashscope.TextEmbedding
                logger.info(f"Initialized DashScope embedding: {self.model}")
                
            elif self.provider == "openai":
                from openai import AsyncOpenAI
                from src.config import get_settings
                settings = get_settings()
                
                self._client = AsyncOpenAI(api_key=settings.openai_api_key)
                logger.info(f"Initialized OpenAI embedding: {self.model}")
                
            elif self.provider == "ollama":
                import ollama
                self._client = ollama
                logger.info(f"Initialized Ollama embedding: {self.model}")
                
            else:
                raise ValueError(f"Unsupported embedding provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Failed to initialize embedding client: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """嵌入单个文本"""
        # 检查缓存
        cached_embedding = self.cache.get(text, self.model)
        if cached_embedding is not None:
            return cached_embedding
        
        # 调用embedding API
        try:
            if self.provider == "dashscope":
                response = self._client.call(
                    model=self.model,
                    input=text
                )
                embedding = response.output["embeddings"][0]["embedding"]
                
            elif self.provider == "openai":
                response = await self._client.embeddings.create(
                    model=self.model,
                    input=text
                )
                embedding = response.data[0].embedding
                
            elif self.provider == "ollama":
                response = self._client.embeddings(
                    model=self.model,
                    prompt=text
                )
                embedding = response["embedding"]
            
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            # 缓存结果
            self.cache.set(text, self.model, embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本"""
        embeddings = []
        
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
        
        return embeddings
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return self.cache.get_stats()
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()


# 全局实例
_embedding_service: Optional[EnhancedEmbeddingService] = None


def get_embedding_service(
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> EnhancedEmbeddingService:
    """获取嵌入服务实例"""
    global _embedding_service
    
    if _embedding_service is None:
        from src.config import get_settings
        settings = get_settings()
        
        provider = provider or settings.embedding_provider
        model = model or settings.embedding_model
        
        _embedding_service = EnhancedEmbeddingService(
            provider=provider,
            model=model
        )
    
    return _embedding_service


def set_embedding_service(service: EnhancedEmbeddingService) -> None:
    """设置嵌入服务实例"""
    global _embedding_service
    _embedding_service = service
