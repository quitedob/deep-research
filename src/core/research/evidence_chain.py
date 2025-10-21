# -*- coding: utf-8 -*-
"""
Evidence Chain Analysis System for Deep Research Platform
Manages evidence collection, analysis, and synthesis
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    """Types of evidence"""
    WEB_SOURCE = "web_source"
    ACADEMIC_PAPER = "academic_paper"
    BOOK = "book"
    INTERVIEW = "interview"
    SURVEY = "survey"
    EXPERT_OPINION = "expert_opinion"
    DOCUMENTATION = "documentation"
    DATA_ANALYSIS = "data_analysis"
    EXPERIMENTAL = "experimental"
    CASE_STUDY = "case_study"
    OTHER = "other"


class EvidenceQuality(str, Enum):
    """Evidence quality ratings"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNVERIFIED = "unverified"


class EvidenceStatus(str, Enum):
    """Evidence processing status"""
    COLLECTED = "collected"
    ANALYZED = "analyzed"
    VERIFIED = "verified"
    INTEGRATED = "integrated"
    REJECTED = "rejected"


class EvidenceRelation(str, Enum):
    """Types of relationships between evidence items"""
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    EXTENDS = "extends"
    CLARIFIES = "clarifies"
    DEPENDS_ON = "depends_on"
    COMPLEMENTS = "complements"
    DUPLICATES = "duplicates"


@dataclass
class EvidenceItem:
    """Individual evidence item"""
    id: str
    content: str
    source: str
    evidence_type: EvidenceType
    quality: EvidenceQuality
    status: EvidenceStatus
    collected_by: str  # Agent or user who collected it
    collection_date: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    related_evidence: Set[str] = field(default_factory=set)
    confidence_score: float = 0.0
    relevance_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "evidence_type": self.evidence_type,
            "quality": self.quality,
            "status": self.status,
            "collected_by": self.collected_by,
            "collection_date": self.collection_date.isoformat(),
            "metadata": self.metadata,
            "tags": list(self.tags),
            "related_evidence": list(self.related_evidence),
            "confidence_score": self.confidence_score,
            "relevance_score": self.relevance_score
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceItem":
        """Create from dictionary representation"""
        return cls(
            id=data["id"],
            content=data["content"],
            source=data["source"],
            evidence_type=EvidenceType(data["evidence_type"]),
            quality=EvidenceQuality(data["quality"]),
            status=EvidenceStatus(data["status"]),
            collected_by=data["collected_by"],
            collection_date=datetime.fromisoformat(data["collection_date"]),
            metadata=data.get("metadata", {}),
            tags=set(data.get("tags", [])),
            related_evidence=set(data.get("related_evidence", [])),
            confidence_score=data.get("confidence_score", 0.0),
            relevance_score=data.get("relevance_score", 0.0)
        )


class EvidenceChain(BaseModel):
    """Evidence chain model for managing collections of evidence"""

    id: str = Field(description="Unique identifier for the evidence chain")
    plan_id: str = Field(description="Associated research plan ID")
    title: str = Field(description="Title of the evidence chain")
    description: str = Field(description="Description of the evidence chain")
    evidence_items: List[Dict[str, Any]] = Field(default_factory=list, description="List of evidence items")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
    created_by: str = Field(description="User who created the evidence chain")
    status: str = Field(default="active", description="Evidence chain status")

    # Analysis results
    synthesis_summary: Optional[str] = Field(default=None, description="Synthesis of all evidence")
    key_findings: List[str] = Field(default_factory=list, description="Key findings from evidence")
    confidence_level: float = Field(default=0.0, description="Overall confidence in evidence chain")
    quality_score: float = Field(default=0.0, description="Overall quality score")

    # Relationships and patterns
    evidence_relationships: List[Dict[str, Any]] = Field(default_factory=list, description="Relationships between evidence items")
    thematic_groups: List[Dict[str, Any]] = Field(default_factory=list, description="Thematic groupings of evidence")

    class Config:
        from_attributes = True


