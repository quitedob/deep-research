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
    """研究专用 Agent - 集成搜索和分析能力 (策略二：提供参考资料)"""

    def __init__(self, config: AgentConfig):
        # 确保研究 Agent 有必要的工具
        if not config.tools:
            config.tools = ["kimi_search", "arxiv_search", "wikipedia_search", "tavily_search"]

        # 确保有研究能力
        if not config.capabilities:
            config.capabilities = ["research", "analysis", "synthesis", "fact_checking"]

        # 设置默认的研究相关配置
        if not config.role_definition:
            config.role_definition = "专业的研究员，擅长信息收集、分析和综合，具备批判性思维和信息验证能力"
        if not config.reasoning_mode:
            config.reasoning_mode = "step_by_step"
        if not config.output_format:
            config.output_format = "markdown"

        super().__init__(config)

        # 研究特定配置
        self.research_depth = "deep"  # shallow, medium, deep
        self.max_sources = 20
        self.min_sources = 3

        # 参考资料管理 (策略二)
        self.reference_materials = []
        self.source_credibility_scores = {}
        self.research_timeline = []

        logger.info(f"Research Agent {self.name} initialized with enhanced research capabilities")
    
    async def conduct_research(
        self,
        topic: str,
        requirements: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """执行增强研究任务 (策略二：集成参考资料)"""
        requirements = requirements or {}

        # 清空之前的研究状态
        self.reference_materials = []
        self.source_credibility_scores = {}
        self.research_timeline = []

        # 创建增强研究消息
        research_content = self.integrate_reference_materials(
            f"请对以下主题进行深度研究: {topic}",
            requirements.get("initial_sources", [])
        )

        research_msg = Msg(
            name="user",
            content=research_content,
            role="user",
            metadata={
                "task_type": "enhanced_research",
                "requirements": requirements,
                "research_depth": self.research_depth,
                "max_sources": self.max_sources,
                "min_sources": self.min_sources
            }
        )

        # 记录研究开始
        self.research_timeline.append({
            "action": "research_started",
            "topic": topic,
            "timestamp": self._get_current_timestamp()
        })

        # 执行研究
        result = await self.reply(research_msg)

        # 提取和整理研究结果
        research_result = {
            "topic": topic,
            "result": result.content,
            "metadata": result.metadata,
            "reference_materials": self.reference_materials,
            "source_credibility": self.source_credibility_scores,
            "sources_count": len(self.reference_materials),
            "iterations": result.metadata.get("iterations", 0),
            "confidence_score": result.metadata.get("confidence_score", 0.0),
            "research_timeline": self.research_timeline
        }

        # 记录研究完成
        self.research_timeline.append({
            "action": "research_completed",
            "sources_found": len(self.reference_materials),
            "confidence": research_result["confidence_score"],
            "timestamp": self._get_current_timestamp()
        })

        return research_result
    
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
    
    async def analyze_sources(self, sources: List[Dict]) -> Dict[str, Any]:
        """增强信息源分析 (策略二：提供参考资料)"""
        # 评估源的可信度
        for source in sources:
            credibility_score = self._assess_source_credibility(source)
            self.source_credibility_scores[source.get("url", source.get("title", "unknown"))] = credibility_score

        # 创建增强分析消息
        analysis_content = self.integrate_reference_materials(
            f"请分析以下 {len(sources)} 个信息源，提取关键信息和洞察",
            sources
        )

        analysis_msg = Msg(
            name="user",
            content=analysis_content,
            role="user",
            metadata={
                "task_type": "enhanced_source_analysis",
                "sources": sources,
                "credibility_scores": self.source_credibility_scores
            }
        )

        result = await self.reply(analysis_msg)

        # 更新参考资料
        self._update_reference_materials(sources, "source_analysis")

        return {
            "analysis": result.content,
            "key_findings": result.metadata.get("key_findings", []),
            "insights": result.metadata.get("insights", []),
            "source_assessment": self.source_credibility_scores,
            "confidence": result.metadata.get("confidence_score", 0.0)
        }

    async def synthesize_report(self, research_data: Dict) -> str:
        """增强研究报告合成 (策略二：集成参考资料)"""
        # 提取所有参考资料
        all_references = research_data.get("reference_materials", [])

        # 创建增强合成消息
        synthesis_content = self.integrate_reference_materials(
            "请将研究数据合成为一份完整的研究报告，包括引用来源和可信度评估",
            all_references
        )

        synthesis_msg = Msg(
            name="user",
            content=synthesis_content,
            role="user",
            metadata={
                "task_type": "enhanced_synthesis",
                "research_data": research_data,
                "reference_count": len(all_references),
                "source_credibility": self.source_credibility_scores
            }
        )

        result = await self.reply(synthesis_msg)
        return result.content

    def add_reference_material(self, material: Dict[str, Any]) -> None:
        """添加参考资料 (策略二)"""
        # 评估材料可信度
        credibility = self._assess_source_credibility(material)

        # 添加材料
        self.reference_materials.append({
            **material,
            "credibility_score": credibility,
            "added_timestamp": self._get_current_timestamp()
        })

        # 记录操作
        self.research_timeline.append({
            "action": "reference_added",
            "source": material.get("title", "unknown"),
            "credibility": credibility,
            "timestamp": self._get_current_timestamp()
        })

    def _assess_source_credibility(self, source: Dict[str, Any]) -> float:
        """评估信息源可信度 (策略二：提供参考资料)"""
        score = 0.5  # 基础分数

        # 1. 来源类型评估
        source_type = source.get("type", "").lower()
        type_scores = {
            "academic": 0.9,      # 学术论文
            "government": 0.85,   # 政府报告
            "news": 0.6,         # 新闻报道
            "blog": 0.4,         # 博客
            "forum": 0.3,        # 论坛
            "wiki": 0.7          # 维基百科
        }
        score = type_scores.get(source_type, score)

        # 2. 作者/机构可信度
        author = source.get("author", "").lower()
        institution = source.get("institution", "").lower()

        trusted_institutions = [
            "university", "college", "institute", "research",
            "government", "official", "academic"
        ]

        if any(trusted in institution for trusted in trusted_institutions):
            score += 0.1

        if "professor" in author or "ph.d" in author or "dr." in author:
            score += 0.1

        # 3. 时效性
        if "date" in source:
            try:
                # 简单的时效性检查
                date_str = str(source["date"])
                if "2024" in date_str or "2025" in date_str:
                    score += 0.1
                elif "2020" in date_str or "2021" in date_str or "2022" in date_str or "2023" in date_str:
                    score += 0.05
            except:
                pass

        # 4. 引用和验证
        if source.get("citations", 0) > 10:
            score += 0.05
        if source.get("peer_reviewed", False):
            score += 0.1

        return min(max(score, 0.0), 1.0)  # 确保分数在0-1之间

    def _update_reference_materials(self, sources: List[Dict], context: str) -> None:
        """更新参考资料列表"""
        for source in sources:
            if source not in self.reference_materials:
                self.add_reference_material({
                    **source,
                    "context": context
                })

    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def filter_sources_by_credibility(self, min_credibility: float = 0.6) -> List[Dict]:
        """根据可信度过滤信息源 (策略二)"""
        return [
            material for material in self.reference_materials
            if material.get("credibility_score", 0.0) >= min_credibility
        ]

    def get_research_summary(self) -> Dict[str, Any]:
        """获取研究摘要"""
        if not self.reference_materials:
            return {"status": "no research data"}

        credible_sources = self.filter_sources_by_credibility(0.6)
        avg_credibility = sum(m.get("credibility_score", 0.0) for m in self.reference_materials) / len(self.reference_materials)

        return {
            "total_sources": len(self.reference_materials),
            "credible_sources": len(credible_sources),
            "average_credibility": avg_credibility,
            "research_stages": len(self.research_timeline),
            "timeline": self.research_timeline,
            "source_types": list(set(m.get("type", "unknown") for m in self.reference_materials))
        }

    def get_research_capabilities(self) -> List[str]:
        """获取增强研究能力"""
        return [
            "多源信息搜索",
            "学术论文检索",
            "百科知识查询",
            "信息分析和综合",
            "报告生成",
            "事实核查",
            "趋势分析",
            "来源可信度评估",
            "参考资料集成",
            "批判性思维分析",
            "信息交叉验证",
            "研究过程追踪"
        ]


def create_research_agents() -> Dict[str, ResearchAgent]:
    """创建预定义的增强研究 Agent"""
    agents = {}

    # 通用研究 Agent (使用增强配置)
    agents["general_researcher"] = ResearchAgent(AgentConfig(
        name="通用研究员",
        role="researcher",
        role_definition="专业的研究员，擅长信息收集、分析和综合，具备批判性思维和信息验证能力",
        system_prompt="""你是一个专业的研究员，擅长收集、分析和综合各种信息。
你的任务是帮助用户进行深度研究，提供准确、全面和有洞察力的信息。

工作流程:
1. 理解研究需求
2. 制定搜索策略
3. 收集多源信息
4. 分析和验证信息
5. 综合生成报告

研究原则:
- 优先使用高可信度的信息源
- 对信息进行交叉验证
- 明确标注信息来源和可信度
- 保持客观、准确和专业

请使用思维链推理方法，详细展示你的研究过程。""",
        capabilities=["research", "analysis", "synthesis", "fact_checking"],
        tools=["kimi_search", "arxiv_search", "wikipedia_search", "tavily_search"],
        reasoning_mode="step_by_step",
        output_format="markdown",
        behavior_guidance=[
            "优先查找学术和官方来源",
            "对每个信息源进行可信度评估",
            "提供明确的信息来源引用",
            "交叉验证关键信息",
            "区分事实和观点"
        ],
        quality_criteria=["信息准确性", "来源可靠性", "分析深度", "逻辑连贯性"],
        few_shot_examples=[
            {
                "input": "研究人工智能在医疗领域的应用",
                "output": "我会从学术数据库、官方医疗机构报告和权威新闻来源收集信息，并对每个来源进行可信度评估..."
            }
        ]
    ))

    # 学术研究 Agent (使用增强配置)
    agents["academic_researcher"] = ResearchAgent(AgentConfig(
        name="学术研究员",
        role="academic_researcher",
        role_definition="学术研究专家，专注于学术论文和科研资料的研究，具备深度学术分析能力",
        system_prompt="""你是一个学术研究专家，专注于学术论文和科研资料的研究。
你擅长查找最新的学术文献，分析研究趋势，评估研究质量。

专业领域:
- 学术论文检索和分析
- 研究方法评估
- 文献综述
- 科研趋势分析

学术研究原则:
- 优先选择同行评议的期刊文章
- 评估研究的样本大小和方法论
- 考虑研究的局限性和偏差
- 提供平衡的观点

请使用严谨的学术方法进行研究分析。""",
        capabilities=["academic_research", "literature_review", "trend_analysis", "methodology_evaluation"],
        tools=["arxiv_search", "kimi_search", "wikipedia_search", "google_scholar_search"],
        reasoning_mode="chain_of_thought",
        output_format="markdown",
        language_style="academic",
        behavior_guidance=[
            "优先检索同行评议的学术文献",
            "评估研究方法的严谨性",
            "考虑研究的局限性和偏差",
            "提供平衡的学术观点",
            "正确引用学术来源"
        ],
        quality_criteria=["学术严谨性", "方法科学性", "结论可靠性", "引用规范性"],
        context_requirements=[
            "需要充分的学术数据库访问",
            "考虑研究的时效性和影响因子",
            "关注研究方法和样本大小"
        ]
    ))

    # 事实核查专家 Agent (新增)
    agents["fact_checker"] = ResearchAgent(AgentConfig(
        name="事实核查专家",
        role="fact_checker",
        role_definition="专业的事实核查专家，擅长验证信息准确性和识别虚假信息",
        system_prompt="""你是一个专业的事实核查专家，擅长验证信息的准确性。
你的任务是检查信息的真实性，识别潜在的虚假信息和误导性内容。

核查流程:
1. 分解待核查的声明
2. 查找原始信息源
3. 交叉验证多个来源
4. 评估信息源的可靠性
5. 得出核查结论

核查标准:
- 优先使用第一手信息源
- 检查信息的时效性
- 识别潜在的偏见和误导
- 提供明确的核查结论

请以高度的责任感和严谨性进行事实核查。""",
        capabilities=["fact_checking", "source_verification", "bias_detection", "accuracy_assessment"],
        tools=["kimi_search", "wikipedia_search", "tavily_search", "official_sources_search"],
        reasoning_mode="step_by_step",
        output_format="structured",
        behavior_guidance=[
            "总是查找第一手信息源",
            "交叉验证关键信息",
            "识别和标注潜在的偏见",
            "提供明确的可信度评级",
            "区分事实、观点和推测"
        ],
        quality_criteria=["准确性", "可靠性", "客观性", "透明度"]
    ))

    return agents
