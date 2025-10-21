# -*- coding: utf-8 -*-
"""
嵌入模型服务
支持多种嵌入模型提供者，用于RAG系统的文本向量化
"""

import os
import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class EmbeddingResult:
    """嵌入结果数据类"""
    embeddings: List[List[float]]
    model: str
    usage: Optional[Dict[str, Any]] = None
    
    def to_numpy(self) -> np.ndarray:
        """转换为numpy数组"""
        return np.array(self.embeddings)

class BaseEmbeddingProvider(ABC):
    """基础嵌入提供者抽象类"""
    
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.config = kwargs
        self.is_initialized = False
        
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化嵌入提供者"""
        pass
    
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """嵌入文本列表"""
        pass
    
    async def embed_single_text(self, text: str) -> List[float]:
        """嵌入单个文本"""
        result = await self.embed_texts([text])
        return result.embeddings[0]
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        pass
    
    async def cleanup(self) -> None:
        """清理资源"""
        logger.info(f"{self.__class__.__name__} cleaned up")
    
    def get_dimension(self) -> int:
        """获取嵌入维度"""
        return 768  # 默认维度

class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """Ollama嵌入提供者"""
    
    def __init__(self, model_name: str = "nomic-embed-text", base_url: str = None, **kwargs):
        super().__init__(model_name, **kwargs)
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.session = None
        
        # 模型维度配置
        self.model_dimensions = {
            "nomic-embed-text": 768,
            "mxbai-embed-large": 1024,
            "all-minilm": 384,
            "paraphrase-multilingual": 768
        }
    
    async def initialize(self) -> bool:
        """初始化Ollama嵌入提供者"""
        try:
            import aiohttp
            
            connector = aiohttp.TCPConnector(limit=10)
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
            
            # 检查模型是否可用
            health = await self.health_check()
            if health.get("status") == "healthy":
                self.is_initialized = True
                logger.info(f"OllamaEmbeddingProvider initialized with model: {self.model_name}")
                return True
            else:
                logger.error("Ollama embedding model health check failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize Ollama embedding provider: {e}")
            return False
    
    async def embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """嵌入文本列表"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            embeddings = []
            
            # Ollama一次只能处理一个文本
            for text in texts:
                request_data = {
                    "model": self.model_name,
                    "prompt": text
                }
                
                async with self.session.post(
                    f"{self.base_url}/api/embeddings",
                    json=request_data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama embedding error {response.status}: {error_text}")
                    
                    result = await response.json()
                    embedding = result.get("embedding", [])
                    embeddings.append(embedding)
            
            return EmbeddingResult(
                embeddings=embeddings,
                model=self.model_name,
                usage={"total_texts": len(texts)}
            )
            
        except Exception as e:
            logger.error(f"Ollama embedding failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self.session:
                return {"status": "unhealthy", "error": "Session not initialized"}
            
            start_time = time.time()
            
            # 测试嵌入一个简单文本
            test_data = {
                "model": self.model_name,
                "prompt": "test"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/embeddings",
                json=test_data
            ) as response:
                latency = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    result = await response.json()
                    embedding = result.get("embedding", [])
                    
                    return {
                        "status": "healthy",
                        "model": self.model_name,
                        "provider": "ollama",
                        "latency_ms": round(latency, 2),
                        "dimension": len(embedding) if embedding else self.get_dimension()
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "model": self.model_name,
                        "provider": "ollama",
                        "error": f"HTTP {response.status}"
                    }
                    
        except Exception as e:
            return {
                "status": "unhealthy",
                "model": self.model_name,
                "provider": "ollama",
                "error": str(e)
            }
    
    async def cleanup(self) -> None:
        """清理资源"""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("OllamaEmbeddingProvider cleaned up")
    
    def get_dimension(self) -> int:
        """获取嵌入维度"""
        return self.model_dimensions.get(self.model_name, 768)

class SentenceTransformersProvider(BaseEmbeddingProvider):
    """SentenceTransformers本地嵌入提供者"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", **kwargs):
        super().__init__(model_name, **kwargs)
        self.model = None
        
        # 支持的模型配置
        self.model_configs = {
            "all-MiniLM-L6-v2": {"dimension": 384, "max_length": 512},
            "all-mpnet-base-v2": {"dimension": 768, "max_length": 512},
            "paraphrase-multilingual-MiniLM-L12-v2": {"dimension": 384, "max_length": 512},
            "distiluse-base-multilingual-cased": {"dimension": 512, "max_length": 512}
        }
    
    async def initialize(self) -> bool:
        """初始化SentenceTransformers提供者"""
        try:
            from sentence_transformers import SentenceTransformers
            
            # 在线程池中加载模型（避免阻塞事件循环）
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, SentenceTransformers, self.model_name
            )
            
            self.is_initialized = True
            logger.info(f"SentenceTransformers initialized with model: {self.model_name}")
            return True
            
        except ImportError:
            logger.error("SentenceTransformers not installed. Please install with: pip install sentence-transformers")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize SentenceTransformers: {e}")
            return False
    
    async def embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """嵌入文本列表"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # 在线程池中执行嵌入（避免阻塞）
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, self.model.encode, texts, {"convert_to_numpy": True}
            )
            
            # 转换为列表格式
            embeddings_list = embeddings.tolist()
            
            return EmbeddingResult(
                embeddings=embeddings_list,
                model=self.model_name,
                usage={"total_texts": len(texts)}
            )
            
        except Exception as e:
            logger.error(f"SentenceTransformers embedding failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self.model:
                return {"status": "unhealthy", "error": "Model not loaded"}
            
            start_time = time.time()
            
            # 测试嵌入
            test_embedding = await self.embed_single_text("test")
            latency = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "model": self.model_name,
                "provider": "sentence_transformers",
                "latency_ms": round(latency, 2),
                "dimension": len(test_embedding)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "model": self.model_name,
                "provider": "sentence_transformers",
                "error": str(e)
            }
    
    def get_dimension(self) -> int:
        """获取嵌入维度"""
        config = self.model_configs.get(self.model_name, {})
        return config.get("dimension", 384)

class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI嵌入提供者"""
    
    def __init__(self, model_name: str = "text-embedding-3-small", api_key: str = None, **kwargs):
        super().__init__(model_name, **kwargs)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.session = None
        
        # OpenAI模型配置
        self.model_configs = {
            "text-embedding-3-small": {"dimension": 1536, "max_tokens": 8191},
            "text-embedding-3-large": {"dimension": 3072, "max_tokens": 8191},
            "text-embedding-ada-002": {"dimension": 1536, "max_tokens": 8191}
        }
    
    async def initialize(self) -> bool:
        """初始化OpenAI嵌入提供者"""
        if not self.api_key:
            logger.error("OpenAI API key not provided")
            return False
        
        try:
            import aiohttp
            
            connector = aiohttp.TCPConnector(limit=50)
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            self.is_initialized = True
            logger.info(f"OpenAIEmbeddingProvider initialized with model: {self.model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI embedding provider: {e}")
            return False
    
    async def embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """嵌入文本列表"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            request_data = {
                "model": self.model_name,
                "input": texts
            }
            
            async with self.session.post(
                "https://api.openai.com/v1/embeddings",
                json=request_data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI embedding error {response.status}: {error_text}")
                
                result = await response.json()
                
                # 提取嵌入向量
                embeddings = [item["embedding"] for item in result["data"]]
                
                return EmbeddingResult(
                    embeddings=embeddings,
                    model=result.get("model", self.model_name),
                    usage=result.get("usage")
                )
                
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self.session:
                return {"status": "unhealthy", "error": "Session not initialized"}
            
            start_time = time.time()
            
            # 测试嵌入
            test_data = {
                "model": self.model_name,
                "input": ["test"]
            }
            
            async with self.session.post(
                "https://api.openai.com/v1/embeddings",
                json=test_data
            ) as response:
                latency = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    result = await response.json()
                    embedding = result["data"][0]["embedding"]
                    
                    return {
                        "status": "healthy",
                        "model": self.model_name,
                        "provider": "openai",
                        "latency_ms": round(latency, 2),
                        "dimension": len(embedding)
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "model": self.model_name,
                        "provider": "openai",
                        "error": f"HTTP {response.status}"
                    }
                    
        except Exception as e:
            return {
                "status": "unhealthy",
                "model": self.model_name,
                "provider": "openai",
                "error": str(e)
            }
    
    async def cleanup(self) -> None:
        """清理资源"""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("OpenAIEmbeddingProvider cleaned up")
    
    def get_dimension(self) -> int:
        """获取嵌入维度"""
        config = self.model_configs.get(self.model_name, {})
        return config.get("dimension", 1536)

class MockEmbeddingProvider(BaseEmbeddingProvider):
    """模拟嵌入提供者，用于测试"""
    
    def __init__(self, model_name: str = "mock-embedding", dimension: int = 768, **kwargs):
        super().__init__(model_name, **kwargs)
        self.dimension = dimension
    
    async def initialize(self) -> bool:
        """初始化模拟提供者"""
        self.is_initialized = True
        logger.info("MockEmbeddingProvider initialized")
        return True
    
    async def embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """生成模拟嵌入"""
        embeddings = []
        
        for text in texts:
            # 基于文本哈希生成稳定的模拟向量
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            
            # 转换为数字并归一化
            embedding = []
            for i in range(self.dimension):
                # 使用哈希值的不同部分生成向量元素
                hash_part = text_hash[i % len(text_hash)]
                value = (ord(hash_part) - 48) / 128.0 - 0.5  # 归一化到[-0.5, 0.5]
                embedding.append(value)
            
            embeddings.append(embedding)
        
        return EmbeddingResult(
            embeddings=embeddings,
            model=self.model_name,
            usage={"total_texts": len(texts)}
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """模拟健康检查"""
        return {
            "status": "healthy",
            "model": self.model_name,
            "provider": "mock",
            "latency_ms": 1,
            "dimension": self.dimension
        }
    
    def get_dimension(self) -> int:
        """获取嵌入维度"""
        return self.dimension

class EmbeddingService:
    """嵌入服务管理器"""
    
    def __init__(self):
        self.providers: Dict[str, BaseEmbeddingProvider] = {}
        self.default_provider = None
        self._initialize_providers()
    
    def _initialize_providers(self):
        """初始化嵌入提供者"""
        try:
            # 优先顺序：Ollama > SentenceTransformers > OpenAI > Mock
            
            # Ollama嵌入
            if os.getenv("OLLAMA_BASE_URL"):
                ollama_provider = OllamaEmbeddingProvider()
                self.providers["ollama"] = ollama_provider
            
            # SentenceTransformers
            st_provider = SentenceTransformersProvider()
            self.providers["sentence_transformers"] = st_provider
            
            # OpenAI
            if os.getenv("OPENAI_API_KEY"):
                openai_provider = OpenAIEmbeddingProvider()
                self.providers["openai"] = openai_provider
            
            # 模拟提供者（总是可用）
            mock_provider = MockEmbeddingProvider()
            self.providers["mock"] = mock_provider
            
            # 设置默认提供者
            if "ollama" in self.providers:
                self.default_provider = self.providers["ollama"]
            elif "sentence_transformers" in self.providers:
                self.default_provider = self.providers["sentence_transformers"]
            else:
                self.default_provider = self.providers["mock"]
            
            logger.info(f"Initialized {len(self.providers)} embedding providers")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding providers: {e}")
    
    async def initialize_all_providers(self) -> Dict[str, bool]:
        """初始化所有提供者"""
        results = {}
        
        for name, provider in self.providers.items():
            try:
                success = await provider.initialize()
                results[name] = success
                if success:
                    logger.info(f"Embedding provider '{name}' initialized successfully")
                else:
                    logger.warning(f"Embedding provider '{name}' failed to initialize")
            except Exception as e:
                results[name] = False
                logger.error(f"Embedding provider '{name}' initialization error: {e}")
        
        return results
    
    async def embed_texts(
        self, 
        texts: List[str], 
        provider_name: Optional[str] = None
    ) -> EmbeddingResult:
        """嵌入文本列表"""
        provider = self._get_provider(provider_name)
        
        if not provider.is_initialized:
            await provider.initialize()
        
        return await provider.embed_texts(texts)
    
    async def embed_single_text(
        self, 
        text: str, 
        provider_name: Optional[str] = None
    ) -> List[float]:
        """嵌入单个文本"""
        result = await self.embed_texts([text], provider_name)
        return result.embeddings[0]
    
    def _get_provider(self, provider_name: Optional[str] = None) -> BaseEmbeddingProvider:
        """获取指定的提供者"""
        if provider_name:
            if provider_name not in self.providers:
                raise ValueError(f"Unknown embedding provider: {provider_name}")
            return self.providers[provider_name]
        
        return self.default_provider
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """检查所有提供者的健康状态"""
        results = {}
        
        for name, provider in self.providers.items():
            try:
                health = await provider.health_check()
                results[name] = health
            except Exception as e:
                results[name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return results
    
    async def cleanup_all_providers(self):
        """清理所有提供者"""
        for provider in self.providers.values():
            try:
                await provider.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up embedding provider: {e}")

# 全局嵌入服务实例
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """获取全局嵌入服务实例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
