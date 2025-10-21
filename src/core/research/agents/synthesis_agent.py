# -*- coding: utf-8 -*-
"""
Synthesis Agent for Deep Research Platform
Specialized agent for synthesizing research findings and generating insights
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re
from collections import defaultdict, Counter

from .base_agent import BaseResearchAgent, AgentCapability, AgentTask


class SynthesisAgent(BaseResearchAgent):
    """
    Specialized synthesis agent that combines research findings, evidence,
    and insights into coherent reports and recommendations
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        synthesis_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize synthesis agent

        Args:
            agent_id: Unique identifier for the agent
            synthesis_config: Configuration for synthesis processes
        """
        # Define synthesis capabilities
        capabilities = [
            AgentCapability(
                name="research_synthesis",
                description="Synthesize research findings from multiple sources",
                priority=1
            ),
            AgentCapability(
                name="evidence_integration",
                description="Integrate evidence into coherent narratives",
                priority=2
            ),
            AgentCapability(
                name="insight_generation",
                description="Generate actionable insights from research",
                priority=3
            ),
            AgentCapability(
                name="recommendation_creation",
                description="Create evidence-based recommendations",
                priority=3
            ),
            AgentCapability(
                name="report_generation",
                description="Generate comprehensive research reports",
                priority=2
            ),
            AgentCapability(
                name="conclusion_formulation",
                description="Formulate evidence-based conclusions",
                priority=2
            )
        ]

        super().__init__(
            agent_id=agent_id or f"synthesis_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name="Synthesis Agent",
            capabilities=capabilities,
            max_concurrent_tasks=2,
            timeout=1200  # 20 minutes timeout for synthesis tasks
        )

        # Synthesis configuration
        self.synthesis_config = synthesis_config or {}
        self.synthesis_templates = self._load_synthesis_templates()
        self.insight_patterns = self._load_insight_patterns()

    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Process a synthesis task

        Args:
            task: Synthesis task to process

        Returns:
            Synthesis results
        """
        task_type = task.task_type
        parameters = task.parameters

        try:
            if task_type == "research_synthesis":
                return await self._synthesize_research_findings(parameters)
            elif task_type == "evidence_integration":
                return await self._integrate_evidence(parameters)
            elif task_type == "insight_generation":
                return await self._generate_insights(parameters)
            elif task_type == "recommendation_creation":
                return await self._create_recommendations(parameters)
            elif task_type == "report_generation":
                return await self._generate_report(parameters)
            elif task_type == "conclusion_formulation":
                return await self._formulate_conclusions(parameters)
            elif task_type == "comprehensive_synthesis":
                return await self._perform_comprehensive_synthesis(parameters)
            elif task_type == "comparative_analysis":
                return await self._perform_comparative_analysis(parameters)
            else:
                raise ValueError(f"Unknown task type: {task_type}")

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "task_type": task_type,
                "parameters": parameters
            }

    def get_agent_type(self) -> str:
        """Get the agent type identifier"""
        return "synthesis_agent"

    async def _synthesize_research_findings(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize research findings from multiple sources"""
        research_findings = parameters.get("research_findings", [])
        synthesis_type = parameters.get("synthesis_type", "comprehensive")
        focus_areas = parameters.get("focus_areas", [])
        target_audience = parameters.get("target_audience", "general")

        if not research_findings:
            raise ValueError("Research findings are required for synthesis")

        # Preprocess findings
        processed_findings = await self._preprocess_findings(research_findings)

        # Perform synthesis based on type
        if synthesis_type == "comprehensive":
            synthesis_result = await self._comprehensive_synthesis(processed_findings, focus_areas, target_audience)
        elif synthesis_type == "thematic":
            synthesis_result = await self._thematic_synthesis(processed_findings, focus_areas)
        elif synthesis_type == "chronological":
            synthesis_result = await self._chronological_synthesis(processed_findings)
        elif synthesis_type == "comparative":
            synthesis_result = await self._comparative_synthesis(processed_findings)
        else:
            synthesis_result = await self._comprehensive_synthesis(processed_findings, focus_areas, target_audience)

        return {
            "success": True,
            "synthesis_type": synthesis_type,
            "focus_areas": focus_areas,
            "target_audience": target_audience,
            "synthesis_result": synthesis_result,
            "findings_processed": len(processed_findings),
            "quality_metrics": await self._calculate_synthesis_quality(synthesis_result, processed_findings)
        }

    async def _integrate_evidence(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate evidence into coherent narratives"""
        evidence_items = parameters.get("evidence_items", [])
        integration_strategy = parameters.get("strategy", "thematic")
        narrative_type = parameters.get("narrative_type", "analytical")
        quality_threshold = parameters.get("quality_threshold", 0.6)

        if not evidence_items:
            raise ValueError("Evidence items are required for integration")

        # Filter evidence by quality
        high_quality_evidence = [
            evidence for evidence in evidence_items
            if evidence.get("confidence_score", 0) >= quality_threshold
        ]

        # Group evidence based on strategy
        if integration_strategy == "thematic":
            grouped_evidence = await self._group_evidence_by_theme(high_quality_evidence)
        elif integration_strategy == "chronological":
            grouped_evidence = await self._group_evidence_by_time(high_quality_evidence)
        elif integration_strategy == "source_type":
            grouped_evidence = await self._group_evidence_by_source_type(high_quality_evidence)
        else:
            grouped_evidence = await self._group_evidence_by_theme(high_quality_evidence)

        # Generate narratives
        narratives = []
        for group_name, evidence_group in grouped_evidence.items():
            narrative = await self._generate_narrative(
                evidence_group, group_name, narrative_type
            )
            narratives.append(narrative)

        # Create integrated summary
        integrated_summary = await self._create_integrated_summary(narratives)

        return {
            "success": True,
            "integration_strategy": integration_strategy,
            "narrative_type": narrative_type,
            "quality_threshold": quality_threshold,
            "evidence_used": len(high_quality_evidence),
            "total_evidence": len(evidence_items),
            "evidence_groups": dict(grouped_evidence),
            "narratives": narratives,
            "integrated_summary": integrated_summary
        }

    async def _generate_insights(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate actionable insights from research and evidence"""
        research_data = parameters.get("research_data", [])
        evidence_data = parameters.get("evidence_data", [])
        insight_type = parameters.get("insight_type", "strategic")
        context = parameters.get("context", {})
        max_insights = parameters.get("max_insights", 10)

        # Combine all data sources
        all_data = research_data + evidence_data

        if not all_data:
            raise ValueError("Research or evidence data is required for insight generation")

        # Analyze patterns and trends
        patterns = await self._analyze_patterns(all_data)
        trends = await self._identify_trends(all_data)
        anomalies = await self._detect_anomalies(all_data)

        # Generate insights based on type
        if insight_type == "strategic":
            insights = await self._generate_strategic_insights(patterns, trends, context)
        elif insight_type == "operational":
            insights = await self._generate_operational_insights(patterns, trends, context)
        elif insight_type == "predictive":
            insights = await self._generate_predictive_insights(patterns, trends, anomalies, context)
        else:
            insights = await self._generate_strategic_insights(patterns, trends, context)

        # Prioritize and limit insights
        prioritized_insights = await self._prioritize_insights(insights)
        final_insights = prioritized_insights[:max_insights]

        return {
            "success": True,
            "insight_type": insight_type,
            "context": context,
            "data_sources": {
                "research_findings": len(research_data),
                "evidence_items": len(evidence_data),
                "total_sources": len(all_data)
            },
            "analysis_results": {
                "patterns": patterns,
                "trends": trends,
                "anomalies": anomalies
            },
            "insights": final_insights,
            "insight_count": len(final_insights)
        }

    async def _create_recommendations(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create evidence-based recommendations"""
        insights = parameters.get("insights", [])
        evidence_summary = parameters.get("evidence_summary", {})
        recommendation_type = parameters.get("type", "actionable")
        target_context = parameters.get("target_context", {})
        priority_level = parameters.get("priority_level", "medium")

        if not insights:
            raise ValueError("Insights are required for recommendation creation")

        # Analyze evidence strength
        evidence_strength = await self._analyze_evidence_strength(evidence_summary)

        # Generate recommendations based on type
        if recommendation_type == "actionable":
            recommendations = await self._generate_actionable_recommendations(
                insights, evidence_strength, target_context
            )
        elif recommendation_type == "strategic":
            recommendations = await self._generate_strategic_recommendations(
                insights, evidence_strength, target_context
            )
        elif recommendation_type == "operational":
            recommendations = await self._generate_operational_recommendations(
                insights, evidence_strength, target_context
            )
        else:
            recommendations = await self._generate_actionable_recommendations(
                insights, evidence_strength, target_context
            )

        # Prioritize recommendations
        prioritized_recommendations = await self._prioritize_recommendations(
            recommendations, priority_level, evidence_strength
        )

        return {
            "success": True,
            "recommendation_type": recommendation_type,
            "target_context": target_context,
            "priority_level": priority_level,
            "evidence_strength": evidence_strength,
            "insights_used": len(insights),
            "recommendations": prioritized_recommendations,
            "recommendation_count": len(prioritized_recommendations)
        }

    async def _generate_report(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive research report"""
        title = parameters.get("title", "Research Report")
        research_findings = parameters.get("research_findings", [])
        evidence_items = parameters.get("evidence_items", [])
        insights = parameters.get("insights", [])
        recommendations = parameters.get("recommendations", [])
        report_format = parameters.get("format", "standard")
        include_sections = parameters.get("include_sections", ["summary", "findings", "evidence", "insights", "recommendations"])

        # Generate report sections
        report_sections = {}

        if "summary" in include_sections:
            report_sections["executive_summary"] = await self._generate_executive_summary(
                research_findings, evidence_items, insights
            )

        if "findings" in include_sections:
            report_sections["research_findings"] = await self._structure_findings_section(research_findings)

        if "evidence" in include_sections:
            report_sections["evidence_analysis"] = await self._structure_evidence_section(evidence_items)

        if "insights" in include_sections:
            report_sections["key_insights"] = await self._structure_insights_section(insights)

        if "recommendations" in include_sections:
            report_sections["recommendations"] = await self._structure_recommendations_section(recommendations)

        if "methodology" in include_sections:
            report_sections["methodology"] = await self._generate_methodology_section(
                research_findings, evidence_items
            )

        if "conclusions" in include_sections:
            report_sections["conclusions"] = await self._generate_conclusions_section(
                research_findings, insights, recommendations
            )

        # Generate metadata
        metadata = await self._generate_report_metadata(
            title, research_findings, evidence_items, insights, recommendations
        )

        return {
            "success": True,
            "title": title,
            "report_format": report_format,
            "generated_at": datetime.now().isoformat(),
            "metadata": metadata,
            "sections": report_sections,
            "section_count": len(report_sections)
        }

    async def _formulate_conclusions(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Formulate evidence-based conclusions"""
        primary_findings = parameters.get("primary_findings", [])
        supporting_evidence = parameters.get("supporting_evidence", [])
        confidence_level = parameters.get("confidence_level", "moderate")
        conclusion_type = parameters.get("type", "comprehensive")

        if not primary_findings:
            raise ValueError("Primary findings are required for conclusion formulation")

        # Analyze evidence support for conclusions
        evidence_support = await self._analyze_evidence_support(primary_findings, supporting_evidence)

        # Formulate conclusions based on type
        if conclusion_type == "comprehensive":
            conclusions = await self._formulate_comprehensive_conclusions(
                primary_findings, evidence_support, confidence_level
            )
        elif conclusion_type == "focused":
            conclusions = await self._formulate_focused_conclusions(
                primary_findings, evidence_support, confidence_level
            )
        elif conclusion_type == "predictive":
            conclusions = await self._formulate_predictive_conclusions(
                primary_findings, evidence_support, confidence_level
            )
        else:
            conclusions = await self._formulate_comprehensive_conclusions(
                primary_findings, evidence_support, confidence_level
            )

        # Validate conclusions
        validated_conclusions = await self._validate_conclusions(conclusions, evidence_support)

        return {
            "success": True,
            "conclusion_type": conclusion_type,
            "confidence_level": confidence_level,
            "primary_findings_count": len(primary_findings),
            "supporting_evidence_count": len(supporting_evidence),
            "evidence_support": evidence_support,
            "conclusions": validated_conclusions,
            "conclusion_count": len(validated_conclusions)
        }

    async def _perform_comprehensive_synthesis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive synthesis of all research components"""
        research_findings = parameters.get("research_findings", [])
        evidence_items = parameters.get("evidence_items", [])
        existing_insights = parameters.get("insights", [])
        context = parameters.get("context", {})
        synthesis_goals = parameters.get("goals", ["understanding", "insights", "recommendations"])

        if not research_findings and not evidence_items:
            raise ValueError("Research findings or evidence items are required for comprehensive synthesis")

        synthesis_results = {}

        # Synthesize research findings
        if research_findings and "understanding" in synthesis_goals:
            research_synthesis = await self._synthesize_research_findings({
                "research_findings": research_findings,
                "synthesis_type": "comprehensive",
                "context": context
            })
            synthesis_results["research_synthesis"] = research_synthesis

        # Integrate evidence
        if evidence_items and "understanding" in synthesis_goals:
            evidence_integration = await self._integrate_evidence({
                "evidence_items": evidence_items,
                "strategy": "thematic"
            })
            synthesis_results["evidence_integration"] = evidence_integration

        # Generate new insights
        if "insights" in synthesis_goals:
            all_data = research_findings + evidence_items
            insight_generation = await self._generate_insights({
                "research_data": research_findings,
                "evidence_data": evidence_items,
                "insight_type": "strategic",
                "context": context
            })
            synthesis_results["insight_generation"] = insight_generation

        # Create recommendations
        if "recommendations" in synthesis_goals:
            insights = (
                synthesis_results.get("insight_generation", {}).get("insights", []) or
                existing_insights
            )
            if insights:
                recommendation_creation = await self._create_recommendations({
                    "insights": insights,
                    "evidence_summary": await self._create_evidence_summary(evidence_items),
                    "type": "actionable",
                    "target_context": context
                })
                synthesis_results["recommendation_creation"] = recommendation_creation

        # Generate overall synthesis summary
        synthesis_summary = await self._generate_comprehensive_summary(synthesis_results)

        return {
            "success": True,
            "synthesis_goals": synthesis_goals,
            "context": context,
            "data_sources": {
                "research_findings": len(research_findings),
                "evidence_items": len(evidence_items),
                "existing_insights": len(existing_insights)
            },
            "synthesis_results": synthesis_results,
            "synthesis_summary": synthesis_summary
        }

    async def _perform_comparative_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comparative analysis of different sources or perspectives"""
        comparison_groups = parameters.get("comparison_groups", [])
        comparison_criteria = parameters.get("criteria", ["relevance", "quality", "recency"])
        analysis_depth = parameters.get("analysis_depth", "detailed")

        if len(comparison_groups) < 2:
            raise ValueError("At least two comparison groups are required")

        # Analyze each group
        group_analyses = {}
        for group_name, group_data in comparison_groups.items():
            group_analysis = await self._analyze_comparison_group(group_data, comparison_criteria)
            group_analyses[group_name] = group_analysis

        # Compare groups
        comparison_results = await self._compare_groups(group_analyses, comparison_criteria)

        # Identify similarities and differences
        similarities = await self._identify_similarities(group_analyses)
        differences = await self._identify_differences(group_analyses)

        # Generate comparative insights
        comparative_insights = await self._generate_comparative_insights(
            group_analyses, comparison_results, similarities, differences
        )

        return {
            "success": True,
            "comparison_criteria": comparison_criteria,
            "analysis_depth": analysis_depth,
            "group_count": len(comparison_groups),
            "group_analyses": group_analyses,
            "comparison_results": comparison_results,
            "similarities": similarities,
            "differences": differences,
            "comparative_insights": comparative_insights
        }

    # Helper methods for synthesis operations

    async def _preprocess_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preprocess research findings for synthesis"""
        processed = []

        for finding in findings:
            processed_finding = {
                "id": finding.get("id", ""),
                "content": finding.get("content", ""),
                "source": finding.get("source", ""),
                "relevance_score": finding.get("relevance_score", 0.5),
                "confidence_score": finding.get("confidence_score", 0.5),
                "timestamp": finding.get("timestamp", datetime.now().isoformat()),
                "themes": await self._extract_themes(finding.get("content", "")),
                "key_points": await self._extract_key_points(finding.get("content", ""))
            }
            processed.append(processed_finding)

        return processed

    async def _comprehensive_synthesis(self, findings: List[Dict[str, Any]], focus_areas: List[str], target_audience: str) -> Dict[str, Any]:
        """Perform comprehensive synthesis of findings"""
        # Identify main themes
        all_themes = []
        for finding in findings:
            all_themes.extend(finding.get("themes", []))
        theme_counts = Counter(all_themes)
        main_themes = [theme for theme, count in theme_counts.most_common(5)]

        # Group findings by themes
        themed_findings = defaultdict(list)
        for finding in findings:
            for theme in finding.get("themes", []):
                if theme in main_themes:
                    themed_findings[theme].append(finding)

        # Generate synthesis for each theme
        theme_syntheses = {}
        for theme, theme_findings in themed_findings.items():
            theme_synthesis = await self._synthesize_theme(theme, theme_findings, target_audience)
            theme_syntheses[theme] = theme_synthesis

        # Generate overall synthesis
        overall_synthesis = await self._generate_overall_synthesis(theme_syntheses, findings)

        return {
            "main_themes": main_themes,
            "theme_syntheses": theme_syntheses,
            "overall_synthesis": overall_synthesis,
            "focus_areas_coverage": await self._assess_focus_areas_coverage(theme_syntheses, focus_areas),
            "target_audience_adaptation": target_audience
        }

    async def _generate_narrative(self, evidence_group: List[Dict[str, Any]], group_name: str, narrative_type: str) -> Dict[str, Any]:
        """Generate narrative for a group of evidence"""
        if not evidence_group:
            return {"title": group_name, "narrative": "", "supporting_evidence": []}

        # Extract key information from evidence
        key_points = []
        supporting_evidence = []

        for evidence in evidence_group:
            content = evidence.get("content", "")
            if content:
                # Extract main point
                sentences = content.split('.')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) > 50 and len(sentence) < 200:
                        key_points.append(sentence)
                        break

                supporting_evidence.append({
                    "source": evidence.get("source", ""),
                    "content": content[:200] + "..." if len(content) > 200 else content,
                    "confidence": evidence.get("confidence_score", 0.5)
                })

        # Generate narrative based on type
        if narrative_type == "analytical":
            narrative = await self._generate_analytical_narrative(group_name, key_points, supporting_evidence)
        elif narrative_type == "storytelling":
            narrative = await self._generate_storytelling_narrative(group_name, key_points, supporting_evidence)
        else:
            narrative = await self._generate_analytical_narrative(group_name, key_points, supporting_evidence)

        return {
            "title": group_name,
            "narrative_type": narrative_type,
            "narrative": narrative,
            "key_points": key_points[:3],  # Top 3 key points
            "supporting_evidence_count": len(supporting_evidence),
            "average_confidence": sum(e["confidence"] for e in supporting_evidence) / len(supporting_evidence) if supporting_evidence else 0.0
        }

    async def _analyze_patterns(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze patterns in the data"""
        patterns = []

        # Frequency patterns
        content_texts = [item.get("content", "").lower() for item in data if item.get("content")]
        word_freq = Counter()
        for text in content_texts:
            words = re.findall(r'\b\w+\b', text)
            word_freq.update(words)

        # Extract significant patterns (high-frequency words)
        significant_words = [(word, count) for word, count in word_freq.most_common(20) if len(word) > 4]

        for word, count in significant_words:
            if count >= 3:  # Minimum frequency threshold
                patterns.append({
                    "type": "frequency",
                    "pattern": word,
                    "frequency": count,
                    "significance": count / len(content_texts),
                    "description": f"Word '{word}' appears in {count} out of {len(content_texts)} sources"
                })

        return patterns

    async def _identify_trends(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify trends in the data"""
        trends = []

        # Temporal trends if timestamps are available
        timestamped_data = [
            item for item in data
            if item.get("timestamp") and item.get("content")
        ]

        if timestamped_data:
            # Group by time periods
            time_groups = defaultdict(list)
            for item in timestamped_data:
                try:
                    timestamp = datetime.fromisoformat(item["timestamp"].replace('Z', '+00:00'))
                    period = timestamp.strftime("%Y-%m")  # Monthly grouping
                    time_groups[period].append(item)
                except:
                    continue

            # Identify trends over time
            if len(time_groups) > 1:
                sorted_periods = sorted(time_groups.keys())
                for i in range(len(sorted_periods) - 1):
                    current_period = sorted_periods[i]
                    next_period = sorted_periods[i + 1]

                    current_count = len(time_groups[current_period])
                    next_count = len(time_groups[next_period])

                    if next_count > current_count * 1.2:  # 20% increase
                        trends.append({
                            "type": "increasing",
                            "period": f"{current_period} to {next_period}",
                            "change_percentage": ((next_count - current_count) / current_count) * 100,
                            "description": f"Increasing trend from {current_period} to {next_period}"
                        })
                    elif next_count < current_count * 0.8:  # 20% decrease
                        trends.append({
                            "type": "decreasing",
                            "period": f"{current_period} to {next_period}",
                            "change_percentage": ((current_count - next_count) / current_count) * 100,
                            "description": f"Decreasing trend from {current_period} to {next_period}"
                        })

        return trends

    async def _detect_anomalies(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in the data"""
        anomalies = []

        # Content length anomalies
        content_lengths = [len(item.get("content", "")) for item in data if item.get("content")]
        if content_lengths:
            avg_length = sum(content_lengths) / len(content_lengths)
            std_dev = (sum((x - avg_length) ** 2 for x in content_lengths) / len(content_lengths)) ** 0.5

            for item in data:
                content = item.get("content", "")
                if content:
                    length = len(content)
                    # Outliers are more than 2 standard deviations from mean
                    if abs(length - avg_length) > 2 * std_dev:
                        anomalies.append({
                            "type": "content_length",
                            "item_id": item.get("id", "unknown"),
                            "value": length,
                            "expected_range": f"{avg_length - 2 * std_dev:.0f} - {avg_length + 2 * std_dev:.0f}",
                            "description": f"Content length {length} is unusually {'long' if length > avg_length else 'short'}"
                        })

        return anomalies

    async def _extract_themes(self, content: str) -> List[str]:
        """Extract themes from content"""
        if not content:
            return []

        # Simple theme extraction based on keyword frequency
        words = re.findall(r'\b\w+\b', content.lower())
        word_freq = Counter(words)

        # Filter out common words and get significant themes
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how', 'not', 'no', 'yes'}

        significant_words = [
            word for word, count in word_freq.items()
            if word not in common_words and len(word) > 4 and count >= 2
        ]

        return significant_words[:5]  # Top 5 themes

    async def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content"""
        if not content:
            return []

        # Split into sentences and extract meaningful ones
        sentences = [s.strip() for s in content.split('.') if s.strip()]

        key_points = []
        for sentence in sentences:
            # Filter for meaningful sentences
            if (len(sentence) > 30 and
                len(sentence) < 300 and
                any(indicator in sentence.lower() for indicator in
                    ['therefore', 'however', 'furthermore', 'consequently', 'because', 'since', 'result', 'finding', 'conclusion'])):
                key_points.append(sentence)

        return key_points[:3]  # Top 3 key points

    def _load_synthesis_templates(self) -> Dict[str, str]:
        """Load synthesis templates"""
        return {
            "executive_summary": """
Based on comprehensive analysis of {source_count} sources, the research reveals {main_findings}.
Key themes identified include {themes}. The evidence quality assessment indicates {quality_assessment}.
""",
            "thematic_synthesis": """
Theme: {theme}
Evidence from {evidence_count} sources supports this theme.
Key findings: {key_findings}
Confidence level: {confidence_level}
""",
            "recommendation": """
Recommendation: {recommendation}
Evidence support: {evidence_support}
Priority: {priority}
Expected impact: {impact}
"""
        }

    def _load_insight_patterns(self) -> Dict[str, List[str]]:
        """Load insight generation patterns"""
        return {
            "strategic": [
                "The data suggests a strategic opportunity in {area}",
                "Based on the evidence, focusing on {focus_area} could yield significant benefits",
                "The convergence of evidence points to {conclusion}"
            ],
            "operational": [
                "Operationally, the findings suggest {operational_implication}",
                "The evidence indicates that {process} should be {action}",
                "From an implementation perspective, {recommendation}"
            ],
            "predictive": [
                "Based on current trends, we can predict {prediction}",
                "The pattern suggests that {outcome} is likely",
                "Extrapolating from the evidence, {future_state}"
            ]
        }