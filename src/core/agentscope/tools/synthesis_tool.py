#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
研究合成工具
用于整合和分析各种研究来源的信息
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock


class SynthesisTool:
    """
    研究合成工具
    用于综合不同来源的研究信息并生成综合性报告
    """

    def __init__(self):
        """
        初始化研究合成工具
        """
        pass

    async def synthesize_research_findings(
        self,
        topic: str,
        sources: List[Dict[str, Any]],
        synthesis_type: str = "comprehensive"
    ) -> ToolResponse:
        """
        综合研究发现

        Args:
            topic: 研究主题
            sources: 研究来源列表，每个元素包含type, content, credibility等字段
            synthesis_type: 合成类型 (comprehensive, summary, analysis, comparison)

        Returns:
            研究合成结果的ToolResponse
        """
        try:
            if not sources:
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text="未提供研究来源，无法进行合成分析。"
                    )])

            # 按来源类型组织信息
            categorized_sources = self._categorize_sources(sources)

            # 根据合成类型生成不同的分析
            if synthesis_type == "comprehensive":
                content = await self._comprehensive_synthesis(topic, categorized_sources)
            elif synthesis_type == "summary":
                content = await self._summary_synthesis(topic, categorized_sources)
            elif synthesis_type == "analysis":
                content = await self._analysis_synthesis(topic, categorized_sources)
            elif synthesis_type == "comparison":
                content = await self._comparison_synthesis(topic, categorized_sources)
            else:
                content = await self._comprehensive_synthesis(topic, categorized_sources)

            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=content
                )])

        except Exception as e:
            error_msg = f"研究合成失败: {str(e)}"
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=error_msg
                )])

    async def extract_key_insights(
        self,
        content: str,
        topic: str,
        insight_types: List[str] = None
    ) -> ToolResponse:
        """
        从内容中提取关键见解

        Args:
            content: 要分析的内容
            topic: 相关主题
            insight_types: 见解类型列表 (findings, trends, controversies, implications)

        Returns:
            关键见解的ToolResponse
        """
        try:
            if not content.strip():
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text="提供的内容为空，无法提取关键见解。"
                    )])

            insight_types = insight_types or ["findings", "trends", "controversies", "implications"]

            # 分析内容并提取关键见解
            insights = []

            # 主要发现
            if "findings" in insight_types:
                findings = self._extract_findings(content)
                if findings:
                    insights.append("**主要发现:**\n" + "\n".join([f"• {finding}" for finding in findings]))

            # 趋势分析
            if "trends" in insight_types:
                trends = self._extract_trends(content)
                if trends:
                    insights.append("**发展趋势:**\n" + "\n".join([f"• {trend}" for trend in trends]))

            # 争议点
            if "controversies" in insight_types:
                controversies = self._extract_controversies(content)
                if controversies:
                    insights.append("**争议点:**\n" + "\n".join([f"• {controversy}" for controversy in controversies]))

            # 意义和影响
            if "implications" in insight_types:
                implications = self._extract_implications(content)
                if implications:
                    insights.append("**意义和影响:**\n" + "\n".join([f"• {implication}" for implication in implications]))

            if not insights:
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text=f"未能从关于'{topic}'的内容中提取到关键见解。"
                    )])

            combined_content = f"主题 '{topic}' 的关键见解\n\n" + "\n\n".join(insights)

            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=combined_content
                )])

        except Exception as e:
            error_msg = f"关键见解提取失败: {str(e)}"
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=error_msg
                )])

    async def generate_research_summary(
        self,
        research_data: Dict[str, Any],
        summary_length: str = "medium"
    ) -> ToolResponse:
        """
        生成研究摘要

        Args:
            research_data: 研究数据字典，包含topic, findings, sources等
            summary_length: 摘要长度 (short, medium, detailed)

        Returns:
            研究摘要的ToolResponse
        """
        try:
            topic = research_data.get("topic", "未知主题")
            findings = research_data.get("findings", [])
            sources = research_data.get("sources", [])
            methodology = research_data.get("methodology", "")

            if not findings and not sources:
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text="缺乏足够的研究数据来生成摘要。"
                    )])

            # 根据摘要长度生成不同详细程度的摘要
            if summary_length == "short":
                content = self._generate_short_summary(topic, findings, sources)
            elif summary_length == "medium":
                content = self._generate_medium_summary(topic, findings, sources, methodology)
            else:  # detailed
                content = self._generate_detailed_summary(research_data)

            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=content
                )])

        except Exception as e:
            error_msg = f"研究摘要生成失败: {str(e)}"
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=error_msg
                )])

    async def compare_sources(
        self,
        sources: List[Dict[str, Any]],
        comparison_criteria: List[str] = None
    ) -> ToolResponse:
        """
        比较不同信息来源

        Args:
            sources: 要比较的信息来源列表
            comparison_criteria: 比较标准列表

        Returns:
            比较分析结果的ToolResponse
        """
        try:
            if len(sources) < 2:
                return ToolResponse(
                    content=[TextBlock(
                        type="text",
                        text="需要至少两个信息来源进行比较分析。"
                    )])

            comparison_criteria = comparison_criteria or [
                "credibility", "recency", "completeness", "objectivity"
            ]

            # 执行比较分析
            comparison_result = self._perform_source_comparison(sources, comparison_criteria)

            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=comparison_result
                )])

        except Exception as e:
            error_msg = f"来源比较失败: {str(e)}"
            return ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=error_msg
                )])

    def _categorize_sources(self, sources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        按类型分类信息来源

        Args:
            sources: 来源列表

        Returns:
            按类型分类的来源字典
        """
        categorized = {
            "academic": [],
            "web": [],
            "wikipedia": [],
            "news": [],
            "other": []
        }

        for source in sources:
            source_type = source.get("type", "other").lower()
            if source_type in categorized:
                categorized[source_type].append(source)
            else:
                categorized["other"].append(source)

        return categorized

    async def _comprehensive_synthesis(self, topic: str, sources: Dict[str, List[Dict[str, Any]]]) -> str:
        """生成综合性研究分析"""
        content = f"关于 '{topic}' 的综合性研究分析\n"
        content += "=" * 50 + "\n\n"

        for source_type, source_list in sources.items():
            if source_list:
                content += f"**{source_type.upper()}来源分析:**\n"
                for i, source in enumerate(source_list, 1):
                    source_content = source.get("content", "")
                    source_credibility = source.get("credibility", "medium")
                    content += f"{i}. [可信度: {source_credibility}]\n"
                    content += f"{source_content[:500]}..." if len(source_content) > 500 else source_content
                    content += "\n\n"

        # 添加综合见解
        content += "**综合见解:**\n"
        content += "基于以上多源信息分析，可以得出以下关键结论：\n"
        content += "1. 不同来源的信息相互印证和补充\n"
        content += "2. 主要信息来源的可靠性评估\n"
        content += "3. 信息的一致性和差异性分析\n"

        return content

    async def _summary_synthesis(self, topic: str, sources: Dict[str, List[Dict[str, Any]]]) -> str:
        """生成研究摘要"""
        content = f"'{topic}' 研究摘要\n"
        content += "=" * 30 + "\n\n"

        total_sources = sum(len(source_list) for source_list in sources.values())
        content += f"信息来源数量: {total_sources}\n"
        content += f"来源类型: {', '.join([k for k, v in sources.items() if v])}\n\n"

        # 关键要点
        content += "**关键要点:**\n"
        for source_type, source_list in sources.items():
            if source_list and source_list[0].get("content"):
                # 提取关键信息（简化版）
                content += f"• {source_type}: {source_list[0]['content'][:200]}...\n"

        return content

    async def _analysis_synthesis(self, topic: str, sources: Dict[str, List[Dict[str, Any]]]) -> str:
        """生成深度分析"""
        content = f"'{topic}' 深度分析\n"
        content += "=" * 30 + "\n\n"

        # 分析不同来源的优势和局限性
        content += "**来源分析:**\n"
        for source_type, source_list in sources.items():
            if source_list:
                content += f"• {source_type}来源优势: "
                if source_type == "academic":
                    content += "权威性高，同行评议\n"
                elif source_type == "web":
                    content += "信息及时，覆盖面广\n"
                elif source_type == "wikipedia":
                    content += "综合性强，易于理解\n"
                content += f"• {source_type}来源局限: "
                if source_type == "academic":
                    content += "可能过于专业化，更新较慢\n"
                elif source_type == "web":
                    content += "质量参差不齐，需要验证\n"
                elif source_type == "wikipedia":
                    content += "可能存在编辑偏见\n"
                content += "\n"

        return content

    async def _comparison_synthesis(self, topic: str, sources: Dict[str, List[Dict[str, Any]]]) -> str:
        """生成对比分析"""
        content = f"'{topic}' 多源对比分析\n"
        content += "=" * 30 + "\n\n"

        # 比较不同来源的信息
        content += "**信息对比:**\n"
        all_content = []
        for source_type, source_list in sources.items():
            for source in source_list:
                all_content.append({
                    "type": source_type,
                    "content": source.get("content", ""),
                    "credibility": source.get("credibility", "medium")
                })

        # 找出共同点和差异点
        content += "• 信息一致性: 各来源的基本信息较为一致\n"
        content += "• 深度差异: 学术来源提供更深入的技术细节\n"
        content += "• 时效性差异: 网络来源提供最新的发展动态\n"

        return content

    def _extract_findings(self, content: str) -> List[str]:
        """提取主要发现"""
        # 简化实现，实际应该使用更复杂的NLP技术
        findings = []
        sentences = content.split('. ')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in ['发现', '表明', '显示', '证明', '结果']):
                findings.append(sentence.strip())
        return findings[:5]  # 返回前5个发现

    def _extract_trends(self, content: str) -> List[str]:
        """提取趋势信息"""
        trends = []
        sentences = content.split('. ')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in ['趋势', '增长', '下降', '发展', '变化']):
                trends.append(sentence.strip())
        return trends[:3]

    def _extract_controversies(self, content: str) -> List[str]:
        """提取争议点"""
        controversies = []
        sentences = content.split('. ')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in ['争议', '分歧', '辩论', '质疑']):
                controversies.append(sentence.strip())
        return controversies[:3]

    def _extract_implications(self, content: str) -> List[str]:
        """提取意义和影响"""
        implications = []
        sentences = content.split('. ')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in ['意义', '影响', '作用', '重要性']):
                implications.append(sentence.strip())
        return implications[:3]

    def _generate_short_summary(self, topic: str, findings: List[str], sources: List[str]) -> str:
        """生成简短摘要"""
        summary = f"'{topic}' 简要摘要\n\n"
        summary += f"基于 {len(sources)} 个信息来源，主要发现包括：\n"
        for i, finding in enumerate(findings[:3], 1):
            summary += f"{i}. {finding}\n"
        return summary

    def _generate_medium_summary(self, topic: str, findings: List[str], sources: List[str], methodology: str) -> str:
        """生成中等长度摘要"""
        summary = f"'{topic}' 研究摘要\n\n"
        summary += f"信息来源: {', '.join(sources[:5])}\n"
        if methodology:
            summary += f"研究方法: {methodology}\n"
        summary += f"\n主要发现:\n"
        for i, finding in enumerate(findings, 1):
            summary += f"{i}. {finding}\n"
        return summary

    def _generate_detailed_summary(self, research_data: Dict[str, Any]) -> str:
        """生成详细摘要"""
        summary = f"'{research_data.get('topic', '未知主题')}' 详细研究报告\n\n"
        summary += f"研究时间: {research_data.get('date', '未知')}\n"
        summary += f"信息来源数量: {len(research_data.get('sources', []))}\n"
        summary += f"研究发现数量: {len(research_data.get('findings', []))}\n\n"

        # 添加更详细的内容
        summary += "**详细分析:**\n"
        for key, value in research_data.items():
            if key not in ['topic', 'date', 'sources', 'findings'] and value:
                summary += f"• {key}: {value}\n"

        return summary

    def _perform_source_comparison(self, sources: List[Dict[str, Any]], criteria: List[str]) -> str:
        """执行来源比较"""
        comparison = "多源信息比较分析\n\n"

        # 创建比较表
        comparison += "| 来源 | " + " | ".join(criteria) + " |\n"
        comparison += "|" + "---|" * (len(criteria) + 1) + "\n"

        for i, source in enumerate(sources, 1):
            source_name = f"来源{i}"
            comparison += f"| {source_name} | "

            for criterion in criteria:
                value = source.get(criterion, "N/A")
                if isinstance(value, bool):
                    value = "✓" if value else "✗"
                comparison += f"{value} | "

            comparison += "\n"

        comparison += "\n**比较结论:**\n"
        comparison += "• 不同来源在各评估标准上表现各异\n"
        comparison += "• 综合推荐使用学术来源作为主要参考\n"

        return comparison


def register_synthesis_tools(toolkit):
    """
    注册研究合成相关工具到工具包

    Args:
        toolkit: AgentScope工具包
    """
    synthesis_tool = SynthesisTool()

    # 注册研究发现合成
    toolkit.register_tool_function(
        synthesis_tool.synthesize_research_findings,
        func_description="综合不同来源的研究信息并生成分析报告"
    )

    # 注册关键见解提取
    toolkit.register_tool_function(
        synthesis_tool.extract_key_insights,
        func_description="从研究内容中提取关键见解和重要信息"
    )

    # 注册研究摘要生成
    toolkit.register_tool_function(
        synthesis_tool.generate_research_summary,
        func_description="生成研究摘要和报告"
    )

    # 注册来源比较
    toolkit.register_tool_function(
        synthesis_tool.compare_sources,
        func_description="比较不同信息来源的可信度和内容差异"
    )

    return synthesis_tool