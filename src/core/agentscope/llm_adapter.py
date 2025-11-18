#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgentScope LLM适配器
用于将现有的BaseLLM实现适配到AgentScope框架
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from agentscope.message import Msg
from agentscope.model._model_base import ChatModelBase
from agentscope.model._model_response import ChatResponse

# 导入现有的LLM基类
from src.core.llm.base_llm import BaseLLM


class AgentScopeLLMAdapter(ChatModelBase):
    """
    AgentScope LLM适配器
    将现有的BaseLLM实现包装为AgentScope兼容的接口
    """

    def __init__(
        self,
        base_llm: BaseLLM,
        model_name: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ):
        """
        初始化适配器

        Args:
            base_llm: 现有的BaseLLM实例
            model_name: 模型名称，如果为None则从base_llm获取
            stream: 是否使用流式输出
            **kwargs: 其他参数
        """
        # Initialize ChatModelBase with model_name and stream
        super().__init__(
            model_name=model_name or getattr(base_llm, 'model_name', 'unknown'),
            stream=stream,
            **kwargs
        )
        self.base_llm = base_llm

    async def __call__(
        self,
        messages: Union[Msg, List[Msg]],
        stream: bool = False,
        **kwargs
    ) -> Union[ChatResponse, Any]:
        """
        调用LLM生成响应

        Args:
            messages: 输入消息列表
            stream: 是否使用流式输出
            **kwargs: 其他参数

        Returns:
            模型响应
        """
        # 转换消息格式
        if isinstance(messages, Msg):
            messages = [messages]

        # 转换为BaseLLM格式
        chat_messages = self._convert_messages_to_base_format(messages)

        # 调用底层LLM
        if stream:
            return self._stream_response(chat_messages, **kwargs)
        else:
            return await self._generate_response(chat_messages, **kwargs)

    def _convert_messages_to_base_format(self, messages: List[Union[Msg, Dict]]) -> List[Dict[str, str]]:
        """
        将AgentScope消息转换为BaseLLM格式

        Args:
            messages: AgentScope消息列表（可以是 Msg 对象或字典）

        Returns:
            BaseLLM格式的消息列表
        """
        chat_messages = []
        for msg in messages:
            # 处理字典格式
            if isinstance(msg, dict):
                chat_messages.append({
                    "role": msg.get("role", "user"),
                    "content": str(msg.get("content", ""))
                })
            # 处理 Msg 对象
            else:
                chat_messages.append({
                    "role": msg.role,
                    "content": msg.content if isinstance(msg.content, str) else str(msg.content)
                })
        return chat_messages

    async def _generate_response(self, messages: List[Dict[str, str]], **kwargs) -> ChatResponse:
        """
        生成非流式响应

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            AgentScope模型响应
        """
        try:
            # 获取模型名称
            model = kwargs.pop('model', None) or self.model_name
            
            # 调用底层LLM
            response = await self.base_llm.chat_completion(
                messages=messages,
                model=model,
                **kwargs
            )

            # 解析响应 - 支持不同的响应格式
            from agentscope.message import TextBlock, ToolUseBlock
            
            content_blocks = []
            
            if isinstance(response, dict) and 'choices' in response:
                # OpenAI 格式
                message = response.get('choices', [{}])[0].get('message', {})
                
                # 处理文本内容
                text_content = message.get('content', '')
                if text_content:
                    text_block = TextBlock(text=text_content)
                    text_block["type"] = "text"
                    content_blocks.append(text_block)
                
                # 处理工具调用
                tool_calls = message.get('tool_calls', [])
                if tool_calls:
                    for tool_call in tool_calls:
                        func = tool_call.get('function', {})
                        tool_name = func.get('name', '')
                        tool_args = func.get('arguments', '{}')
                        
                        tool_block = ToolUseBlock(
                            id=tool_call.get('id', ''),
                            name=tool_name,
                            input=json.loads(tool_args)
                        )
                        tool_block["type"] = "tool_use"
                        content_blocks.append(tool_block)
            
            elif isinstance(response, dict) and 'content' in response:
                # 简单格式
                text_block = TextBlock(text=response.get('content', ''))
                text_block["type"] = "text"
                content_blocks.append(text_block)
            else:
                # 其他格式
                text_block = TextBlock(text=str(response))
                text_block["type"] = "text"
                content_blocks.append(text_block)
            
            # 如果没有任何内容块，添加一个空的文本块
            if not content_blocks:
                text_block = TextBlock(text="")
                text_block["type"] = "text"
                content_blocks.append(text_block)

            # Return ChatResponse compatible object
            return ChatResponse(
                content=content_blocks,
                metadata={"raw": response if isinstance(response, dict) else {'content': str(response)}}
            )

        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")

    async def _stream_response(self, messages: List[Dict[str, str]], **kwargs):
        """
        生成流式响应

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Yields:
            流式响应片段
        """
        try:
            # 获取模型名称
            model = kwargs.pop('model', None) or self.model_name
            
            # 调用底层LLM流式接口
            async for chunk in self.base_llm.chat_completion_stream(
                messages=messages,
                model=model,
                **kwargs
            ):
                # 支持不同的响应格式
                if isinstance(chunk, dict):
                    # OpenAI格式
                    if 'choices' in chunk:
                        content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                    # 简单格式
                    elif 'content' in chunk:
                        content = chunk.get('content', '')
                    else:
                        content = str(chunk)
                else:
                    content = str(chunk)
                    
                if content:
                    from agentscope.message import TextBlock
                    text_block = TextBlock(text=content)
                    text_block["type"] = "text"  # 添加 type 字段
                    yield ChatResponse(
                        content=[text_block],
                        metadata={"raw": chunk if isinstance(chunk, dict) else {'content': content}}
                    )

        except Exception as e:
            raise Exception(f"流式LLM调用失败: {str(e)}")


