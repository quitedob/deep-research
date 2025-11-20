#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆提取 Agent
后台异步分析对话，提取值得记忆的事实
"""

import logging
from typing import List, Dict, Any, Optional
import json

from src.core.llm.ollama_llm import OllamaLLM
from src.core.memory.memory_manager import Mem0MemoryManager
from src.dao.memory_dao import MemoryDAO

logger = logging.getLogger(__name__)


class MemoryAgent:
    """
    记忆提取Agent
    
    职责：
    1. 分析对话内容
    2. 识别值得记忆的信息（用户偏好、背景、技能等）
    3. 提取结构化事实
    4. 存储到记忆系统
    """
    
    # 事实类型定义
    FACT_TYPES = {
        "preference": "用户偏好",
        "skill": "技能水平",
        "background": "背景信息",
        "goal": "目标意图",
        "constraint": "约束条件",
        "general": "一般信息"
    }
    
    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        extraction_model: str = "gemma3:4b"
    ):
        """
        初始化记忆Agent
        
        Args:
            ollama_base_url: Ollama服务地址
            extraction_model: 用于提取的轻量级模型
        """
        self.ollama = OllamaLLM(base_url=ollama_base_url)
        self.extraction_model = extraction_model
        self.memory_manager = Mem0MemoryManager(ollama_base_url=ollama_base_url)
        self.memory_dao = MemoryDAO()
        
        logger.info(f"Memory Agent initialized with model: {extraction_model}")
    
    async def extract_facts_from_conversation(
        self,
        user_message: str,
        assistant_message: str,
        conversation_context: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        从对话中提取事实
        
        Args:
            user_message: 用户消息
            assistant_message: 助手回复
            conversation_context: 对话上下文（可选）
            
        Returns:
            提取的事实列表
        """
        # 构建提示词
        system_prompt = """你是一个记忆提取助手。分析用户和助手的对话，提取值得长期记忆的信息。

重点关注：
1. 用户的偏好和习惯
2. 用户的技能水平和背景
3. 用户的目标和意图
4. 重要的约束条件
5. 需要记住的关键信息

输出格式为JSON数组，每个事实包含：
- fact_content: 事实内容（简洁明确）
- fact_type: 类型（preference/skill/background/goal/constraint/general）
- validity_score: 可信度（0.0-1.0）

如果没有值得记忆的信息，返回空数组 []。

示例输出：
[
  {
    "fact_content": "用户是Python初学者",
    "fact_type": "skill",
    "validity_score": 0.9
  },
  {
    "fact_content": "用户偏好简洁的代码示例",
    "fact_type": "preference",
    "validity_score": 0.8
  }
]"""
        
        # 构建上下文
        context_str = ""
        if conversation_context:
            context_lines = []
            for msg in conversation_context[-3:]:  # 只取最近3轮
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:100]  # 截断
                context_lines.append(f"{role}: {content}")
            context_str = "\n".join(context_lines)
        
        prompt = f"""对话历史：
{context_str}

当前对话：
用户: {user_message}
助手: {assistant_message}

请提取值得记忆的事实（JSON格式）："""
        
        try:
            # 使用轻量级模型提取
            response = await self.ollama.generate_completion(
                prompt=prompt,
                model=self.extraction_model,
                temperature=0.3,  # 低温度保证稳定性
                max_tokens=500,
                system=system_prompt,
                format="json"  # 要求JSON输出
            )
            
            content = response.get("choices", [{}])[0].get("text", "").strip()
            
            if not content:
                logger.debug("No facts extracted from conversation")
                return []
            
            # 解析JSON
            try:
                facts = json.loads(content)
                
                # 如果返回的是单个字典，转换为列表
                if isinstance(facts, dict):
                    logger.debug("LLM returned single fact as dict, converting to list")
                    facts = [facts]
                elif not isinstance(facts, list):
                    logger.warning(f"Invalid facts format: {type(facts)}")
                    return []
                
                # 验证和过滤事实
                valid_facts = []
                for fact in facts:
                    if self._validate_fact(fact):
                        valid_facts.append(fact)
                
                logger.info(f"Extracted {len(valid_facts)} valid facts")
                return valid_facts
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse facts JSON: {e}")
                logger.debug(f"Raw content: {content}")
                return []
            
        except Exception as e:
            logger.error(f"Failed to extract facts: {e}")
            return []
    
    def _validate_fact(self, fact: Dict[str, Any]) -> bool:
        """
        验证事实的有效性
        
        Args:
            fact: 事实字典
            
        Returns:
            是否有效
        """
        # 检查必需字段
        if not isinstance(fact, dict):
            return False
        
        if "fact_content" not in fact or not fact["fact_content"]:
            return False
        
        if "fact_type" not in fact:
            fact["fact_type"] = "general"
        
        # 验证事实类型
        if fact["fact_type"] not in self.FACT_TYPES:
            logger.warning(f"Unknown fact type: {fact['fact_type']}, using 'general'")
            fact["fact_type"] = "general"
        
        # 验证有效性分数
        if "validity_score" not in fact:
            fact["validity_score"] = 0.8
        else:
            try:
                score = float(fact["validity_score"])
                if score < 0.0 or score > 1.0:
                    fact["validity_score"] = 0.8
            except (ValueError, TypeError):
                fact["validity_score"] = 0.8
        
        # 检查内容长度
        content = fact["fact_content"]
        if len(content) < 5 or len(content) > 500:
            logger.warning(f"Fact content length invalid: {len(content)}")
            return False
        
        return True
    
    async def process_conversation(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        message_id: Optional[int] = None
    ) -> int:
        """
        处理对话并提取记忆
        
        Args:
            session_id: 会话ID
            user_message: 用户消息
            assistant_message: 助手回复
            message_id: 消息ID
            
        Returns:
            提取的事实数量
        """
        try:
            # 1. 获取用户ID
            user_id = await self.memory_dao.get_session_user_id(session_id)
            if not user_id:
                logger.error(f"Cannot find user_id for session {session_id}")
                return 0
            
            # 2. 提取事实
            facts = await self.extract_facts_from_conversation(
                user_message=user_message,
                assistant_message=assistant_message
            )
            
            if not facts:
                logger.debug("No facts to store")
                # 标记消息已处理
                if message_id:
                    await self.memory_dao.mark_message_processed(message_id)
                return 0
            
            # 3. 存储事实
            stored_count = 0
            for fact in facts:
                memory_id = await self.memory_manager.add_memory(
                    user_id=user_id,
                    fact_content=fact["fact_content"],
                    fact_type=fact["fact_type"],
                    source_session_id=session_id,
                    source_message_id=message_id,
                    validity_score=fact["validity_score"]
                )
                
                if memory_id:
                    stored_count += 1
                    logger.debug(f"Stored fact: {fact['fact_content'][:50]}...")
            
            # 4. 标记消息已处理
            if message_id:
                await self.memory_dao.mark_message_processed(message_id)
            
            logger.info(f"Processed conversation: stored {stored_count}/{len(facts)} facts")
            return stored_count
            
        except Exception as e:
            logger.error(f"Failed to process conversation: {e}")
            return 0
    
    async def batch_process_unprocessed_messages(
        self,
        session_id: str,
        max_messages: int = 10
    ) -> int:
        """
        批量处理未处理的消息
        
        Args:
            session_id: 会话ID
            max_messages: 最大处理数量
            
        Returns:
            处理的消息数量
        """
        try:
            # 获取未处理的消息
            messages = await self.memory_dao.get_unprocessed_messages(
                session_id=session_id,
                limit=max_messages
            )
            
            if not messages:
                logger.debug("No unprocessed messages")
                return 0
            
            # 配对用户和助手消息
            processed = 0
            i = 0
            while i < len(messages) - 1:
                msg1 = messages[i]
                msg2 = messages[i + 1]
                
                # 检查是否为用户-助手配对
                if msg1['role'] == 'user' and msg2['role'] == 'assistant':
                    await self.process_conversation(
                        session_id=session_id,
                        user_message=msg1['content'],
                        assistant_message=msg2['content'],
                        message_id=msg2['id']
                    )
                    processed += 2
                    i += 2
                else:
                    # 标记为已处理但不提取
                    await self.memory_dao.mark_message_processed(msg1['id'])
                    processed += 1
                    i += 1
            
            logger.info(f"Batch processed {processed} messages")
            return processed
            
        except Exception as e:
            logger.error(f"Failed to batch process messages: {e}")
            return 0
