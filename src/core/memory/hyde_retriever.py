#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HyDE (Hypothetical Document Embeddings) Retriever
使用假设文档生成提升检索质量
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio

from src.core.llm.ollama_llm import OllamaLLM

logger = logging.getLogger(__name__)


class HyDERetriever:
    """
    HyDE检索器
    
    工作原理：
    1. 用户提问 -> LLM生成假设性答案文档
    2. 对假设文档进行向量化
    3. 用假设文档的向量去检索真实文档
    4. 返回最相关的记忆片段
    """
    
    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        embedding_model: str = "embeddinggemma",
        generation_model: str = "gemma3:4b"
    ):
        """
        初始化HyDE检索器
        
        Args:
            ollama_base_url: Ollama服务地址
            embedding_model: 嵌入模型名称
            generation_model: 用于生成假设文档的模型
        """
        self.ollama = OllamaLLM(base_url=ollama_base_url)
        self.embedding_model = embedding_model
        self.generation_model = generation_model
        
        logger.info(f"HyDE Retriever initialized with embedding: {embedding_model}, generation: {generation_model}")
    
    async def generate_hypothetical_document(
        self,
        query: str,
        user_context: Optional[str] = None
    ) -> str:
        """
        生成假设文档
        
        Args:
            query: 用户查询
            user_context: 用户上下文信息
            
        Returns:
            假设文档内容
        """
        # 构建提示词
        system_prompt = """你是一个知识助手。用户会提出一个问题，请你生成一个简短的、假设性的答案。
这个答案不需要完全准确，但应该包含可能相关的关键信息和概念。
保持答案简洁，2-3句话即可。"""
        
        context_info = f"\n用户背景：{user_context}" if user_context else ""
        
        prompt = f"""问题：{query}{context_info}

请生成一个简短的假设性答案："""
        
        try:
            # 使用轻量级模型快速生成
            response = await self.ollama.generate_completion(
                prompt=prompt,
                model=self.generation_model,
                temperature=0.7,
                max_tokens=150,
                system=system_prompt
            )
            
            hypothetical_doc = response.get("choices", [{}])[0].get("text", "").strip()
            
            if not hypothetical_doc:
                # 如果生成失败，直接使用原始查询
                logger.warning("Failed to generate hypothetical document, using original query")
                return query
            
            logger.debug(f"Generated hypothetical document: {hypothetical_doc[:100]}...")
            return hypothetical_doc
            
        except Exception as e:
            logger.error(f"Error generating hypothetical document: {e}")
            return query
    
    async def embed_text(self, text: str) -> List[float]:
        """
        将文本转换为向量
        
        Args:
            text: 输入文本
            
        Returns:
            向量表示
        """
        try:
            embedding = await self.ollama.embeddings(
                input_text=text,
                model=self.embedding_model,
                truncate=True
            )
            
            if not embedding:
                logger.error("Empty embedding returned")
                return []
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []
    
    async def embed_query_with_hyde(
        self,
        query: str,
        user_context: Optional[str] = None,
        use_hyde: bool = True
    ) -> List[float]:
        """
        使用HyDE策略对查询进行向量化
        
        Args:
            query: 用户查询
            user_context: 用户上下文
            use_hyde: 是否使用HyDE（False则直接嵌入原始查询）
            
        Returns:
            查询向量
        """
        if use_hyde:
            # 生成假设文档
            hypothetical_doc = await self.generate_hypothetical_document(query, user_context)
            # 对假设文档进行向量化
            return await self.embed_text(hypothetical_doc)
        else:
            # 直接对原始查询进行向量化
            return await self.embed_text(query)
    
    async def batch_embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量嵌入文本
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        tasks = [self.embed_text(text) for text in texts]
        embeddings = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤掉失败的嵌入
        valid_embeddings = []
        for i, emb in enumerate(embeddings):
            if isinstance(emb, Exception):
                logger.error(f"Failed to embed text {i}: {emb}")
                valid_embeddings.append([])
            else:
                valid_embeddings.append(emb)
        
        return valid_embeddings