# AgentScopeModelResponse is replaced by ChatResponse from agentscope


class DualLLMManager:
    """
    双LLM管理器
    用于管理主LLM（DeepSeek）和多模态LLM（gemma3:4b）
    """

    def __init__(
        self,
        primary_llm: BaseLLM,        # DeepSeek-chat
        multimodal_llm: BaseLLM,     # gemma3:4b
        primary_model_name: str = "deepseek-chat",
        multimodal_model_name: str = "gemma3:4b"
    ):
        """
        初始化双LLM管理器

        Args:
            primary_llm: 主要的文本生成LLM
            multimodal_llm: 多模态LLM（用于图像处理）
            primary_model_name: 主模型名称
            multimodal_model_name: 多模态模型名称
        """
        self.primary_adapter = AgentScopeLLMAdapter(
            primary_llm,
            model_name=primary_model_name
        )

        self.multimodal_adapter = AgentScopeLLMAdapter(
            multimodal_llm,
            model_name=multimodal_model_name
        )
        
        # ReActAgent 需要的属性
        self.stream = False  # 默认不使用流式输出
        self.model_name = primary_model_name

    def get_primary_llm(self) -> AgentScopeLLMAdapter:
        """获取主LLM适配器"""
        return self.primary_adapter

    def get_multimodal_llm(self) -> AgentScopeLLMAdapter:
        """获取多模态LLM适配器"""
        return self.multimodal_adapter

    def is_multimodal_request(self, messages: List[Union[Msg, Dict]]) -> bool:
        """
        检查是否为多模态请求（包含图像）

        Args:
            messages: 消息列表（可以是 Msg 对象或字典）

        Returns:
            是否为多模态请求
        """
        for msg in messages:
            # 处理字典格式的消息
            if isinstance(msg, dict):
                content = msg.get('content', '')
            # 处理 Msg 对象
            elif hasattr(msg, 'content'):
                content = msg.content
            else:
                continue
            
            if isinstance(content, list):
                for block in content:
                    if hasattr(block, 'type') and block.type in ['image', 'video']:
                        return True
            elif isinstance(content, str):
                # 检查是否包含图像URL或base64
                if any(keyword in content.lower() for keyword in ['image:', 'img:', '![', '.jpg', '.png', '.gif']):
                    return True
        return False

    async def __call__(
        self,
        messages: Union[Msg, List[Msg]],
        **kwargs
    ) -> ChatResponse:
        """
        智能路由到合适的LLM

        Args:
            messages: 输入消息
            **kwargs: 其他参数

        Returns:
            模型响应
        """
        if isinstance(messages, Msg):
            messages = [messages]

        # 根据请求类型选择LLM
        if self.is_multimodal_request(messages):
            return await self.multimodal_adapter(messages, **kwargs)
        else:
            return await self.primary_adapter(messages, **kwargs)


def create_llm_manager(
    primary_llm: BaseLLM,
    multimodal_llm: BaseLLM,
    primary_model_name: str = "deepseek-chat",
    multimodal_model_name: str = "gemma3:4b"
) -> DualLLMManager:
    """
    创建LLM管理器的工厂函数

    Args:
        primary_llm: 主LLM实例
        multimodal_llm: 多模态LLM实例
        primary_model_name: 主模型名称
        multimodal_model_name: 多模态模型名称

    Returns:
        DualLLMManager实例
    """
    return DualLLMManager(
        primary_llm=primary_llm,
        multimodal_llm=multimodal_llm,
        primary_model_name=primary_model_name,
        multimodal_model_name=multimodal_model_name
    )