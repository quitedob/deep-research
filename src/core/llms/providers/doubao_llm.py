# -*- coding: utf-8 -*-
"""
Doubao (豆包) LLM Provider
支持联网搜索、视觉理解等功能
"""
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from volcenginesdkarkruntime import Ark

logger = logging.getLogger(__name__)


@dataclass
class _Resp:
    """响应数据类"""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    references: Optional[List[Dict[str, Any]]] = None


class DoubaoProvider:
    """Doubao Provider（火山方舟 API）"""
    
    def __init__(self, model_name: str, api_key: str, base_url: str):
        """
        初始化 Doubao Provider
        
        Args:
            model_name: 模型名称
            api_key: API Key
            base_url: API 基础 URL
        """
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.client = Ark(api_key=api_key, base_url=base_url)
    
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> _Resp:
        """
        生成文本
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            **kwargs: 其他参数
        
        Returns:
            响应对象
        """
        try:
            # 转换消息格式为 Doubao 格式
            formatted_messages = self._format_messages(messages)
            
            # 调用 API
            response = self.client.responses.create(
                model=self.model_name,
                input=formatted_messages,
                stream=False,
                thinking={"type": "disabled"}
            )
            
            # 提取回答内容
            content = ""
            if hasattr(response, 'output') and response.output:
                for output_item in response.output:
                    if hasattr(output_item, 'content') and output_item.content:
                        for content_item in output_item.content:
                            if hasattr(content_item, 'text'):
                                content += content_item.text
            
            # 提取使用信息
            usage = None
            if hasattr(response, 'usage'):
                usage = {
                    "prompt_tokens": getattr(response.usage, 'input_tokens', 0),
                    "completion_tokens": getattr(response.usage, 'output_tokens', 0),
                    "total_tokens": getattr(response.usage, 'total_tokens', 0)
                }
            
            return _Resp(
                content=content,
                model=self.model_name,
                usage=usage
            )
        
        except Exception as e:
            logger.error(f"Doubao generate 失败: {e}")
            raise
    
    async def generate_with_search(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        search_limit: int = 10,
        sources: Optional[List[str]] = None
    ) -> _Resp:
        """
        生成文本（带联网搜索）
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            search_limit: 搜索结果数量限制
            sources: 搜索源列表
        
        Returns:
            响应对象（包含搜索结果）
        """
        try:
            # 转换消息格式
            formatted_messages = self._format_messages(messages)
            
            # 默认搜索源
            if not sources:
                sources = ["toutiao", "douyin", "zhihu", "baidu"]
            
            # 调用 API（带搜索工具）
            response = self.client.responses.create(
                model=self.model_name,
                input=formatted_messages,
                tools=[
                    {
                        "type": "web_search",
                        "limit": search_limit,
                        "sources": sources
                    }
                ],
                stream=False,
                extra_body={"thinking": {"type": "auto"}}
            )
            
            # 提取回答内容
            content = ""
            if hasattr(response, 'output') and response.output:
                for output_item in response.output:
                    if hasattr(output_item, 'content') and output_item.content:
                        for content_item in output_item.content:
                            if hasattr(content_item, 'text'):
                                content += content_item.text
            
            # 提取搜索结果
            references = []
            if hasattr(response, 'references') and response.references:
                for ref in response.references:
                    if hasattr(ref, 'url') and hasattr(ref, 'title'):
                        references.append({
                            "title": ref.title,
                            "url": ref.url,
                            "snippet": getattr(ref, 'content', '')[:200] + "..." if hasattr(ref, 'content') else ""
                        })
            
            # 提取使用信息
            usage = None
            if hasattr(response, 'usage'):
                usage = {
                    "prompt_tokens": getattr(response.usage, 'input_tokens', 0),
                    "completion_tokens": getattr(response.usage, 'output_tokens', 0),
                    "total_tokens": getattr(response.usage, 'total_tokens', 0)
                }
            
            return _Resp(
                content=content,
                model=self.model_name,
                usage=usage,
                references=references
            )
        
        except Exception as e:
            logger.error(f"Doubao generate_with_search 失败: {e}")
            raise
    
    async def health_check(self) -> tuple[bool, str]:
        """
        健康检查
        
        Returns:
            (是否健康, 消息)
        """
        try:
            # 发送简单测试请求
            response = self.client.responses.create(
                model=self.model_name,
                input=[{
                    "role": "user",
                    "content": [{"type": "input_text", "text": "你好"}]
                }],
                thinking={"type": "disabled"}
            )
            
            return True, "ok"
        
        except Exception as e:
            return False, str(e)
    
    def _format_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        转换消息格式为 Doubao 格式
        
        Args:
            messages: 标准消息列表
        
        Returns:
            Doubao 格式的消息列表
        """
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            formatted.append({
                "role": role,
                "content": [{"type": "input_text", "text": content}]
            })
        
        return formatted
