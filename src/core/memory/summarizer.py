# -*- coding: utf-8 -*-
"""
对话摘要器
使用LLM对长对话进行智能摘要
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from .conversation_buffer import ChatMessage, ConversationBuffer
from ..llms.router import get_llm_router, TaskType

logger = logging.getLogger(__name__)

class BaseSummarizer(ABC):
    """摘要器基类"""
    
    @abstractmethod
    async def summarize_messages(self, messages: List[ChatMessage]) -> str:
        """摘要消息列表"""
        pass
    
    @abstractmethod
    async def summarize_conversation(self, conversation_buffer: ConversationBuffer) -> str:
        """摘要整个对话"""
        pass

class SimpleSummarizer(BaseSummarizer):
    """简单摘要器（基于规则）"""
    
    def __init__(self):
        pass
    
    async def summarize_messages(self, messages: List[ChatMessage]) -> str:
        """简单摘要实现"""
        if not messages:
            return "无对话内容"
        
        # 统计信息
        user_messages = [msg for msg in messages if msg.role == "user"]
        assistant_messages = [msg for msg in messages if msg.role == "assistant"]
        
        # 提取关键词（简单实现）
        keywords = set()
        for msg in messages:
            words = msg.content.lower().split()
            # 简单的关键词提取：长度大于3的词
            keywords.update([word for word in words if len(word) > 3])
        
        top_keywords = list(keywords)[:10]  # 取前10个关键词
        
        summary = f"对话包含{len(user_messages)}个用户消息和{len(assistant_messages)}个助手回复。"
        if top_keywords:
            summary += f"主要讨论的关键词包括：{', '.join(top_keywords[:5])}等。"
        
        return summary
    
    async def summarize_conversation(self, conversation_buffer: ConversationBuffer) -> str:
        """摘要整个对话"""
        messages = conversation_buffer.get_messages()
        return await self.summarize_messages(messages)

class LLMSummarizer(BaseSummarizer):
    """基于LLM的智能摘要器"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name
        self.llm_router = get_llm_router()
        
        # 摘要提示模板
        self.summary_prompt = """
请对以下对话内容进行摘要。摘要应该：
1. 简洁明了，突出要点
2. 保留重要的信息和结论
3. 保持逻辑性和连贯性
4. 长度控制在200字以内

对话内容：
{conversation}

请提供摘要：
"""
        
        self.progressive_summary_prompt = """
已有的对话摘要：
{existing_summary}

新的对话内容：
{new_conversation}

请将新的对话内容整合到现有摘要中，生成一个更新的综合摘要：
"""
    
    async def summarize_messages(self, messages: List[ChatMessage]) -> str:
        """使用LLM摘要消息"""
        if not messages:
            return "无对话内容"
        
        try:
            # 构建对话文本
            conversation_text = self._format_messages_for_summary(messages)
            
            # 构建摘要请求
            prompt = self.summary_prompt.format(conversation=conversation_text)
            
            # 使用LLM生成摘要
            from ..llms.base_llm import LLMMessage
            llm_messages = [LLMMessage(role="user", content=prompt)]
            
            provider, reasoning = await self.llm_router.route_request(
                llm_messages, 
                task_type=TaskType.CHAT
            )
            
            response = await provider.generate(llm_messages)
            summary = response.content.strip()
            
            logger.info(f"Generated LLM summary for {len(messages)} messages")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating LLM summary: {e}")
            # 回退到简单摘要
            simple_summarizer = SimpleSummarizer()
            return await simple_summarizer.summarize_messages(messages)
    
    async def summarize_conversation(self, conversation_buffer: ConversationBuffer) -> str:
        """摘要整个对话"""
        messages = conversation_buffer.get_messages()
        return await self.summarize_messages(messages)
    
    async def progressive_summarize(
        self, 
        existing_summary: str, 
        new_messages: List[ChatMessage]
    ) -> str:
        """渐进式摘要（将新对话整合到已有摘要中）"""
        if not new_messages:
            return existing_summary
        
        try:
            new_conversation = self._format_messages_for_summary(new_messages)
            
            prompt = self.progressive_summary_prompt.format(
                existing_summary=existing_summary,
                new_conversation=new_conversation
            )
            
            from ..llms.base_llm import LLMMessage
            llm_messages = [LLMMessage(role="user", content=prompt)]
            
            provider, reasoning = await self.llm_router.route_request(
                llm_messages,
                task_type=TaskType.CHAT
            )
            
            response = await provider.generate(llm_messages)
            updated_summary = response.content.strip()
            
            logger.info(f"Updated summary with {len(new_messages)} new messages")
            return updated_summary
            
        except Exception as e:
            logger.error(f"Error generating progressive summary: {e}")
            # 回退策略：简单连接
            new_summary = await self.summarize_messages(new_messages)
            return f"{existing_summary}\n\n新的对话摘要：{new_summary}"
    
    def _format_messages_for_summary(self, messages: List[ChatMessage]) -> str:
        """格式化消息用于摘要"""
        formatted_lines = []
        
        for msg in messages:
            role_name = {
                "user": "用户",
                "assistant": "助手", 
                "system": "系统"
            }.get(msg.role, msg.role)
            
            formatted_lines.append(f"{role_name}: {msg.content}")
        
        return "\n".join(formatted_lines)

