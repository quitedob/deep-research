# -*- coding: utf-8 -*-
"""
Evidence Agent for Deep Research Platform
Specialized agent for evidence collection, validation, and analysis
"""

import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import re
import hashlib

from .base_agent import BaseResearchAgent, AgentCapability, AgentTask
from .evidence_chain import EvidenceChainManager, EvidenceItem, EvidenceType, EvidenceQuality, EvidenceStatus


class EvidenceAgent(BaseResearchAgent):
    """
    Specialized evidence agent that collects, validates, analyzes, and manages
    evidence throughout the research process
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        evidence_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize evidence agent

        Args:
            agent_id: Unique identifier for the agent
            evidence_config: Configuration for evidence processing
        """
        # Define evidence capabilities
        capabilities = [
            AgentCapability(
                name="evidence_collection",
                description="Collect evidence from various sources",
                priority=1
            ),
            AgentCapability(
                name="evidence_validation",
                description="Validate evidence credibility and accuracy",
                priority=2
            ),
            AgentCapability(
                name="evidence_analysis",
                description="Analyze evidence relationships and patterns",
                priority=3
            ),
            AgentCapability(
                name="evidence_synthesis",
                description="Synthesize evidence into coherent findings",
                priority=3
            ),
            AgentCapability(
                name="quality_assessment",
                description="Assess evidence quality and relevance",
                priority=2
            )
        ]

        super().__init__(
            agent_id=agent_id or f"evidence_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name="Evidence Agent",
            capabilities=capabilities,
            max_concurrent_tasks=3,
            timeout=900  # 15 minutes timeout for evidence tasks
        )

        # Evidence processing configuration
        self.evidence_config = evidence_config or {}
        self.quality_thresholds = self.evidence_config.get("quality_thresholds", {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        })

        # Evidence management
        self.evidence_managers: Dict[str, EvidenceChainManager] = {}
        self.evidence_cache: Dict[str, Any] = {}
        self.validation_rules = self._load_validation_rules()

    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Process an evidence-related task

        Args:
            task: Evidence task to process

        Returns:
            Evidence processing results
        """
        task_type = task.task_type
        parameters = task.parameters

        try:
            if task_type == "evidence_collection":
                return await self._collect_evidence(parameters)
            elif task_type == "evidence_validation":
                return await self._validate_evidence(parameters)
            elif task_type == "evidence_analysis":
                return await self._analyze_evidence(parameters)
            elif task_type == "evidence_synthesis":
                return await self._synthesize_evidence(parameters)
            elif task_type == "quality_assessment":
                return await self._assess_evidence_quality(parameters)
            elif task_type == "evidence_chain_creation":
                return await self._create_evidence_chain(parameters)
            elif task_type == "evidence_relationship_analysis":
                return await self._analyze_evidence_relationships(parameters)
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
        return "evidence_agent"

    async def _collect_evidence(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Collect evidence from various sources"""
        sources = parameters.get("sources", [])
        plan_id = parameters.get("plan_id", "")
        collection_strategy = parameters.get("strategy", "comprehensive")
        quality_filter = parameters.get("quality_filter", "medium")

        if not sources:
            raise ValueError("Sources are required for evidence collection")

        if not plan_id:
            raise ValueError("Plan ID is required for evidence collection")

        # Get or create evidence chain manager
        if plan_id not in self.evidence_managers:
            self.evidence_managers[plan_id] = EvidenceChainManager(plan_id)

        manager = self.evidence_managers[plan_id]
        collected_evidence = []
        collection_stats = {
            "total_sources": len(sources),
            "successful_collections": 0,
            "failed_collections": 0,
            "quality_distribution": {"high": 0, "medium": 0, "low": 0, "unverified": 0}
        }

        for source in sources:
            try:
                # Extract evidence content from source
                evidence_content = self._extract_evidence_content(source)
                if not evidence_content:
                    continue

                # Determine evidence type and quality
                evidence_type = self._determine_evidence_type(source)
                initial_quality = self._assess_initial_quality(source, quality_filter)

                # Add evidence to chain
                evidence_id = await manager.add_evidence(
                    content=evidence_content,
                    source=source.get("url", source.get("title", "Unknown")),
                    evidence_type=evidence_type,
                    collected_by=self.agent_id,
                    quality=initial_quality,
                    metadata=source.get("metadata", {}),
                    tags=source.get("tags", [])
                )

                # Track collection
                evidence_item = manager.evidence_index.get(evidence_id)
                if evidence_item:
                    collected_evidence.append(evidence_item.to_dict())
                    collection_stats["successful_collections"] += 1
                    collection_stats["quality_distribution"][initial_quality] += 1

            except Exception as e:
                collection_stats["failed_collections"] += 1
                print(f"Failed to collect evidence from source: {e}")

        return {
            "success": True,
            "plan_id": plan_id,
            "collected_evidence": [evidence for evidence in collected_evidence],
            "collection_stats": collection_stats,
            "collection_strategy": collection_strategy,
            "quality_filter": quality_filter
        }

    async def _validate_evidence(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate evidence credibility and accuracy"""
        evidence_items = parameters.get("evidence_items", [])
        validation_criteria = parameters.get("criteria", ["source_credibility", "content_accuracy", "freshness"])
        strict_mode = parameters.get("strict_mode", False)

        if not evidence_items:
            raise ValueError("Evidence items are required for validation")

        validation_results = []
        validation_stats = {
            "total_validated": len(evidence_items),
            "passed_validation": 0,
            "failed_validation": 0,
            "validation_score_distribution": {"high": 0, "medium": 0, "low": 0}
        }

        for evidence in evidence_items:
            try:
                validation_result = await self._validate_single_evidence(
                    evidence, validation_criteria, strict_mode
                )
                validation_results.append(validation_result)

                if validation_result["overall_valid"]:
                    validation_stats["passed_validation"] += 1
                else:
                    validation_stats["failed_validation"] += 1

                score_category = self._categorize_validation_score(validation_result["overall_score"])
                validation_stats["validation_score_distribution"][score_category] += 1

            except Exception as e:
                validation_results.append({
                    "evidence_id": evidence.get("id", "unknown"),
                    "valid": False,
                    "error": str(e),
                    "overall_valid": False
                })
                validation_stats["failed_validation"] += 1

        return {
            "success": True,
            "validation_results": validation_results,
            "validation_stats": validation_stats,
            "validation_criteria": validation_criteria,
            "strict_mode": strict_mode
        }

    async def _analyze_evidence(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze evidence patterns and relationships"""
        evidence_items = parameters.get("evidence_items", [])
        analysis_type = parameters.get("analysis_type", "comprehensive")
        focus_areas = parameters.get("focus_areas", [])

        if not evidence_items:
            raise ValueError("Evidence items are required for analysis")

        analysis_results = {}

        # Pattern analysis
        if analysis_type in ["comprehensive", "patterns"]:
            analysis_results["patterns"] = await self._analyze_evidence_patterns(evidence_items)

        # Relationship analysis
        if analysis_type in ["comprehensive", "relationships"]:
            analysis_results["relationships"] = await self._analyze_evidence_relationships(evidence_items)

        # Gap analysis
        if analysis_type in ["comprehensive", "gaps"]:
            analysis_results["gaps"] = await self._identify_evidence_gaps(evidence_items, focus_areas)

        # Quality analysis
        if analysis_type in ["comprehensive", "quality"]:
            analysis_results["quality"] = await self._analyze_evidence_quality_distribution(evidence_items)

        # Temporal analysis
        if analysis_type in ["comprehensive", "temporal"]:
            analysis_results["temporal"] = await self._analyze_temporal_patterns(evidence_items)

        return {
            "success": True,
            "analysis_type": analysis_type,
            "focus_areas": focus_areas,
            "total_evidence_analyzed": len(evidence_items),
            "analysis_results": analysis_results
        }

    async def _synthesize_evidence(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize evidence into coherent findings"""
        evidence_items = parameters.get("evidence_items", [])
        synthesis_type = parameters.get("synthesis_type", "summary")
        confidence_threshold = parameters.get("confidence_threshold", 0.6)
        max_evidence = parameters.get("max_evidence", 50)

        if not evidence_items:
            raise ValueError("Evidence items are required for synthesis")

        # Filter evidence by confidence
        filtered_evidence = [
            evidence for evidence in evidence_items
            if evidence.get("confidence_score", 0) >= confidence_threshold
        ][:max_evidence]

        synthesis_results = {}

        if synthesis_type in ["summary", "comprehensive"]:
            synthesis_results["summary"] = await self._generate_evidence_summary(filtered_evidence)

        if synthesis_type in ["key_findings", "comprehensive"]:
            synthesis_results["key_findings"] = await self._extract_key_findings(filtered_evidence)

        if synthesis_type in ["insights", "comprehensive"]:
            synthesis_results["insights"] = await self._generate_insights(filtered_evidence)

        if synthesis_type in ["recommendations", "comprehensive"]:
            synthesis_results["recommendations"] = await self._generate_recommendations(filtered_evidence)

        return {
            "success": True,
            "synthesis_type": synthesis_type,
            "evidence_used": len(filtered_evidence),
            "confidence_threshold": confidence_threshold,
            "synthesis_results": synthesis_results
        }

    async def _assess_evidence_quality(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Assess quality of evidence items"""
        evidence_items = parameters.get("evidence_items", [])
        assessment_criteria = parameters.get("criteria", ["relevance", "credibility", "freshness", "completeness"])

        if not evidence_items:
            raise ValueError("Evidence items are required for quality assessment")

        quality_assessments = []
        quality_stats = {
            "total_assessed": len(evidence_items),
            "average_quality": 0.0,
            "quality_distribution": {"high": 0, "medium": 0, "low": 0, "unverified": 0}
        }

        total_quality_score = 0.0

        for evidence in evidence_items:
            assessment = await self._assess_single_evidence_quality(evidence, assessment_criteria)
            quality_assessments.append(assessment)

            # Update statistics
            quality_level = assessment["overall_quality"]
            quality_stats["quality_distribution"][quality_level] += 1
            total_quality_score += assessment["overall_score"]

        quality_stats["average_quality"] = total_quality_score / len(evidence_items) if evidence_items else 0.0

        return {
            "success": True,
            "quality_assessments": quality_assessments,
            "quality_stats": quality_stats,
            "assessment_criteria": assessment_criteria
        }

    async def _create_evidence_chain(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new evidence chain"""
        plan_id = parameters.get("plan_id", "")
        title = parameters.get("title", "Evidence Chain")
        description = parameters.get("description", "Evidence collection and analysis")
        initial_evidence = parameters.get("initial_evidence", [])

        if not plan_id:
            raise ValueError("Plan ID is required to create evidence chain")

        # Create evidence chain manager
        manager = EvidenceChainManager(plan_id)
        manager.evidence_chain.title = title
        manager.evidence_chain.description = description

        # Add initial evidence if provided
        if initial_evidence:
            for evidence in initial_evidence:
                await manager.add_evidence(
                    content=evidence.get("content", ""),
                    source=evidence.get("source", ""),
                    evidence_type=evidence.get("type", "other"),
                    collected_by=self.agent_id,
                    quality=evidence.get("quality", "medium"),
                    metadata=evidence.get("metadata", {}),
                    tags=evidence.get("tags", [])
                )

        # Store manager
        self.evidence_managers[plan_id] = manager

        return {
            "success": True,
            "plan_id": plan_id,
            "chain_id": manager.evidence_chain.id,
            "title": title,
            "initial_evidence_count": len(initial_evidence),
            "chain_summary": await manager.get_evidence_summary()
        }

    async def _analyze_evidence_relationships(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze relationships between evidence items"""
        evidence_items = parameters.get("evidence_items", [])
        relationship_types = parameters.get("relationship_types", ["supports", "contradicts", "extends"])

        if not evidence_items:
            raise ValueError("Evidence items are required for relationship analysis")

        relationships = []
        relationship_stats = {
            "total_pairs_analyzed": 0,
            "relationships_found": 0,
            "relationship_type_distribution": {}
        }

        # Analyze pairwise relationships
        for i, evidence1 in enumerate(evidence_items):
            for j, evidence2 in enumerate(evidence_items):
                if i >= j:  # Avoid duplicates
                    continue

                relationship_stats["total_pairs_analyzed"] += 1

                # Determine relationship
                relationship = await self._determine_evidence_relationship(evidence1, evidence2)

                if relationship:
                    relationships.append(relationship)
                    relationship_stats["relationships_found"] += 1

                    rel_type = relationship["type"]
                    if rel_type not in relationship_stats["relationship_type_distribution"]:
                        relationship_stats["relationship_type_distribution"][rel_type] = 0
                    relationship_stats["relationship_type_distribution"][rel_type] += 1

        return {
            "success": True,
            "relationships": relationships,
            "relationship_stats": relationship_stats,
            "relationship_types": relationship_types
        }

    def _extract_evidence_content(self, source: Dict[str, Any]) -> str:
        """Extract evidence content from source"""
        content_sources = [
            source.get("content", ""),
            source.get("snippet", ""),
            source.get("abstract", ""),
            source.get("summary", ""),
            source.get("description", "")
        ]

        # Use the first non-empty content source
        for content in content_sources:
            if content and len(content.strip()) > 50:  # Minimum length threshold
                return content.strip()

        return ""

    def _determine_evidence_type(self, source: Dict[str, Any]) -> str:
        """Determine evidence type based on source characteristics"""
        source_type = source.get("source_type", "").lower()
        url = source.get("url", "").lower()

        if source_type == "academic" or "arxiv" in url:
            return EvidenceType.ACADEMIC_PAPER.value
        elif source_type == "wikipedia":
            return EvidenceType.WEB_SOURCE.value
        elif "edu" in url or "gov" in url:
            return EvidenceType.DOCUMENTATION.value
        elif "book" in url or source_type == "book":
            return EvidenceType.BOOK.value
        elif "survey" in url or "poll" in url:
            return EvidenceType.SURVEY.value
        elif "study" in url or "research" in url:
            return EvidenceType.DATA_ANALYSIS.value
        else:
            return EvidenceType.WEB_SOURCE.value

    def _assess_initial_quality(self, source: Dict[str, Any], quality_filter: str) -> str:
        """Assess initial quality of evidence"""
        score = 0.0

        # Source type quality
        source_type = source.get("source_type", "").lower()
        if source_type == "academic":
            score += 0.3
        elif source_type == "wikipedia":
            score += 0.2
        elif source_type == "web":
            url = source.get("url", "").lower()
            if any(domain in url for domain in ["edu", "gov", "org"]):
                score += 0.2

        # Content length and depth
        content = self._extract_evidence_content(source)
        if len(content) > 1000:
            score += 0.2
        elif len(content) > 500:
            score += 0.1

        # Relevance score if available
        relevance = source.get("relevance_score", 0.5)
        score += relevance * 0.3

        # Determine quality level
        if score >= self.quality_thresholds["high"]:
            return EvidenceQuality.HIGH.value
        elif score >= self.quality_thresholds["medium"]:
            return EvidenceQuality.MEDIUM.value
        elif score >= self.quality_thresholds["low"]:
            return EvidenceQuality.LOW.value
        else:
            return EvidenceQuality.UNVERIFIED.value

    async def _validate_single_evidence(self, evidence: Dict[str, Any], criteria: List[str], strict_mode: bool) -> Dict[str, Any]:
        """Validate a single evidence item"""
        validation_result = {
            "evidence_id": evidence.get("id", "unknown"),
            "validations": {},
            "overall_valid": True,
            "overall_score": 0.0
        }

        total_score = 0.0
        criteria_count = 0

        for criterion in criteria:
            score = 0.0
            if criterion == "source_credibility":
                score = self._validate_source_credibility(evidence)
            elif criterion == "content_accuracy":
                score = self._validate_content_accuracy(evidence)
            elif criterion == "freshness":
                score = self._validate_freshness(evidence)
            elif criterion == "completeness":
                score = self._validate_completeness(evidence)

            validation_result["validations"][criterion] = {
                "score": score,
                "passed": score >= (0.7 if strict_mode else 0.5)
            }

            total_score += score
            criteria_count += 1

            if score < (0.7 if strict_mode else 0.5):
                validation_result["overall_valid"] = False

        validation_result["overall_score"] = total_score / criteria_count if criteria_count > 0 else 0.0

        return validation_result

    def _validate_source_credibility(self, evidence: Dict[str, Any]) -> float:
        """Validate source credibility"""
        score = 0.5  # Base score

        source = evidence.get("source", "").lower()
        evidence_type = evidence.get("evidence_type", "")

        # High credibility sources
        if evidence_type == "academic_paper":
            score += 0.3
        elif evidence_type == "book":
            score += 0.2
        elif "edu" in source or "gov" in source:
            score += 0.2
        elif "org" in source:
            score += 0.1

        return min(score, 1.0)

    def _validate_content_accuracy(self, evidence: Dict[str, Any]) -> float:
        """Validate content accuracy"""
        # Simplified validation - in practice this would use fact-checking
        content = evidence.get("content", "")

        score = 0.5  # Base score

        # Length and detail indicators
        if len(content) > 1000:
            score += 0.2
        elif len(content) > 500:
            score += 0.1

        # Citation and reference indicators
        if any(indicator in content.lower() for indicator in ["study", "research", "according to", "data shows"]):
            score += 0.2

        return min(score, 1.0)

    def _validate_freshness(self, evidence: Dict[str, Any]) -> float:
        """Validate evidence freshness"""
        collection_date = evidence.get("collection_date")
        if collection_date:
            try:
                date_obj = datetime.fromisoformat(collection_date.replace('Z', '+00:00'))
                days_old = (datetime.now(date_obj.tzinfo) - date_obj).days

                if days_old <= 30:
                    return 1.0
                elif days_old <= 90:
                    return 0.8
                elif days_old <= 365:
                    return 0.6
                else:
                    return 0.4
            except:
                pass

        return 0.6  # Default score

    def _validate_completeness(self, evidence: Dict[str, Any]) -> float:
        """Validate evidence completeness"""
        score = 0.5  # Base score

        content = evidence.get("content", "")
        if len(content) > 1000:
            score += 0.3
        elif len(content) > 500:
            score += 0.2
        elif len(content) > 200:
            score += 0.1

        # Structure indicators
        if any(indicator in content.lower() for indicator in ["conclusion", "summary", "therefore", "because"]):
            score += 0.2

        return min(score, 1.0)

    def _categorize_validation_score(self, score: float) -> str:
        """Categorize validation score"""
        if score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        else:
            return "low"

    async def _analyze_evidence_patterns(self, evidence_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in evidence"""
        patterns = {
            "common_themes": [],
            "source_types": {},
            "quality_distribution": {},
            "temporal_patterns": {}
        }

        # Analyze source types
        for evidence in evidence_items:
            source_type = evidence.get("evidence_type", "unknown")
            patterns["source_types"][source_type] = patterns["source_types"].get(source_type, 0) + 1

        # Analyze quality distribution
        for evidence in evidence_items:
            quality = evidence.get("quality", "unknown")
            patterns["quality_distribution"][quality] = patterns["quality_distribution"].get(quality, 0) + 1

        return patterns

    async def _identify_evidence_gaps(self, evidence_items: List[Dict[str, Any]], focus_areas: List[str]) -> List[str]:
        """Identify gaps in evidence"""
        gaps = []

        # Check for missing source types
        source_types = set(evidence.get("evidence_type", "") for evidence in evidence_items)
        expected_types = {"academic_paper", "book", "web_source", "documentation"}
        missing_types = expected_types - source_types

        for missing_type in missing_types:
            gaps.append(f"Missing {missing_type.replace('_', ' ')} sources")

        # Check focus area coverage
        for area in focus_areas:
            area_coverage = sum(
                1 for evidence in evidence_items
                if area.lower() in evidence.get("content", "").lower()
            )
            if area_coverage == 0:
                gaps.append(f"No evidence covering focus area: {area}")

        return gaps

    async def _analyze_evidence_quality_distribution(self, evidence_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze quality distribution of evidence"""
        quality_scores = []
        for evidence in evidence_items:
            confidence = evidence.get("confidence_score", 0.5)
            relevance = evidence.get("relevance_score", 0.5)
            overall_quality = (confidence + relevance) / 2
            quality_scores.append(overall_quality)

        if not quality_scores:
            return {"average": 0.0, "min": 0.0, "max": 0.0, "distribution": {}}

        return {
            "average": sum(quality_scores) / len(quality_scores),
            "min": min(quality_scores),
            "max": max(quality_scores),
            "distribution": {
                "high": len([s for s in quality_scores if s >= 0.8]),
                "medium": len([s for s in quality_scores if 0.6 <= s < 0.8]),
                "low": len([s for s in quality_scores if s < 0.6])
            }
        }

    async def _analyze_temporal_patterns(self, evidence_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal patterns in evidence"""
        dates = []
        for evidence in evidence_items:
            collection_date = evidence.get("collection_date")
            if collection_date:
                try:
                    date_obj = datetime.fromisoformat(collection_date.replace('Z', '+00:00'))
                    dates.append(date_obj)
                except:
                    pass

        if not dates:
            return {"date_range": "Unknown", "evidence_over_time": {}}

        dates.sort()
        return {
            "date_range": f"{dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}",
            "total_timespan_days": (dates[-1] - dates[0]).days,
            "evidence_over_time": {
                "last_30_days": len([d for d in dates if (datetime.now(d.tzinfo) - d).days <= 30]),
                "last_90_days": len([d for d in dates if (datetime.now(d.tzinfo) - d).days <= 90]),
                "older": len([d for d in dates if (datetime.now(d.tzinfo) - d).days > 90])
            }
        }

    async def _generate_evidence_summary(self, evidence_items: List[Dict[str, Any]]) -> str:
        """Generate summary of evidence"""
        if not evidence_items:
            return "No evidence available for summary."

        summary_parts = []
        summary_parts.append(f"Evidence Summary based on {len(evidence_items)} items:")

        # Quality overview
        high_quality = len([e for e in evidence_items if e.get("confidence_score", 0) >= 0.8])
        summary_parts.append(f"\nHigh-quality evidence: {high_quality}/{len(evidence_items)} ({high_quality/len(evidence_items)*100:.1f}%)")

        # Source type distribution
        source_types = {}
        for evidence in evidence_items:
            source_type = evidence.get("evidence_type", "unknown")
            source_types[source_type] = source_types.get(source_type, 0) + 1

        summary_parts.append("\nSource Types:")
        for source_type, count in source_types.items():
            summary_parts.append(f"  {source_type.replace('_', ' ').title()}: {count}")

        return "".join(summary_parts)

    async def _extract_key_findings(self, evidence_items: List[Dict[str, Any]]) -> List[str]:
        """Extract key findings from evidence"""
        findings = []

        # Sort by confidence and relevance
        sorted_evidence = sorted(
            evidence_items,
            key=lambda x: (x.get("confidence_score", 0) + x.get("relevance_score", 0)) / 2,
            reverse=True
        )

        # Extract top findings
        for evidence in sorted_evidence[:10]:
            content = evidence.get("content", "")
            if content:
                # Extract first meaningful sentence or phrase
                sentences = content.split('.')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) > 50 and len(sentence) < 300:
                        findings.append(sentence)
                        break

        return findings[:5]  # Top 5 findings

    async def _generate_insights(self, evidence_items: List[Dict[str, Any]]) -> List[str]:
        """Generate insights from evidence"""
        insights = []

        # Quality insight
        avg_confidence = sum(e.get("confidence_score", 0) for e in evidence_items) / len(evidence_items)
        if avg_confidence >= 0.8:
            insights.append("Evidence shows high overall confidence levels")
        elif avg_confidence <= 0.5:
            insights.append("Evidence confidence levels are relatively low, consider additional sources")

        # Source diversity insight
        source_types = set(e.get("evidence_type", "") for e in evidence_items)
        if len(source_types) >= 4:
            insights.append("Good diversity of source types strengthens findings")
        elif len(source_types) <= 2:
            insights.append("Limited source type diversity, consider broadening source base")

        return insights

    async def _generate_recommendations(self, evidence_items: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on evidence"""
        recommendations = []

        # Quality recommendations
        low_quality_count = len([e for e in evidence_items if e.get("confidence_score", 0) < 0.6])
        if low_quality_count > len(evidence_items) * 0.3:
            recommendations.append("Seek higher quality sources to strengthen evidence base")

        # Source type recommendations
        source_types = [e.get("evidence_type", "") for e in evidence_items]
        if "academic_paper" not in source_types:
            recommendations.append("Consider including academic research papers for stronger support")

        return recommendations

    async def _assess_single_evidence_quality(self, evidence: Dict[str, Any], criteria: List[str]) -> Dict[str, Any]:
        """Assess quality of a single evidence item"""
        assessment = {
            "evidence_id": evidence.get("id", "unknown"),
            "criteria_scores": {},
            "overall_score": 0.0,
            "overall_quality": "medium"
        }

        total_score = 0.0
        for criterion in criteria:
            score = 0.0
            if criterion == "relevance":
                score = evidence.get("relevance_score", 0.5)
            elif criterion == "credibility":
                score = self._assess_evidence_credibility(evidence)
            elif criterion == "freshness":
                score = self._assess_evidence_freshness(evidence)
            elif criterion == "completeness":
                score = self._assess_evidence_completeness(evidence)

            assessment["criteria_scores"][criterion] = score
            total_score += score

        assessment["overall_score"] = total_score / len(criteria) if criteria else 0.0

        if assessment["overall_score"] >= 0.8:
            assessment["overall_quality"] = "high"
        elif assessment["overall_score"] >= 0.6:
            assessment["overall_quality"] = "medium"
        else:
            assessment["overall_quality"] = "low"

        return assessment

    def _assess_evidence_credibility(self, evidence: Dict[str, Any]) -> float:
        """Assess evidence credibility"""
        return self._validate_source_credibility(evidence)

    def _assess_evidence_freshness(self, evidence: Dict[str, Any]) -> float:
        """Assess evidence freshness"""
        return self._validate_freshness(evidence)

    def _assess_evidence_completeness(self, evidence: Dict[str, Any]) -> float:
        """Assess evidence completeness"""
        return self._validate_completeness(evidence)

    async def _determine_evidence_relationship(self, evidence1: Dict[str, Any], evidence2: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Determine relationship between two evidence items"""
        content1 = evidence1.get("content", "").lower()
        content2 = evidence2.get("content", "").lower()

        # Check for supporting relationship
        if self._is_supporting_evidence(content1, content2):
            return {
                "evidence_1_id": evidence1.get("id"),
                "evidence_2_id": evidence2.get("id"),
                "type": "supports",
                "confidence": 0.7,
                "description": "Evidence 1 supports evidence 2"
            }

        # Check for contradictory relationship
        if self._is_contradictory_evidence(content1, content2):
            return {
                "evidence_1_id": evidence1.get("id"),
                "evidence_2_id": evidence2.get("id"),
                "type": "contradicts",
                "confidence": 0.6,
                "description": "Evidence items contradict each other"
            }

        return None

    def _is_supporting_evidence(self, content1: str, content2: str) -> bool:
        """Check if content1 supports content2"""
        # Simplified check - in practice this would use more sophisticated NLP
        words1 = set(content1.split()[:10])  # First 10 words
        words2 = set(content2.split()[:10])

        overlap = len(words1.intersection(words2))
        return overlap >= 3  # At least 3 overlapping words

    def _is_contradictory_evidence(self, content1: str, content2: str) -> bool:
        """Check if content contradicts content2"""
        contradictory_pairs = [
            ("increase", "decrease"),
            ("improve", "worsen"),
            ("beneficial", "harmful"),
            ("effective", "ineffective"),
            ("support", "oppose")
        ]

        for word1, word2 in contradictory_pairs:
            if word1 in content1 and word2 in content2:
                return True
            if word2 in content1 and word1 in content2:
                return True

        return False

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules for evidence"""
        return {
            "source_credibility": {
                "academic": 0.9,
                "government": 0.8,
                "educational": 0.7,
                "organizational": 0.6,
                "commercial": 0.4,
                "unknown": 0.3
            },
            "content_requirements": {
                "min_length": 100,
                "max_length": 10000,
                "required_indicators": ["evidence", "data", "research", "study"]
            },
            "freshness_thresholds": {
                "excellent": 30,  # days
                "good": 90,
                "acceptable": 365,
                "outdated": 730
            }
        }