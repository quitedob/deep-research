#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgentScope深度研究代理
基于ReActAgent的多模态研究智能体
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.tool import Toolkit
from agentscope.memory import InMemoryMemory
from agentscope.formatter import OpenAIChatFormatter, OllamaChatFormatter

# 导入自定义组件
from backend.core.agentscope.llm_adapter import DualLLMManager
from backend.core.agentscope.memory.research_memory import ResearchMemoryManager
from backend.core.agentscope.tools import (
    register_web_search_tools,
    register_wikipedia_tools,
    register_arxiv_tools,
    register_image_analysis_tools,
    register_synthesis_tools
)

# 导入数据访问对象
from backend.repositories.research_dao import ResearchDAO
from backend.core.llm.base_llm import BaseLLM


logger = logging.getLogger(__name__)


class DeepResearchAgent(ReActAgent):
    """
    深度研究智能体
    集成多种研究工具，支持多模态输入和智能推理
    """

    def __init__(
        self,
        session_id: str,
        llm_instance: 'BaseLLM',
        multimodal_llm_instance: Optional['BaseLLM'] = None,
        web_search_api_key: str = "",
        max_iterations: int = 15,  # 增加迭代次数以支持更完整的研究
        parallel_tool_calls: bool = True
    ):
        """
        初始化深度研究智能体

        Args:
            session_id: 研究会话ID
            llm_instance: 主LLM实例（通过LLM工厂创建，用于文本生成）
            multimodal_llm_instance: 多模态LLM实例（可选，用于图像分析）
            web_search_api_key: 网络搜索API密钥
            max_iterations: 最大推理迭代次数
            parallel_tool_calls: 是否启用并行工具调用
        """
        # 导入LLM抽象层
        from backend.core.llm.base_llm import BaseLLM
        from backend.core.llm.factory import LLMFactory
        
        # 准备所有需要的组件（使用局部变量，不设置实例属性）
        # 如果没有提供多模态LLM，使用主LLM
        if multimodal_llm_instance is None:
            multimodal_llm_instance = llm_instance
        
        # 获取模型名称（使用静态方法）
        primary_model_name = DeepResearchAgent._get_model_name_static(llm_instance)
        multimodal_model_name = DeepResearchAgent._get_model_name_static(multimodal_llm_instance)
        
        # 创建双LLM管理器
        llm_manager = DualLLMManager(
            primary_llm=llm_instance,
            multimodal_llm=multimodal_llm_instance,
            primary_model_name=primary_model_name,
            multimodal_model_name=multimodal_model_name
        )

        # 初始化数据访问对象
        research_dao = ResearchDAO()

        # 创建记忆管理器
        memory_manager = ResearchMemoryManager(research_dao)

        # 创建工具包
        toolkit = Toolkit()

        # 创建系统提示词（使用静态方法）
        system_prompt = DeepResearchAgent._create_system_prompt_static()

        # 创建一个临时的内存对象用于初始化
        # 实际的会话记忆将在异步方法中初始化
        temp_memory = InMemoryMemory()

        # 首先调用 super().__init__()（AgentScope 要求）
        super().__init__(
            name="DeepResearchAgent",
            sys_prompt=system_prompt,
            model=llm_manager,
            formatter=OllamaChatFormatter() if llm_instance.get_provider_name() == "ollama" else OpenAIChatFormatter(),
            toolkit=toolkit,
            memory=temp_memory,
            max_iters=max_iterations,
            parallel_tool_calls=parallel_tool_calls
        )

        # 现在可以安全地设置实例属性
        self.session_id = session_id
        self.web_search_api_key = web_search_api_key
        self.llm_instance = llm_instance
        self.research_dao = research_dao
        self.llm_manager = llm_manager
        self.memory_manager = memory_manager
        self.session_memory = None  # 将在 async_init 中初始化
        self.toolkit = toolkit
        self._memory_initialized = False

        # 研究状态跟踪
        self.research_phase = "planning"
        self.research_progress = 0.0
        self.current_tools_used = []
        self.findings_count = 0

        # 工具调用失败跟踪
        self.tool_failure_tracker = {}  # {tool_name: failure_count}
        self.max_tool_failures = 3      # 单个工具最多失败3次
        self.consecutive_failures = 0   # 连续失败计数
        self.max_consecutive_failures = 5  # 最多连续失败5次
        
        # 原地踏步检测
        self.recent_actions = []  # 记录最近的操作
        self.max_stagnation_check = 3  # 检查最近3次操作（降低阈值以更快检测循环）
        self.tool_call_history = {}  # {tool_name: {args_hash: call_count}} 跟踪相同参数的重复调用

        # 注册所有研究工具
        self._register_research_tools()

    async def async_init(self):
        """
        异步初始化方法，用于初始化需要异步操作的组件
        必须在使用代理之前调用
        """
        if not self._memory_initialized:
            # 创建会话记忆
            self.session_memory = await self.memory_manager.create_session(self.session_id)
            # 更新代理的记忆
            self.memory = self.session_memory.short_memory
            self._memory_initialized = True
    
    @staticmethod
    def _get_model_name_static(llm_instance: 'BaseLLM') -> str:
        """
        获取LLM实例的模型名称（静态方法）

        Args:
            llm_instance: LLM实例

        Returns:
            模型名称
        """
        # 尝试从配置中获取模型名称
        if getattr(llm_instance, 'model', None):
            return llm_instance.model
        elif hasattr(llm_instance, 'config') and 'model' in llm_instance.config:
            return llm_instance.config['model']
        else:
            # 从配置文件获取默认模型
            from backend.config.llm_config import get_config
            provider = llm_instance.get_provider_name()
            try:
                config = get_config()
                provider_config = config.get_provider_config(provider)
                return provider_config.default_model
            except:
                # 最后的备用方案
                default_models = {
                    'deepseek': 'deepseek-flash',
                    'ollama': 'gemma3:4b',
                    'zhipu': 'glm-4.6'
                }
                return default_models.get(provider, 'unknown')

    @staticmethod
    def _create_system_prompt_static() -> str:
        """
        创建系统提示词（静态方法）

        Returns:
            系统提示词字符串
        """
        return """你是一个专业的深度研究助手，具备强大的信息搜集、分析和综合能力。

## 核心能力
1. **多源信息搜集**: 可以同时使用网络搜索、维基百科、学术论文数据库等多种信息源
2. **智能内容分析**: 能够分析文本、图像等多种类型的内容
3. **综合推理**: 能够整合不同来源的信息，形成全面的研究报告
4. **多模态支持**: 支持文本和图像输入，能够分析图表、流程图等视觉内容

## 研究流程
1. **理解需求**: 仔细分析用户的研究需求和问题
2. **制定策略**: 根据需求制定合适的信息搜集策略
3. **并行搜集**: 同时使用多个工具搜集相关信息
4. **信息验证**: 验证信息的可靠性和相关性
5. **综合分析**: 整合所有信息，进行深入分析
6. **生成报告**: 提供结构化的研究报告

## 使用工具指南
- **web_search**: 搜索最新的网络信息和新闻（第一步）
- **search_wikipedia**: 查找维基百科中的基础知识（第二步）
- **search_arxiv_papers**: 搜索相关的学术论文（第三步，必须执行）
- **analyze_image**: 分析图像内容（如有图像）
- **synthesize_research_findings**: 综合研究发现（最后一步）

## 重要原则
- 始终确保信息的准确性和可靠性
- 综合多个来源的信息，避免单一来源偏见
- **避免重复调用相同的工具和参数** - 如果已经获取了某个页面的内容，不要再次请求
- **按顺序完成所有研究步骤** - 不要跳过ArXiv学术论文搜索
- 为用户提供结构化、易于理解的回答
- 在不确定时明确指出，避免猜测
- 保持客观中立的研究态度
- **当获取足够信息后，立即进入下一步** - 不要在同一个工具上停留太久

请开始你的研究工作，为用户提供高质量的研究服务。"""

    def _register_research_tools(self) -> None:
        """
        注册所有研究工具到工具包
        """
        # 注册网络搜索工具
        self._tool_resources = []
        if self.web_search_api_key:
            self._tool_resources.append(register_web_search_tools(self.toolkit, self.web_search_api_key))

        # 注册维基百科工具
        register_wikipedia_tools(self.toolkit)

        # 注册ArXiv学术论文工具
        register_arxiv_tools(self.toolkit)

        register_image_analysis_tools(
            self.toolkit, llm_instance=self.llm_manager.multimodal_adapter.base_llm,
            model=self.llm_manager.multimodal_adapter.model_name,
        )

        # 注册研究合成工具
        register_synthesis_tools(self.toolkit)
        
        # 包装所有工具以自动记录研究发现
        self._wrap_tools_with_finding_recorder()

    async def close(self):
        for resource in self._tool_resources:
            await resource.close()

    def _wrap_tools_with_finding_recorder(self) -> None:
        """
        包装所有工具函数，使其自动记录研究发现
        
        注意：不直接包装工具，而是通过重写 reply 方法来拦截工具调用结果
        这样可以避免破坏 AgentScope 的工具对象结构
        """
        # 保存原始的 reply 方法
        if not hasattr(self, '_original_reply'):
            self._original_reply = self.reply
            # 不需要包装工具，而是在 reply 方法中处理
            logger.info("工具发现记录器已启用（通过 reply 拦截）")
    
    async def reply(self, x=None):
        """
        重写 reply 方法以拦截工具调用结果
        """
        # 调用原始的 reply 方法
        result = await super().reply(x)
        
        # 如果会话记忆已初始化，尝试从结果中提取发现
        if self.session_memory and result:
            try:
                # 检查是否有工具调用记录
                if hasattr(self, 'memory') and self.memory:
                    # ✅ 修复：不传递 limit 参数，直接获取所有消息
                    recent_messages = await self.memory.get_memory()
                    
                    # 只查看最近5条消息
                    recent_messages = recent_messages[-5:] if len(recent_messages) > 5 else recent_messages
                    
                    # 查找最近的工具调用
                    for msg in reversed(recent_messages):
                        if hasattr(msg, 'metadata') and msg.metadata:
                            tool_name = msg.metadata.get('tool_name')
                            if tool_name:
                                # 记录工具使用
                                self.update_tool_usage(tool_name, success=True)
                                
                                # 尝试记录发现
                                await self._record_finding_from_message(msg, tool_name)
            except Exception as e:
                # 静默失败，不影响主流程
                logger.info(f"记录发现时出错: {str(e)}")
        
        return result
    
    async def _extract_tools_and_findings_from_memory(self):
        """Persist actual tool-result text without repr/JSON conversion or duplicate IDs."""
        recorded = getattr(self, "_recorded_tool_results", set())
        for message in await self.memory.get_memory():
            for block in message.get_content_blocks("tool_result"):
                block_id = block.get("id")
                if block_id in recorded:
                    continue
                tool_name = block.get("name", "")
                text = "\n".join(item["text"] for item in block.get("output", [])
                                  if isinstance(item, dict) and item.get("type") == "text")
                if text and not text.startswith(("Error:", "Traceback", "工具调用失败")):
                    await self._record_finding_from_content(text, tool_name)
                    if tool_name not in self.current_tools_used:
                        self.current_tools_used.append(tool_name)
                recorded.add(block_id)
        self._recorded_tool_results = recorded

    async def _record_finding_from_content(self, content: str, tool_name: str):
        """
        从内容中提取并记录研究发现
        
        Args:
            content: 消息内容
            tool_name: 工具名称
        """
        try:
            # ✅ 确保 content 是字符串
            if isinstance(content, list):
                content = str(content)
            elif not isinstance(content, str):
                content = str(content)
            
            # 如果内容太短，不记录
            if not content or not content.strip():
                return
            
            # ✅ 尝试从 JSON 格式的工具输出中提取实际内容
            try:
                import json
                # 检查是否是 JSON 格式
                if content.strip().startswith('{') or content.strip().startswith('['):
                    data = json.loads(content)
                    # 提取实际的文本内容
                    if isinstance(data, dict):
                        if 'output' in data:
                            output = data['output']
                            if isinstance(output, list) and len(output) > 0:
                                if isinstance(output[0], dict) and 'text' in output[0]:
                                    content = output[0]['text']
                        elif 'text' in data:
                            content = data['text']
            except:
                pass  # 如果不是 JSON，继续使用原始内容
            
            # 确定来源类型
            source_type = "unknown"
            source_url = "unknown"
            
            if "web_search" in tool_name or "news_search" in tool_name:
                source_type = "web"
                import re
                urls = re.findall(r"https?://[^\s]+", content)
                source_url = urls[0] if urls else ""
                await self._extract_and_record_arxiv_citations(content)
            elif "wikipedia" in tool_name:
                source_type = "wikipedia"
                source_url = "wikipedia_search"
            elif "arxiv" in tool_name:
                source_type = "arxiv"
                source_url = "arxiv_search"
                # 尝试提取引用
                await self._extract_and_record_arxiv_citations(content)
            elif "image" in tool_name:
                source_type = "image"
                source_url = "image_analysis"
            elif "synthesis" in tool_name or "synthesize" in tool_name:
                source_type = "synthesis"
                source_url = "research_synthesis"
            
            relevance_score = None  # No relevance assessment has been performed.

            # 记录研究发现
            await self.session_memory.add_research_finding(
                source_type=source_type,
                source_url=source_url,
                content=content,
                relevance_score=relevance_score
            )
            
            # 更新发现计数
            self.findings_count += 1
            
            logger.info(f"  已记录研究发现 [{source_type}]: {content[:80]}...")
            
        except Exception as e:
            raise
    

    
    async def _extract_and_record_arxiv_citations(self, content: str) -> None:
        """
        从ArXiv搜索结果中提取并记录引用
        
        Args:
            content: ArXiv搜索结果内容
        """
        try:
            # 简单的解析逻辑：查找论文标题和作者
            lines = content.split('\n')
            current_paper = {}
            
            for line in lines:
                line = line.strip()
                
                # 检测论文标题（通常是数字开头）
                if line and line[0].isdigit() and '. ' in line:
                    # 保存上一篇论文
                    if current_paper.get('title'):
                        await self._save_arxiv_citation(current_paper)
                    
                    # 开始新论文
                    title = line.split('. ', 1)[1] if '. ' in line else line
                    current_paper = {'title': title, 'authors': [], 'url': ''}
                
                # 检测作者行
                elif line.startswith('作者:') or line.startswith('Authors:'):
                    authors_str = line.split(':', 1)[1].strip()
                    # 分割作者名（处理中英文）
                    authors = [a.strip() for a in authors_str.replace('等', '').split(',')]
                    current_paper['authors'] = authors
                
                # 检测ArXiv ID或链接
                elif 'arxiv.org' in line.lower() or line.startswith('ID:'):
                    if 'arxiv.org' in line.lower():
                        # 提取URL
                        import re
                        url_match = re.search(r'https?://[^\s]+', line)
                        if url_match:
                            current_paper['url'] = url_match.group(0)
                    elif line.startswith('ID:'):
                        arxiv_id = line.split(':', 1)[1].strip()
                        current_paper['url'] = f"https://arxiv.org/abs/{arxiv_id}"
                
                # 检测发布年份
                elif '发布时间:' in line or 'Published:' in line:
                    year_str = line.split(':', 1)[1].strip()
                    # 提取年份
                    import re
                    year_match = re.search(r'(\d{4})', year_str)
                    if year_match:
                        current_paper['year'] = int(year_match.group(1))
            
            # 保存最后一篇论文
            if current_paper.get('title'):
                await self._save_arxiv_citation(current_paper)
                
        except Exception as e:
            raise
    
    async def _save_arxiv_citation(self, paper: dict) -> None:
        """
        保存ArXiv论文引用
        
        Args:
            paper: 论文信息字典
        """
        try:
            if not paper.get('title'):
                return
            
            await self.session_memory.add_citation(
                title=paper.get('title', 'Unknown'),
                authors=paper.get('authors', []),
                source_url=paper.get('url', ''),
                publication_year=paper.get('year'),
                doi=None
            )
            
            logger.info(f"已记录引用: {paper.get('title', '')[:50]}...")
            
        except Exception as e:
            raise

    async def conduct_research(
        self,
        query: str,
        research_type: str = "comprehensive",
        sources: Optional[List[str]] = None,
        include_images: bool = False
    ) -> Dict[str, Any]:
        """
        执行深度研究

        Args:
            query: 研究查询
            research_type: 研究类型 (comprehensive, academic, news, analysis)
            sources: 指定的信息源类型
            include_images: 是否包含图像分析

        Returns:
            研究结果字典
        """
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"开始研究: {query}")
            logger.info(f"研究类型: {research_type}")
            logger.info(f"信息源: {sources}")
            logger.info(f"{'='*60}\n")
            
            # 更新研究状态
            self.research_phase = "research"
            self.research_progress = 0.1

            # 创建研究消息
            research_query = self._format_research_query(
                query, research_type, sources, include_images
            )
            
            logger.info(f"研究提示词:\n{research_query}\n")

            research_msg = Msg(
                name="user",
                role="user",
                content=research_query
            )

            # 执行研究
            logger.info("开始执行 ReActAgent 推理循环...")
            
            # 重置失败计数器
            self.tool_failure_tracker = {}
            self.consecutive_failures = 0
            self.recent_actions = []
            
            result = await self(research_msg)
            logger.info(f"ReActAgent 执行完成\n")
            
            # 检查是否因为循环而提前终止
            if self.consecutive_failures >= self.max_consecutive_failures:
                logger.info(f"研究因连续失败 {self.consecutive_failures} 次而终止")

            # ✅ 手动记录工具使用和发现（从内存中提取）
            await self._extract_tools_and_findings_from_memory()

            # 更新进度
            self.research_progress = 0.8

            # 生成研究报告
            logger.info("生成研究报告...")
            report = await self._generate_research_report(query)
            logger.info(f"报告生成完成\n")

            # 完成研究
            self.research_phase = "completed"
            self.research_progress = 1.0
            
            logger.info(f"{'='*60}")
            logger.info(f"研究完成!")
            logger.info(f"使用的工具: {self.current_tools_used}")
            logger.info(f"发现数量: {self.findings_count}")
            logger.info(f"{'='*60}\n")

            # 将 Msg 对象转换为可序列化的格式
            result_content = result.content if hasattr(result, 'content') else str(result)
            
            # ✅ 存储研究结果到实例变量，以便 export_session_data 可以访问
            self.research_result = {
                "session_id": self.session_id,
                "query": query,
                "research_type": research_type,
                "result": result_content,
                "report": report,
                "tools_used": self.current_tools_used,
                "findings_count": self.findings_count,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            return self.research_result

        except Exception as e:
            logger.info(f"\n{'='*60}")
            logger.info(f"研究过程出错: {e}")
            logger.info(f"{'='*60}\n")
            import traceback
            traceback.print_exc()
            
            raise

    def _format_research_query(
        self,
        query: str,
        research_type: str,
        sources: Optional[List[str]],
        include_images: bool
    ) -> str:
        """
        格式化研究查询

        Args:
            query: 原始查询
            research_type: 研究类型
            sources: 指定的信息源
            include_images: 是否包含图像

        Returns:
            格式化的查询字符串
        """
        formatted_query = f"请进行以下深度研究:\n\n主题: {query}\n"

        formatted_query += f"研究类型: {research_type}\n"

        if sources:
            formatted_query += f"优先使用的信息源: {', '.join(sources)}\n"

        if include_images:
            formatted_query += "包含图像分析功能\n"

        formatted_query += """
请按照以下步骤进行研究:
1. 首先使用网络搜索获取最新信息
2. 查找维基百科中的背景知识
3. 搜索相关的学术论文
4. 如有图像，进行图像分析
5. 综合所有信息生成研究报告

请确保研究的全面性和准确性。"""

        return formatted_query

    async def _generate_research_report(self, query: str) -> str:
        """
        使用 LLM 生成研究报告总结

        Args:
            query: 研究查询

        Returns:
            AI 生成的研究报告字符串
        """
        try:
            # 获取所有研究发现
            findings = await self.session_memory.get_research_findings()

            # 获取所有引用
            citations = await self.session_memory.get_citations()

            logger.info(f"开始生成研究报告，发现数量: {len(findings)}, 引用数量: {len(citations)}")

            # 准备发现内容（按相关性排序，取前15个）
            sorted_findings = sorted(
                findings,
                key=lambda x: (x.get("relevance_score") or 0),
                reverse=True
            )[:15]

            findings_text = ""
            for i, finding in enumerate(sorted_findings, 1):
                source_type = finding.get("source_type", "未知")
                content = finding.get("content", "")
                findings_text += f"{i}. [{source_type}] {content}\n\n"

            # 准备引用内容
            citations_text = ""
            for i, citation in enumerate(citations[:10], 1):
                title = citation.get("title", "无标题")
                authors = citation.get("authors", [])
                year = citation.get("publication_year", "")
                citations_text += f"{i}. {title}"
                if authors:
                    citations_text += f" - {', '.join(authors[:3])}"
                if year:
                    citations_text += f" ({year})"
                citations_text += "\n"

            # 构建提示词，让 LLM 生成总结报告
            prompt = f"""请基于以下研究发现和引用，生成一份完整的研究报告。

研究主题: {query}

研究发现:
{findings_text}

参考文献:
{citations_text}

请生成一份结构化的研究报告，包含以下部分：
1. 执行摘要（200-300字）
2. 背景介绍
3. 主要发现（分点详细说明）
4. 深入分析
5. 结论与建议
6. 参考文献列表

要求：
- 使用 Markdown 格式
- 内容要专业、准确、有深度
- 综合所有发现，形成连贯的叙述
- 突出重点和关键信息
- 总字数控制在 2000-3000 字"""

            # 调用 LLM 生成报告
            logger.info("调用 LLM 生成报告...")
            
            # 使用 LLM 生成报告
            from agentscope.message import Msg
            
            report_msg = Msg(
                name="user",
                role="user",
                content=prompt
            )
            
            # 调用 LLM
            response = await self.llm_manager(report_msg)
            
            if response and hasattr(response, 'content'):
                report_content = response.content
                
                # ✅ 处理 content 可能是列表的情况（AgentScope 的 Msg.content 可能是 list[ContentBlock]）
                if isinstance(report_content, list):
                    # 提取所有文本内容
                    text_parts = []
                    for item in report_content:
                        if isinstance(item, dict) and 'text' in item:
                            text_parts.append(str(item['text']))
                        elif hasattr(item, 'text'):
                            text_parts.append(str(item.text))
                        else:
                            text_parts.append(str(item))
                    report_content = '\n'.join(text_parts)
                elif not isinstance(report_content, str):
                    report_content = str(report_content)
                
                logger.info(f"LLM 报告生成完成，长度: {len(report_content)} 字符")
                
                # 添加元数据
                final_report = f"# 深度研究报告\n\n"
                final_report += f"**研究主题**: {query}\n\n"
                final_report += f"**生成时间**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                final_report += f"**数据来源**: {len(findings)} 个发现，{len(citations)} 个引用\n\n"
                final_report += "---\n\n"
                final_report += report_content
                
                return final_report
            else:
                logger.info("LLM 未返回有效内容，使用备用报告格式")
                return self._generate_fallback_report(query, findings, citations)

        except Exception as e:
            error_msg = str(e)
            logger.info(f"生成研究报告时出错: {error_msg}")
            import traceback
            traceback.print_exc()
            
            # ✅ 检查是否是内容敏感错误
            provider_error = getattr(e, "response", None) or {}
            error_code = str(provider_error.get("error", {}).get("code", "")) if isinstance(provider_error, dict) else ""
            if error_code in ("1301", "contentFilter") or "contentFilter" in error_msg or "1301" in error_msg or "敏感内容" in error_msg:
                return f"""# 研究报告生成受限

## 提示

系统检测到研究内容可能包含敏感信息，无法生成完整报告。

您可以：
1. 尝试调整研究主题的表述方式
2. 使用更具体或更学术化的关键词
3. 分段进行研究，避免触发内容过滤

## 已收集的信息

本次研究已成功收集了 {self.findings_count} 条相关信息，但由于内容安全限制，无法生成综合报告。

感谢您的理解与配合。"""
            
            # 尝试使用备用方法
            try:
                findings = await self.session_memory.get_research_findings()
                citations = await self.session_memory.get_citations()
                return self._generate_fallback_report(query, findings, citations)
            except Exception:
                raise RuntimeError("Research report generation failed") from e

    def _generate_fallback_report(self, query: str, findings: List[Dict], citations: List[Dict]) -> str:
        """
        生成备用报告（当 LLM 调用失败时使用）
        
        Args:
            query: 研究查询
            findings: 研究发现列表
            citations: 引用列表
            
        Returns:
            备用格式的报告
        """
        report = f"# 深度研究报告\n\n"
        report += f"**研究主题**: {query}\n\n"
        report += f"**生成时间**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"**数据来源**: {len(findings)} 个发现，{len(citations)} 个引用\n\n"
        report += "---\n\n"

        # 执行摘要
        report += "## 执行摘要\n\n"
        sorted_findings = sorted(findings, key=lambda x: (x.get("relevance_score") or 0), reverse=True)[:3]
        for finding in sorted_findings:
            content = finding.get("content", "")[:200]
            report += f"- {content}...\n\n"

        # 主要发现
        if findings:
            report += "## 主要发现\n\n"
            
            # 按来源分组
            findings_by_source = {}
            for finding in findings:
                source = finding.get("source_type", "其他")
                if source not in findings_by_source:
                    findings_by_source[source] = []
                findings_by_source[source].append(finding)
            
            source_names = {
                "web": "🌐 网络搜索",
                "wikipedia": "📚 维基百科",
                "arxiv": "📖 学术论文",
                "synthesis": "🔍 综合分析"
            }
            
            for source, source_findings in findings_by_source.items():
                report += f"### {source_names.get(source, source)}\n\n"
                top_findings = sorted(source_findings, key=lambda x: (x.get("relevance_score") or 0), reverse=True)[:3]
                for finding in top_findings:
                    content = finding.get("content", "")
                    report += f"- {content}\n\n"

        # 参考文献
        if citations:
            report += "## 参考文献\n\n"
            for i, citation in enumerate(citations[:10], 1):
                title = citation.get("title", "无标题")
                authors = citation.get("authors", [])
                year = citation.get("publication_year", "")
                url = citation.get("source_url", "")
                
                report += f"{i}. {title}"
                if authors:
                    report += f" - {', '.join(authors[:3])}"
                if year:
                    report += f" ({year})"
                if url:
                    report += f"\n   链接: {url}"
                report += "\n\n"

        # 统计信息
        report += "## 研究统计\n\n"
        report += f"- 发现数量: {len(findings)}\n"
        report += f"- 引用数量: {len(citations)}\n"
        report += f"- 使用工具: {len(self.current_tools_used)}\n"

        return report

    async def interrupt_research(self) -> Dict[str, Any]:
        """
        中断当前研究

        Returns:
            中断状态信息
        """
        try:
            # 调用父类中断方法
            await self.interrupt()

            # 保存当前状态
            current_state = await self.session_memory.export_session_data()

            return {
                "session_id": self.session_id,
                "status": "interrupted",
                "phase": self.research_phase,
                "progress": self.research_progress,
                "tools_used": self.current_tools_used,
                "findings_count": self.findings_count,
                "state_data": current_state,
                "interrupted_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "session_id": self.session_id,
                "status": "error",
                "error": str(e),
                "interrupted_at": datetime.utcnow().isoformat()
            }

    async def resume_research(self, state_data: Dict[str, Any]) -> bool:
        """
        恢复被中断的研究

        Args:
            state_data: 保存的状态数据

        Returns:
            是否成功恢复
        """
        try:
            # 恢复记忆状态
            if "short_memory" in state_data:
                for msg_data in state_data["short_memory"]:
                    msg = Msg(
                        name=msg_data["name"],
                        role=msg_data["role"],
                        content=msg_data["content"],
                        timestamp=msg_data.get("timestamp", datetime.utcnow().isoformat())
                    )
                    await self.session_memory.add_message(msg)

            # 恢复其他状态
            self.research_phase = "resumed"
            self.current_tools_used = state_data.get("tools_used", [])
            self.findings_count = len(state_data.get("research_findings", []))

            return True

        except Exception as e:
            logger.info(f"恢复研究时出错: {str(e)}")
            return False

    async def get_research_status(self) -> Dict[str, Any]:
        """
        获取当前研究状态

        Returns:
            研究状态信息
        """
        try:
            memory_stats = await self.memory_manager.get_memory_statistics()

            return {
                "session_id": self.session_id,
                "phase": self.research_phase,
                "progress": self.research_progress,
                "tools_used": self.current_tools_used,
                "findings_count": self.findings_count,
                "memory_stats": memory_stats,
                "last_updated": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "session_id": self.session_id,
                "status": "error",
                "error": str(e)
            }

    async def export_session_data(self) -> Dict[str, Any]:
        """
        导出会话数据

        Returns:
            会话数据字典
        """
        # 从 agent 的 memory 中获取对话历史
        memory_list = []
        if hasattr(self, 'memory') and self.memory:
            # AgentScope 的 memory 对象有 get_memory() 方法
            if hasattr(self.memory, 'get_memory'):
                # ✅ 修复：正确调用异步方法并 await
                msgs = await self.memory.get_memory()
                for msg in msgs:
                    memory_list.append({
                        "role": msg.role if hasattr(msg, 'role') else 'unknown',
                        "name": msg.name if hasattr(msg, 'name') else 'unknown',
                        "content": msg.content if hasattr(msg, 'content') else str(msg),
                        "timestamp": msg.timestamp if hasattr(msg, 'timestamp') else datetime.utcnow().isoformat()
                    })
        
        # 获取研究发现和引用
        findings = await self.session_memory.get_research_findings() if self.session_memory else []
        citations = await self.session_memory.get_citations() if self.session_memory else []
        
        # ✅ 包含研究结果（如果存在）
        result_data = {
            "session_id": self.session_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "short_memory": memory_list,
            "research_findings": findings,
            "citations": citations,
            "tools_used": self.current_tools_used,
            "findings_count": self.findings_count,
            "research_phase": self.research_phase,
            "research_progress": self.research_progress
        }
        
        # 如果研究已完成，包含完整的研究结果
        if hasattr(self, 'research_result') and self.research_result:
            result_data["report"] = self.research_result.get("report", "")
            result_data["result"] = self.research_result.get("result", "")
            result_data["query"] = self.research_result.get("query", "")
        
        return result_data

    def update_tool_usage(self, tool_name: str, success: bool = True, args_str: str = "") -> None:
        """
        更新工具使用记录

        Args:
            tool_name: 使用的工具名称
            success: 工具调用是否成功
            args_str: 工具参数的字符串表示（用于检测重复调用）
        """
        if tool_name not in self.current_tools_used:
            self.current_tools_used.append(tool_name)
        
        # 跟踪失败
        if not success:
            self.tool_failure_tracker[tool_name] = self.tool_failure_tracker.get(tool_name, 0) + 1
            self.consecutive_failures += 1
            
            if self.tool_failure_tracker[tool_name] >= self.max_tool_failures:
                logger.info(f"工具 {tool_name} 已连续失败 {self.tool_failure_tracker[tool_name]} 次")
        else:
            # 成功则重置连续失败计数
            self.consecutive_failures = 0
        
        # 跟踪相同参数的重复调用
        if args_str:
            import hashlib
            args_hash = hashlib.md5(args_str.encode()).hexdigest()
            if tool_name not in self.tool_call_history:
                self.tool_call_history[tool_name] = {}
            self.tool_call_history[tool_name][args_hash] = self.tool_call_history[tool_name].get(args_hash, 0) + 1
            
            # 检测重复调用
            if self.tool_call_history[tool_name][args_hash] >= 2:
                logger.info(f"检测到重复调用: {tool_name} 使用相同参数已被调用 {self.tool_call_history[tool_name][args_hash]} 次")
                logger.info(f"   建议: 尝试不同的工具或参数，或继续下一步研究")
        
        # 记录最近的操作用于检测循环
        self.recent_actions.append(tool_name)
        if len(self.recent_actions) > self.max_stagnation_check:
            self.recent_actions.pop(0)
        
        # 检测是否在原地踏步（连续调用同一个工具）
        if len(self.recent_actions) >= self.max_stagnation_check:
            if len(set(self.recent_actions)) == 1:
                logger.info(f"检测到循环: 连续 {self.max_stagnation_check} 次调用 {tool_name}")
                logger.info(f"   建议: 切换到其他工具（如 search_arxiv_papers）或生成研究报告")