class HierarchicalSummarizer(BaseSummarizer):
    """分层摘要器"""
    
    def __init__(self, chunk_size: int = 20):
        self.chunk_size = chunk_size
        self.llm_summarizer = LLMSummarizer()
    
    async def summarize_messages(self, messages: List[ChatMessage]) -> str:
        """分层摘要消息"""
        if len(messages) <= self.chunk_size:
            return await self.llm_summarizer.summarize_messages(messages)
        
        # 分块摘要
        chunk_summaries = []
        for i in range(0, len(messages), self.chunk_size):
            chunk = messages[i:i + self.chunk_size]
            chunk_summary = await self.llm_summarizer.summarize_messages(chunk)
            chunk_summaries.append(chunk_summary)
        
        # 合并摘要
        if len(chunk_summaries) == 1:
            return chunk_summaries[0]
        
        # 对摘要再进行摘要
        combined_summary = "\n\n".join([
            f"段落{i+1}摘要: {summary}" 
            for i, summary in enumerate(chunk_summaries)
        ])
        
        try:
            from ..llms.base_llm import LLMMessage
            prompt = f"请将以下分段摘要合并为一个连贯的总体摘要：\n\n{combined_summary}"
            llm_messages = [LLMMessage(role="user", content=prompt)]
            
            provider, reasoning = await self.llm_router.route_request(
                llm_messages,
                task_type=TaskType.CHAT
            )
            
            response = await provider.generate(llm_messages)
            final_summary = response.content.strip()
            
            return final_summary
            
        except Exception as e:
            logger.error(f"Error in hierarchical summary merge: {e}")
            return combined_summary
    
    async def summarize_conversation(self, conversation_buffer: ConversationBuffer) -> str:
        """分层摘要整个对话"""
        messages = conversation_buffer.get_messages()
        return await self.summarize_messages(messages)

class SummaryService:
    """摘要服务管理器"""
    
    def __init__(self):
        self.summarizers: Dict[str, BaseSummarizer] = {
            "simple": SimpleSummarizer(),
            "llm": LLMSummarizer(),
            "hierarchical": HierarchicalSummarizer()
        }
        self.default_summarizer = "llm"
    
    async def summarize_conversation(
        self,
        conversation_buffer: ConversationBuffer,
        summarizer_type: str = None
    ) -> str:
        """摘要对话"""
        summarizer_type = summarizer_type or self.default_summarizer
        
        if summarizer_type not in self.summarizers:
            logger.warning(f"Unknown summarizer type: {summarizer_type}, using default")
            summarizer_type = self.default_summarizer
        
        summarizer = self.summarizers[summarizer_type]
        return await summarizer.summarize_conversation(conversation_buffer)
    
    async def summarize_messages(
        self,
        messages: List[ChatMessage],
        summarizer_type: str = None
    ) -> str:
        """摘要消息列表"""
        summarizer_type = summarizer_type or self.default_summarizer
        
        if summarizer_type not in self.summarizers:
            logger.warning(f"Unknown summarizer type: {summarizer_type}, using default")
            summarizer_type = self.default_summarizer
        
        summarizer = self.summarizers[summarizer_type]
        return await summarizer.summarize_messages(messages)
    
    async def progressive_summarize(
        self,
        existing_summary: str,
        new_messages: List[ChatMessage],
        summarizer_type: str = None
    ) -> str:
        """渐进式摘要"""
        summarizer_type = summarizer_type or self.default_summarizer
        
        summarizer = self.summarizers.get(summarizer_type)
        if hasattr(summarizer, 'progressive_summarize'):
            return await summarizer.progressive_summarize(existing_summary, new_messages)
        else:
            # 回退：重新摘要所有内容
            new_summary = await summarizer.summarize_messages(new_messages)
            return f"{existing_summary}\n\n新的对话摘要：{new_summary}"
    
    def add_summarizer(self, name: str, summarizer: BaseSummarizer) -> None:
        """添加自定义摘要器"""
        self.summarizers[name] = summarizer
    
    def get_available_summarizers(self) -> List[str]:
        """获取可用的摘要器列表"""
        return list(self.summarizers.keys())

# 全局摘要服务实例
_summary_service = None

def get_summary_service() -> SummaryService:
    """获取全局摘要服务实例"""
    global _summary_service
    if _summary_service is None:
        _summary_service = SummaryService()
    return _summary_service

# 便捷函数
async def summarize_conversation(
    conversation_buffer: ConversationBuffer,
    summarizer_type: str = "llm"
) -> str:
    """便捷的对话摘要函数"""
    service = get_summary_service()
    return await service.summarize_conversation(conversation_buffer, summarizer_type)

async def summarize_messages(
    messages: List[ChatMessage],
    summarizer_type: str = "llm"
) -> str:
    """便捷的消息摘要函数"""
    service = get_summary_service()
    return await service.summarize_messages(messages, summarizer_type)
