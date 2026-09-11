#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联网搜索服务
实现：用户问题 → LLM生成搜索问题 → 网络搜索 → LLM整合答案
"""

import logging
import json
from typing import Dict, Any, List
from backend.core.llm.factory import LLMFactory
from backend.core.llm.base_llm import APIError
from backend.core.agentscope.tools.web_search_tool import WebSearchTool

logger = logging.getLogger(__name__)


class WebSearchService:
    """联网搜索服务"""
    
    GENERATE_QUERIES_PROMPT = '为以下问题生成 3 到 5 个互补的搜索查询，仅返回 JSON 对象 {{"queries": ["查询"]}}：{user_question}'

    # 整合答案的提示词模板
    SYNTHESIZE_ANSWER_PROMPT = """你是一个专业的信息整合助手。

用户问题：{user_question}

搜索结果：
{search_results}

请基于以上搜索结果，回答用户的问题。要求：
1. 答案要准确、全面、有条理
2. 引用搜索结果中的关键信息
3. 如果信息不足或有矛盾，请说明
4. 使用清晰的结构（如分点、分段）
5. 保持客观中立的态度

请提供详细的回答："""

    def __init__(self):
        """初始化联网搜索服务"""
        self._llms = {}
        
    def _get_llm(self, provider: str, model_name: str):
        """获取LLM实例"""
        key = (provider, model_name)
        if key not in self._llms:
            self._llms[key] = LLMFactory.create_llm(provider=provider, model=model_name)
        return self._llms[key]
    
    def _init_web_search_tool(self, api_key: str):
        """初始化网络搜索工具"""
        # Each request owns its credential-specific client, closed after searching.
        return WebSearchTool(api_key)

    async def generate_search_queries(
        self,
        user_question: str,
        llm_provider: str = "zhipu",
        model_name: str = "glm-4.5-flash"
    ) -> List[str]:
        """
        使用LLM生成搜索查询
        
        Args:
            user_question: 用户问题
            llm_provider: LLM提供商
            model_name: 模型名称
            
        Returns:
            搜索查询列表
        """
        try:
            llm = self._get_llm(llm_provider, model_name)
            
            # 构建提示词
            prompt = self.GENERATE_QUERIES_PROMPT.format(user_question=user_question)
            
            # 调用LLM生成查询
            response = await llm.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=model_name,
                temperature=0.7,
                stream=False
            )
            
            # 提取内容
            content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # 解析JSON
            try:
                # 尝试提取JSON部分
                if '```json' in content:
                    json_str = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    json_str = content.split('```')[1].split('```')[0].strip()
                else:
                    json_str = content.strip()
                
                data = json.loads(json_str)
                queries = data.get('queries', [])
                if not isinstance(queries, list) or any(not isinstance(q, str) for q in queries):
                    raise ValueError('Invalid generated queries')
                queries = list(dict.fromkeys(q.strip() for q in queries if q.strip()))
                
                # 确保至少有5个查询
                if len(queries) < 5:
                    logger.warning(f"生成的查询数量不足: {len(queries)}")
                    # 添加用户原始问题作为备用
                    queries.append(user_question)
                
                return queries[:10]  # 最多10个
                
            except (json.JSONDecodeError, ValueError, AttributeError) as e:
                logger.error(f"解析JSON失败: {e}, 内容: {content}")
                # 降级方案：使用用户原始问题
                return [user_question]
                
        except Exception as e:
            logger.error(f"生成搜索查询失败: {e}")
            # 降级方案：使用用户原始问题
            return [user_question]
    
    async def perform_web_searches(
        self,
        queries: List[str],
        api_key: str,
        max_results_per_query: int = 3
    ) -> str:
        """
        执行网络搜索
        
        Args:
            queries: 搜索查询列表
            api_key: API密钥
            max_results_per_query: 每个查询的最大结果数
            
        Returns:
            格式化的搜索结果字符串
        """
        web_tool = self._init_web_search_tool(api_key)
        try:
            all_results = []
            for i, query in enumerate(queries, 1):
                result = await web_tool.web_search(query=query, max_results=max_results_per_query)
                all_results.append(f"## 搜索 {i}: {query}\n\n{result.content[0]['text']}")
            return "\n\n".join(all_results)
        finally:
            await web_tool.close()

    async def synthesize_answer(
        self,
        user_question: str,
        search_results: str,
        llm_provider: str = "zhipu",
        model_name: str = "glm-4.5-flash"
    ) -> str:
        """
        整合搜索结果生成答案
        
        Args:
            user_question: 用户问题
            search_results: 搜索结果
            llm_provider: LLM提供商
            model_name: 模型名称
            
        Returns:
            整合后的答案
        """
        try:
            llm = self._get_llm(llm_provider, model_name)
            
            # 构建提示词
            prompt = self.SYNTHESIZE_ANSWER_PROMPT.format(
                user_question=user_question,
                search_results=search_results
            )
            
            # 调用LLM生成答案
            response = await llm.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=model_name,
                temperature=0.7,
                stream=False
            )
            
            # 提取内容
            content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
            if not isinstance(content, str) or not content.strip():
                raise APIError('Answer synthesis returned no content')
            return content
            
        except Exception as e:
            logger.error(f"整合答案失败: {e}")
            raise
    
    async def web_search_chat(
        self,
        user_question: str,
        llm_provider: str = "zhipu",
        model_name: str = "glm-4.5-flash",
        api_key: str = None
    ) -> Dict[str, Any]:
        """
        完整的联网搜索对话流程（简化版）
        
        流程：
        1. 直接用用户问题搜索网络
        2. 将搜索结果 + 用户问题发送给 LLM
        
        Args:
            user_question: 用户问题
            llm_provider: LLM提供商
            model_name: 模型名称
            api_key: API密钥
            
        Returns:
            包含答案和搜索结果的字典
        """
        try:
            # 步骤1: 直接用用户问题执行网络搜索
            logger.info(f"步骤1: 执行网络搜索 - 用户问题: {user_question}")
            web_tool = self._init_web_search_tool(api_key or "")
            
            try:
                result = await web_tool.web_search(
                    query=user_question, max_results=10, search_recency_filter="oneMonth"
                )
            finally:
                await web_tool.close()
            
            # 提取搜索结果
            if result and hasattr(result, 'content') and result.content:
                search_results = result.content[0]['text']
            else:
                search_results = "未找到相关搜索结果"
            
            logger.info(f"搜索完成，结果长度: {len(search_results)}")
            
            # 步骤2: 将搜索结果和用户问题发送给 LLM
            logger.info("步骤2: LLM 整合答案")
            final_answer = await self.synthesize_answer(
                user_question=user_question,
                search_results=search_results,
                llm_provider=llm_provider,
                model_name=model_name
            )
            logger.info("答案整合完成")
            
            return {
                "success": True,
                "answer": final_answer,
                "search_results": search_results
            }
            
        except Exception as e:
            logger.error(f"联网搜索对话失败: {e}", exc_info=True)
            raise
