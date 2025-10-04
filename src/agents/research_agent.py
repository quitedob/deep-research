# -*- coding: utf-8 -*-
"""
研究专用 Agent - 参考 AgentScope 设计
"""
import logging
from typing import Any, Dict, List, Optional

from .react_agent import ReActAgent
from .base_agent import AgentConfig
from ..message import Msg

logger = logging.getLogger(__name__)


class ResearchAgent(ReActAgent):
    """研究专用 Agent - 集成搜索和分析能力"""
    
    def __init__(self, config: AgentConfig):
        # 确保研究 Agent 有必要的工具
        if not config.tools:
            config.tools = ["kimi_search", "arxiv_search", "wikipedia_search"]
        
        # 确保有研究能力
        if not config.capabilities:
            config.capabilities = ["research", "analysis", "synthesis"]
        
        super().__init__(config)
        
        # 研究特定配置
        self.research_depth = "deep"  # shallow, medium, deep
        self.max_sources = 20
        self.min_sources = 3
        
        logger.info(f"Research Agent {self.name} initialized")
    
    async def conduct_research(
        self, 
        topic: str, 
        requirements: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """执行研究任务"""
        requirements = requirements or {}
        
        # 创建研究消息
        research_msg = Msg(
            name="user",
            content=f"请对以下主题进行深度研究: {topic}",
            role="user",
            metadata={
                "task_type": "research",
                "requirements": requirements
            }
        )
        
        # 执行研究
        result = await self.reply(research_msg)
        
        # 提取研究结果
        return {
            "topic": topic,
            "result": result.content,
            "metadata": result.metadata,
            "sources_count": len(result.metadata.get("sources", [])),
            "iterations": result.metadata.get("iterations", 0)
        }
    
    async def analyze_sources(self, sources: List[Dict]) -> Dict[str, Any]:
        """分析信息源"""
        analysis_msg = Msg(
            name="user",
            content=f"请分析以下 {len(sources)} 个信息源，提取关键信息和洞察",
            role="user",
            metadata={
                "task_type": "analysis",
                "sources": sources
            }
        )
        
        result = await self.reply(analysis_msg)
        
        return {
            "analysis": result.content,
            "key_findings": result.metadata.get("key_findings", []),
            "insights": result.metadata.get("insights", [])
        }
    
    async def synthesize_report(self, research_data: Dict) -> str:
        """合成研究报告"""
        synthesis_msg = Msg(
            name="user",
            content="请将研究数据合成为一份完整的研究报告",
            role="user",
            metadata={
                "task_type": "synthesis",
                "research_data": research_data
            }
        )
        
        result = await self.reply(synthesis_msg)
        return result.content
    
    def get_research_capabilities(self) -> List[str]:
        """获取研究能力"""
        return [
            "多源信息搜索",
            "学术论文检索",
            "百科知识查询",
            "信息分析和综合",
            "报告生成",
            "事实核查",
            "趋势分析"
        ]


def create_research_agents() -> Dict[str, ResearchAgent]:
    """创建预定义的研究 Agent"""
    agents = {}
    
    # 通用研究 Agent
    agents["general_researcher"] = ResearchAgent(AgentConfig(
        name="通用研究员",
        role="researcher",
        system_prompt="""你是一个专业的研究员，擅长收集、分析和综合各种信息。
你的任务是帮助用户进行深度研究，提供准确、全面和有洞察力的信息。

工作流程:
1. 理解研究需求
2. 制定搜索策略
3. 收集多源信息
4. 分析和验证信息
5. 综合生成报告

请始终保持客观、准确和专业。""",
        capabilities=["research", "analysis", "synthesis"],
        tools=["kimi_search", "arxiv_search", "wikipedia_search"]
    ))
    
    # 学术研究 Agent
    agents["academic_researcher"] = ResearchAgent(AgentConfig(
        name="学术研究员",
        role="academic_researcher",
        system_prompt="""你是一个学术研究专家，专注于学术论文和科研资料的研究。
你擅长查找最新的学术文献，分析研究趋势，评估研究质量。

专业领域:
- 学术论文检索和分析
- 研究方法评估
- 文献综述
- 科研趋势分析

请提供高质量的学术研究支持。""",
        capabilities=["academic_research", "literature_review", "trend_analysis"],
        tools=["arxiv_search", "kimi_search", "wikipedia_search"]
    ))
    
    return agents