class EvidenceChainManager:
    """Manages evidence collection, analysis, and synthesis"""

    def __init__(self, plan_id: str):
        """
        Initialize evidence chain manager

        Args:
            plan_id: Associated research plan ID
        """
        self.plan_id = plan_id
        self.evidence_chain = EvidenceChain(
            id=f"chain_{uuid.uuid4().hex[:8]}",
            plan_id=plan_id,
            title=f"Evidence Chain for Plan {plan_id}",
            description="Systematically collected and analyzed evidence"
        )

        self.evidence_index: Dict[str, EvidenceItem] = {}
        self.analysis_cache: Dict[str, Any] = {}

    async def add_evidence(
        self,
        content: str,
        source: str,
        evidence_type: str,
        collected_by: str,
        quality: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Add evidence to the chain

        Args:
            content: Evidence content
            source: Source of evidence
            evidence_type: Type of evidence
            collected_by: Who collected the evidence
            quality: Quality rating
            metadata: Additional metadata
            tags: Tags for categorization

        Returns:
            Evidence ID
        """
        evidence_id = f"ev_{uuid.uuid4().hex[:8]}"

        evidence_item = EvidenceItem(
            id=evidence_id,
            content=content,
            source=source,
            evidence_type=EvidenceType(evidence_type.lower()),
            quality=EvidenceQuality(quality or EvidenceType.MEDIUM),
            status=EvidenceStatus.COLLECTED,
            collected_by=collected_by,
            collection_date=datetime.now(),
            metadata=metadata or {},
            tags=set(tags or []),
            related_evidence=set(),
            confidence_score=0.0,
            relevance_score=0.0
        )

        # Analyze evidence
        await self._analyze_evidence(evidence_item)

        # Store evidence
        self.evidence_index[evidence_id] = evidence_item
        self.evidence_chain.evidence_items.append(evidence_item.to_dict())

        # Update chain
        self.evidence_chain.updated_at = datetime.now()
        await self._update_chain_analysis()

        return evidence_id

    async def _analyze_evidence(self, evidence: EvidenceItem) -> None:
        """Analyze individual evidence item"""
        # Calculate relevance score based on content analysis
        evidence.relevance_score = await self._calculate_relevance_score(evidence)

        # Calculate confidence score based on source and quality
        evidence.confidence_score = await self._calculate_confidence_score(evidence)

        # Update status
        evidence.status = EvidenceStatus.ANALYZED

    async def _calculate_relevance_score(self, evidence: EvidenceItem) -> float:
        """Calculate relevance score for evidence"""
        score = 0.5  # Base score

        # Length and detail score
        content_length = len(evidence.content)
        if content_length > 500:
            score += 0.2
        elif content_length > 200:
            score += 0.1

        # Keyword relevance (simplified)
        relevant_keywords = [
            "research", "study", "analysis", "data", "finding", "result",
            "evidence", "conclusion", "insight", "information", "fact"
        ]

        keyword_count = sum(
            1 for keyword in relevant_keywords
            if keyword.lower() in evidence.content.lower()
        )
        score += min(keyword_count * 0.05, 0.3)

        return min(score, 1.0)

    async def _calculate_confidence_score(self, evidence: EvidenceItem) -> float:
        """Calculate confidence score for evidence"""
        score = 0.5  # Base score

        # Quality-based scoring
        if evidence.quality == EvidenceQuality.HIGH:
            score += 0.3
        elif evidence.quality == EvidenceQuality.MEDIUM:
            score += 0.1

        # Source-based scoring
        if evidence.evidence_type in [EvidenceType.ACADEMIC_PAPER, EvidenceType.BOOK]:
            score += 0.2
        elif evidence.evidence_type in [EvidenceType.WEB_SOURCE, EvidenceType.DOCUMENTATION]:
            score += 0.1

        return min(score, 1.0)

    async def _update_chain_analysis(self) -> None:
        """Update overall chain analysis"""
        if not self.evidence_chain.evidence_items:
            return

        # Calculate overall scores
        total_confidence = sum(item.get("confidence_score", 0) for item in self.evidence_chain.evidence_items)
        total_relevance = sum(item.get("relevance_score", 0) for item in self.evidence_chain.evidence_items)

        count = len(self.evidence_chain.evidence_items)
        self.evidence_chain.confidence_level = total_confidence / count if count > 0 else 0
        self.evidence_chain.quality_score = total_relevance / count if count > 0 else 0

        # Identify relationships between evidence
        await self._identify_evidence_relationships()

        # Generate synthesis
        await self._generate_synthesis()

    async def _identify_evidence_relationships(self) -> None:
        """Identify relationships between evidence items"""
        relationships = []

        for i, item1 in enumerate(self.evidence_chain.evidence_items):
            for j, item2 in enumerate(self.evidence_chain.evidence_items):
                if i >= j:  # Avoid duplicates
                    continue

                relation = await self._determine_relationship(item1, item2)
                if relation:
                    relationships.append({
                        "evidence_1": item1["id"],
                        "evidence_2": item2["id"],
                        "relationship_type": relation,
                        "confidence": 0.7  # Default confidence for relationships
                    })

        self.evidence_chain.evidence_relationships = relationships

    async def _determine_relationship(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> Optional[str]:
        """Determine relationship between two evidence items"""
        content1 = item1["content"].lower()
        content2 = item2["content"].lower()

        # Check for supporting evidence
        if self._is_supporting(content1, content2) or self._is_supporting(content2, content1):
            return EvidenceRelation.SUPPORTS.value

        # Check for contradictory evidence
        if self._is_contradictory(content1, content2):
            return EvidenceRelation.CONTRADICTS.value

        # Check for extension
        if self._is_extension(content1, content2) or self._is_extension(content2, content1):
            return EvidenceRelation.EXTENDS.value

        # Check for clarification
        if self._is_clarification(content1, content2) or self._is_clarification(content2, content1):
            return EvidenceRelation.CLARIFIES.value

        return None

    def _is_supporting(self, content1: str, content2: str) -> bool:
        """Check if content1 supports content2"""
        # Simplified check - in practice this would use more sophisticated NLP
        return any(word in content2 for word in content1.split() if len(word) > 3)

    def _is_contradictory(self, content1: str, content2: str) -> bool:
        """Check if content contradicts content2"""
        contradictory_pairs = [
            ("increase", "decrease"),
            ("improve", "worsen"),
            ("support", "oppose"),
            ("beneficial", "harmful"),
            ("effective", "ineffective"),
            ("success", "failure"),
            ("advantage", "disadvantage")
        ]

        for word1, word2 in contradictory_pairs:
            if word1 in content1 and word2 in content2:
                return True
            if word2 in content1 and word1 in content2:
                return True

        return False

    def _is_extension(self, content1: str, content2: str) -> bool:
        """Check if content1 extends content2"""
        # Simplified check
        return len(content1) > len(content2) and content2 in content1

    def _is_clarification(self, content1: str, content2: str) -> bool:
        """Check if content1 clarifies content2"""
        clarification_indicators = ["specifically", "particularly", "for example", "such as", "meaning"]
        return any(indicator in content1 for indicator in clarification_indicators)

    async def _generate_synthesis(self) -> None:
        """Generate synthesis of all evidence"""
        if not self.evidence_chain.evidence_items:
            return

        # Sort evidence by relevance and confidence
        sorted_evidence = sorted(
            self.evidence_chain.evidence_items,
            key=lambda x: (x.get("relevance_score", 0) + x.get("confidence_score", 0)) / 2,
            reverse=True
        )

        # Extract key findings
        key_findings = []
        for item in sorted_evidence[:10]:  # Top 10 most relevant items
            if item.get("relevance_score", 0) > 0.6:
                # Extract key sentences (simplified)
                sentences = item["content"].split('.')
                for sentence in sentences:
                    if len(sentence.strip()) > 20:
                        key_findings.append(sentence.strip())

        self.evidence_chain.key_findings = key_findings[:5]  # Top 5 findings

        # Generate synthesis summary
        if key_findings:
            summary = f"Evidence synthesis based on {len(self.evidence_chain.evidence_items)} sources. "
            summary += f"Key findings include: {'; '.join(key_findings[:3])}. "
            summary += f"Overall confidence level: {self.evidence_chain.confidence_level:.2f}. "
            summary += f"Evidence quality score: {self.evidence_chain.quality_score:.2f}."

            self.evidence_chain.synthesis_summary = summary

    async def get_evidence_by_type(self, evidence_type: str) -> List[Dict[str, Any]]:
        """Get evidence filtered by type"""
        return [
            item for item in self.evidence_chain.evidence_items
            if item.get("evidence_type") == evidence_type.lower()
        ]

    async def get_evidence_by_quality(self, quality: str) -> List[Dict[str, Any]]:
        """Get evidence filtered by quality"""
        return [
            item for item in self.evidence_chain.evidence_items
            if item.get("quality") == quality.lower()
        ]

    async def get_high_confidence_evidence(self) -> List[Dict[str, Any]]:
        """Get evidence with high confidence scores"""
        threshold = 0.7
        return [
            item for item in self.evidence_chain.evidence_items
            if item.get("confidence_score", 0) >= threshold
        ]

    async def get_evidence_summary(self) -> Dict[str, Any]:
        """Get comprehensive evidence summary"""
        return {
            "chain_id": self.evidence_chain.id,
            "total_evidence": len(self.evidence_evidence_items),
            "by_type": {
                evidence_type: len(await self.get_evidence_by_type(evidence_type))
                for evidence_type in set(item.get("evidence_type") for item in self.evidence_chain.evidence_items)
            },
            "by_quality": {
                quality: len(await self.get_evidence_by_quality(quality))
                for quality in set(item.get("quality") for item in self.evidence_chain.evidence_items)
            },
            "average_confidence": self.evidence_chain.confidence_level,
            "average_quality": self.evidence_chain.quality_score,
            "relationships_count": len(self.evidence_chain.evidence_relationships),
            "key_findings_count": len(self.evidence_chain.key_findings),
            "synthesis_available": self.evidence_chain.synthesis_summary is not None
        }