#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话服务
处理对话会话和消息的业务逻辑
"""

import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
import json

from src.dao.chat_dao import ChatDAO
from src.schemas.chat import (
    ChatSessionCreate, ChatSessionUpdate, ChatRequest,
    ModelInfo, ModelListResponse
)
from src.core.llm.base_llm import BaseLLM
from src.core.llm.deepseek_llm import DeepSeekLLM
from src.core.llm.zhipu_llm import ZhipuLLM
from src.services.web_search_service import WebSearchService
from src.core.memory.memory_manager import Mem0MemoryManager
from src.core.memory.memory_agent import MemoryAgent

logger = logging.getLogger(__name__)


class ChatService:
    """对话服务"""
    
    # 可用的LLM提供商（仅云端API）
    LLM_PROVIDERS = {
        "deepseek": DeepSeekLLM,
        "zhipu": ZhipuLLM
    }
    
    # 模型配置（仅云端API）
    MODEL_CONFIGS = {
        "deepseek": {
            "deepseek-chat": {
                "display_name": "DeepSeek Chat",
                "description": "DeepSeek对话模型，支持推理和非推理模式",
                "context_length": 128000,
                "capabilities": ["chat", "function_calling", "json_mode"]
            },
            "deepseek-reasoner": {
                "display_name": "DeepSeek Reasoner",
                "description": "DeepSeek推理模型，专注于复杂推理任务",
                "context_length": 128000,
                "capabilities": ["chat", "reasoning", "json_mode"]
            }
        },
        "zhipu": {
            "glm-4.5-air": {
                "display_name": "GLM-4.5-Air",
                "description": "智谱AI快速模型",
                "context_length": 128000,
                "capabilities": ["chat", "function_calling", "web_search"]
            },
            "glm-4.6": {
                "display_name": "GLM-4.6",
                "description": "智谱AI最新模型",
                "context_length": 2000000,
                "capabilities": ["chat", "function_calling"]
            }
        }
    }
    
    def __init__(self):
        self.chat_dao = ChatDAO()
        self._llm_instances: Dict[str, BaseLLM] = {}
        self.web_search_service = WebSearchService()
        
        # 初始化记忆系统
        try:
            self.memory_manager = Mem0MemoryManager()
            self.memory_agent = MemoryAgent()
            self.memory_enabled = True
            logger.info("Memory system initialized successfully")
        except Exception as e:
            logger.warning(f"Memory system initialization failed: {e}. Running without memory.")
            self.memory_manager = None
            self.memory_agent = None
            self.memory_enabled = False
    
    def _get_llm_instance(self, provider: str, model_name: str) -> BaseLLM:
        """获取LLM实例"""
        key = f"{provider}:{model_name}"
        
        if key not in self._llm_instances:
            llm_class = self.LLM_PROVIDERS.get(provider)
            if not llm_class:
                raise ValueError(f"不支持的LLM提供商: {provider}")
            
            self._llm_instances[key] = llm_class(model_name=model_name)
        
        return self._llm_instances[key]
    
    async def create_session(
        self,
        user_id: str,
        session_data: ChatSessionCreate
    ) -> Optional[Dict[str, Any]]:
        """创建对话会话"""
        return await self.chat_dao.create_session(
            user_id=user_id,
            title=session_data.title,
            llm_provider=session_data.llm_provider,
            model_name=session_data.model_name,
            system_prompt=session_data.system_prompt
        )
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取对话会话"""
        return await self.chat_dao.get_session(session_id)
    
    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取用户的对话会话列表"""
        return await self.chat_dao.get_user_sessions(user_id, limit, offset)
    
    async def update_session(
        self,
        session_id: str,
        update_data: ChatSessionUpdate
    ) -> bool:
        """更新对话会话"""
        return await self.chat_dao.update_session(
            session_id=session_id,
            title=update_data.title,
            llm_provider=update_data.llm_provider,
            model_name=update_data.model_name,
            system_prompt=update_data.system_prompt,
            status=update_data.status
        )
    
    async def delete_session(self, session_id: str) -> bool:
        """删除对话会话"""
        return await self.chat_dao.delete_session(session_id)
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取会话消息"""
        return await self.chat_dao.get_session_messages(session_id, limit)
    
    async def chat(
        self,
        chat_request: ChatRequest,
        background_tasks: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        处理对话请求（非流式）
        
        Args:
            chat_request: 对话请求
            background_tasks: FastAPI后台任务（用于异步记忆提取）
            
        Returns:
            对话响应
        """
        # 获取会话信息
        session = await self.chat_dao.get_session(chat_request.session_id)
        if not session:
            raise ValueError("会话不存在")
        
        # 保存用户消息
        user_msg_result = await self.chat_dao.add_message(
            session_id=chat_request.session_id,
            role="user",
            content=chat_request.message
        )
        
        # === Mem0 记忆增强：检索相关记忆 ===
        relevant_memories = []
        if self.memory_enabled and self.memory_manager:
            try:
                relevant_memories = await self.memory_manager.retrieve_memories(
                    query=chat_request.message,
                    user_id=session['user_id'],
                    top_k=5,
                    use_hyde=True
                )
                logger.debug(f"Retrieved {len(relevant_memories)} relevant memories")
            except Exception as e:
                logger.error(f"Failed to retrieve memories: {e}")
        
        # 获取历史消息
        history_messages = await self.chat_dao.get_recent_messages(
            chat_request.session_id,
            count=20
        )
        
        # 构建消息列表
        messages = []
        
        # 系统提示词 + 记忆注入
        system_content = session.get('system_prompt', '')
        if relevant_memories:
            memory_context = "\n\n## 用户背景信息（请在回答时参考）：\n"
            for mem in relevant_memories:
                memory_context += f"- {mem['content']}\n"
            system_content = system_content + memory_context if system_content else memory_context.strip()
        
        if system_content:
            messages.append({
                "role": "system",
                "content": system_content
            })
        
        for msg in history_messages:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        # 调用LLM
        llm = self._get_llm_instance(
            session['llm_provider'],
            session['model_name']
        )
        
        response = await llm.chat_completion(
            messages=messages,
            model=session['model_name'],
            stream=False
        )
        
        # 提取内容
        content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        # 保存助手回复
        assistant_msg_result = await self.chat_dao.add_message(
            session_id=chat_request.session_id,
            role="assistant",
            content=content,
            model_name=session['model_name'],
            tokens_used=response.get('usage', {}).get('total_tokens')
        )
        
        # === Mem0 记忆提取：后台异步处理 ===
        if self.memory_enabled and self.memory_agent and background_tasks:
            try:
                background_tasks.add_task(
                    self.memory_agent.process_conversation,
                    session_id=chat_request.session_id,
                    user_message=chat_request.message,
                    assistant_message=content,
                    message_id=assistant_msg_result
                )
                logger.debug("Scheduled memory extraction task")
            except Exception as e:
                logger.error(f"Failed to schedule memory extraction: {e}")
        
        return {
            "session_id": chat_request.session_id,
            "message": {
                "role": "assistant",
                "content": content,
                "model_name": session['model_name']
            },
            "usage": response.get('usage'),
            "memories_used": len(relevant_memories) if relevant_memories else 0
        }
    
    async def chat_stream(
        self,
        chat_request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """
        处理对话请求（流式）
        
        Args:
            chat_request: 对话请求
            
        Yields:
            流式响应数据
        """
        # 获取会话信息
        session = await self.chat_dao.get_session(chat_request.session_id)
        if not session:
            raise ValueError("会话不存在")
        
        # 保存用户消息
        await self.chat_dao.add_message(
            session_id=chat_request.session_id,
            role="user",
            content=chat_request.message
        )
        
        # 获取历史消息
        history_messages = await self.chat_dao.get_recent_messages(
            chat_request.session_id,
            count=20
        )
        
        # 构建消息列表
        messages = []
        if session.get('system_prompt'):
            messages.append({
                "role": "system",
                "content": session['system_prompt']
            })
        
        for msg in history_messages:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        # 调用LLM流式接口
        llm = self._get_llm_instance(
            session['llm_provider'],
            session['model_name']
        )
        
        full_content = ""
        async for chunk in llm.chat_completion_stream(
            messages=messages,
            model=session['model_name'],
            temperature=1.0
        ):
            full_content += chunk
            # 构造SSE格式的响应
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        
        # 保存完整的助手回复
        await self.chat_dao.add_message(
            session_id=chat_request.session_id,
            role="assistant",
            content=full_content,
            model_name=session['model_name']
        )
    
    def get_available_models(self) -> ModelListResponse:
        """获取可用的模型列表"""
        models = []
        
        for provider, provider_models in self.MODEL_CONFIGS.items():
            for model_name, config in provider_models.items():
                models.append(ModelInfo(
                    provider=provider,
                    model_name=model_name,
                    display_name=config['display_name'],
                    description=config.get('description'),
                    context_length=config.get('context_length'),
                    capabilities=config.get('capabilities', []),
                    is_available=True
                ))
        
        return ModelListResponse(
            models=models,
            default_provider="deepseek",
            default_model="deepseek-chat"
        )
    
    async def clear_session_messages(self, session_id: str) -> bool:
        """清空会话消息"""
        return await self.chat_dao.clear_session_messages(session_id)

    async def web_search_chat(
        self,
        chat_request: ChatRequest,
        api_key: str = None
    ) -> Dict[str, Any]:
        """
        处理联网搜索对话请求
        
        Args:
            chat_request: 对话请求
            api_key: API密钥（用于网络搜索）
            
        Returns:
            对话响应
        """
        # 获取会话信息
        session = await self.chat_dao.get_session(chat_request.session_id)
        if not session:
            raise ValueError("会话不存在")
        
        # 保存用户消息
        await self.chat_dao.add_message(
            session_id=chat_request.session_id,
            role="user",
            content=chat_request.message
        )
        
        # 执行联网搜索
        result = await self.web_search_service.web_search_chat(
            user_question=chat_request.message,
            llm_provider=session['llm_provider'],
            model_name=session['model_name'],
            api_key=api_key
        )
        
        if not result['success']:
            error_msg = f"联网搜索失败: {result.get('error', '未知错误')}"
            # 保存错误消息
            await self.chat_dao.add_message(
                session_id=chat_request.session_id,
                role="assistant",
                content=error_msg,
                model_name=session['model_name']
            )
            return {
                "session_id": chat_request.session_id,
                "message": {
                    "role": "assistant",
                    "content": error_msg,
                    "model_name": session['model_name']
                }
            }
        
        # 保存助手回复
        await self.chat_dao.add_message(
            session_id=chat_request.session_id,
            role="assistant",
            content=result['answer'],
            model_name=session['model_name']
        )
        
        return {
            "session_id": chat_request.session_id,
            "message": {
                "role": "assistant",
                "content": result['answer'],
                "model_name": session['model_name']
            },
            "search_results_summary": "已执行网络搜索"
        }
