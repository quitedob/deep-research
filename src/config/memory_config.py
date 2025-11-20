#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆系统配置管理
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class MemoryConfig:
    """记忆系统配置"""
    
    # 基础配置
    enabled: bool = True
    
    # Ollama 配置
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "embeddinggemma"
    generation_model: str = "gemma3:4b"
    
    # ChromaDB 配置
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection_name: str = "user_memories"
    
    # HyDE 配置
    hyde_enabled: bool = True
    hyde_temperature: float = 0.7
    hyde_max_tokens: int = 150
    
    # 检索配置
    retrieval_top_k: int = 5
    min_validity_score: float = 0.7
    
    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1小时
    query_cache_ttl: int = 300  # 5分钟
    
    # 提取配置
    extraction_temperature: float = 0.3
    extraction_max_tokens: int = 500
    
    # 性能配置
    batch_size: int = 10
    max_fact_length: int = 500
    min_fact_length: int = 5
    
    @classmethod
    def from_env(cls) -> "MemoryConfig":
        """从环境变量加载配置"""
        return cls(
            enabled=os.getenv("MEMORY_ENABLED", "true").lower() == "true",
            
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            embedding_model=os.getenv("OLLAMA_EMBEDDING_MODEL", "embeddinggemma"),
            generation_model=os.getenv("OLLAMA_GENERATION_MODEL", "gemma3:4b"),
            
            chroma_persist_dir=os.getenv("CHROMA_PERSIST_DIR", "./data/chroma"),
            chroma_collection_name=os.getenv("CHROMA_COLLECTION_NAME", "user_memories"),
            
            hyde_enabled=os.getenv("HYDE_ENABLED", "true").lower() == "true",
            hyde_temperature=float(os.getenv("HYDE_TEMPERATURE", "0.7")),
            hyde_max_tokens=int(os.getenv("HYDE_MAX_TOKENS", "150")),
            
            retrieval_top_k=int(os.getenv("MEMORY_TOP_K", "5")),
            min_validity_score=float(os.getenv("MEMORY_MIN_VALIDITY", "0.7")),
            
            cache_enabled=os.getenv("MEMORY_CACHE_ENABLED", "true").lower() == "true",
            cache_ttl=int(os.getenv("MEMORY_CACHE_TTL", "3600")),
            query_cache_ttl=int(os.getenv("MEMORY_QUERY_CACHE_TTL", "300")),
            
            extraction_temperature=float(os.getenv("MEMORY_EXTRACTION_TEMP", "0.3")),
            extraction_max_tokens=int(os.getenv("MEMORY_EXTRACTION_MAX_TOKENS", "500")),
            
            batch_size=int(os.getenv("MEMORY_BATCH_SIZE", "10")),
            max_fact_length=int(os.getenv("MEMORY_MAX_FACT_LENGTH", "500")),
            min_fact_length=int(os.getenv("MEMORY_MIN_FACT_LENGTH", "5"))
        )
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        验证配置
        
        Returns:
            (is_valid, error_message)
        """
        if not self.enabled:
            return True, None
        
        if not self.ollama_base_url:
            return False, "OLLAMA_BASE_URL is required"
        
        if not self.embedding_model:
            return False, "OLLAMA_EMBEDDING_MODEL is required"
        
        if not self.generation_model:
            return False, "OLLAMA_GENERATION_MODEL is required"
        
        if not self.chroma_persist_dir:
            return False, "CHROMA_PERSIST_DIR is required"
        
        if self.retrieval_top_k < 1:
            return False, "MEMORY_TOP_K must be >= 1"
        
        if not (0.0 <= self.min_validity_score <= 1.0):
            return False, "MEMORY_MIN_VALIDITY must be between 0.0 and 1.0"
        
        return True, None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "enabled": self.enabled,
            "ollama_base_url": self.ollama_base_url,
            "embedding_model": self.embedding_model,
            "generation_model": self.generation_model,
            "chroma_persist_dir": self.chroma_persist_dir,
            "hyde_enabled": self.hyde_enabled,
            "retrieval_top_k": self.retrieval_top_k,
            "min_validity_score": self.min_validity_score,
            "cache_enabled": self.cache_enabled
        }


# 全局配置实例
_memory_config: Optional[MemoryConfig] = None


def get_memory_config() -> MemoryConfig:
    """获取全局记忆配置实例（单例模式）"""
    global _memory_config
    if _memory_config is None:
        _memory_config = MemoryConfig.from_env()
    return _memory_config


def validate_memory_config() -> tuple[bool, Optional[str]]:
    """验证记忆系统配置"""
    config = get_memory_config()
    return config.validate()
