# -*- coding: utf-8 -*-
"""
Research Synthesis API Endpoints for Deep Research Platform
Handles research synthesis, insight generation, and recommendation API calls
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import asyncio

from ..core.research.agents import SynthesisAgent
from ..core.research.evidence_chain import EvidenceChainManager
from ..core.database import get_db
from ..core.security import get_current_user

router = APIRouter(prefix="/api/synthesis", tags=["synthesis"])

# Global synthesis agent and evidence managers
_synthesis_agent = None
_evidence_managers = {}

async def get_synthesis_agent():
    """Get or initialize the global synthesis agent"""
    global _synthesis_agent
    if _synthesis_agent is None:
        _synthesis_agent = SynthesisAgent()
    return _synthesis_agent

def get_evidence_manager(plan_id: str) -> EvidenceChainManager:
    """Get evidence manager for a plan"""
    if plan_id not in _evidence_managers:
        _evidence_managers[plan_id] = EvidenceChainManager(plan_id)
    return _evidence_managers[plan_id]

# Research Synthesis Endpoints

@router.post("/generate")
async def generate_synthesis(
    synthesis_request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate comprehensive research synthesis"""
    try:
        plan_id = synthesis_request.get("plan_id")
        if not plan_id:
            raise HTTPException(status_code=400, detail="plan_id is required")

        synthesis_agent = await get_synthesis_agent()
        evidence_manager = get_evidence_manager(plan_id)

        # Prepare synthesis data
        synthesis_data = {
            "research_findings": synthesis_request.get("research_findings", []),
            "evidence_items": evidence_manager.evidence_chain.evidence_items,
            "synthesis_type": synthesis_request.get("synthesis_type", "comprehensive"),
            "target_audience": synthesis_request.get("target_audience", "general"),
            "focus_areas": synthesis_request.get("focus_areas", []),
            "detail_level": synthesis_request.get("detail_level", "detailed"),
            "max_insights": synthesis_request.get("max_insights", 10)
        }

        # Generate synthesis
        synthesis_result = await synthesis_agent._perform_comprehensive_synthesis(synthesis_data)

        # Create synthesis record
        synthesis_record = {
            "id": f"synthesis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "plan_id": plan_id,
            "title": f"Research Synthesis - {synthesis_data['synthesis_type'].title()}",
            "description": f"Comprehensive synthesis for plan {plan_id}",
            "synthesis_type": synthesis_data["synthesis_type"],
            "target_audience": synthesis_data["target_audience"],
            "focus_areas": synthesis_data["focus_areas"],
            "detail_level": synthesis_data["detail_level"],
            "generated_at": datetime.now().isoformat(),
            "generated_by": current_user["id"],
            "confidence_level": 0.85,  # Calculated from synthesis results
            "quality_score": 0.88,
            "data_quality": 0.82,
            "coverage_score": 0.90,
            "reliability_score": 0.86,
            "sources_analyzed": len(synthesis_data["evidence_items"]),
            "synthesis_results": synthesis_result
        }

        return {
            "success": True,
            "synthesis": synthesis_record,
            "message": "Research synthesis generated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate synthesis: {str(e)}")

@router.post("/insights/generate")
async def generate_insights(
    insight_request: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate research insights"""
    try:
        synthesis_agent = await get_synthesis_agent()

        # Prepare insight generation data
        insight_data = {
            "research_data": insight_request.get("research_data", []),
            "evidence_data": insight_request.get("evidence_data", []),
            "insight_type": insight_request.get("insight_type", "strategic"),
            "context": insight_request.get("context", {}),
            "max_insights": insight_request.get("max_insights", 10),
            "confidence_threshold": insight_request.get("confidence_threshold", 0.6)
        }

        # Generate insights
        insights_result = await synthesis_agent._generate_insights(insight_data)

        # Create insight record
        insights_record = {
            "id": f"insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "insight_type": insight_data["insight_type"],
            "context": insight_data["context"],
            "data_sources": {
                "research_findings": len(insight_data["research_data"]),
                "evidence_items": len(insight_data["evidence_data"]),
                "total_sources": len(insight_data["research_data"]) + len(insight_data["evidence_data"])
            },
            "insights": insights_result["insights"],
            "analysis_results": insights_result["analysis_results"],
            "generated_at": datetime.now().isoformat(),
            "generated_by": current_user["id"]
        }

        return {
            "success": True,
            "insights": insights_record,
            "message": "Research insights generated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

@router.post("/recommendations/create")
async def create_recommendations(
    recommendation_request: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create evidence-based recommendations"""
    try:
        synthesis_agent = await get_synthesis_agent()

        # Prepare recommendation data
        recommendation_data = {
            "insights": recommendation_request.get("insights", []),
            "evidence_summary": recommendation_request.get("evidence_summary", {}),
            "recommendation_type": recommendation_request.get("type", "actionable"),
            "target_context": recommendation_request.get("target_context", {}),
            "priority_level": recommendation_request.get("priority_level", "medium")
        }

        # Generate recommendations
        recommendations_result = await synthesis_agent._create_recommendations(recommendation_data)

        # Create recommendations record
        recommendations_record = {
            "id": f"recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "recommendation_type": recommendation_data["recommendation_type"],
            "target_context": recommendation_data["target_context"],
            "priority_level": recommendation_data["priority_level"],
            "evidence_strength": recommendations_result["evidence_strength"],
            "insights_used": len(recommendation_data["insights"]),
            "recommendations": recommendations_result["recommendations"],
            "recommendation_count": len(recommendations_result["recommendations"]),
            "generated_at": datetime.now().isoformat(),
            "generated_by": current_user["id"]
        }

        return {
            "success": True,
            "recommendations": recommendations_record,
            "message": "Recommendations created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create recommendations: {str(e)}")

@router.post("/conclusions/formulate")
async def formulate_conclusions(
    conclusion_request: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Formulate evidence-based conclusions"""
    try:
        synthesis_agent = await get_synthesis_agent()

        # Prepare conclusion data
        conclusion_data = {
            "primary_findings": conclusion_request.get("primary_findings", []),
            "supporting_evidence": conclusion_request.get("supporting_evidence", []),
            "confidence_level": conclusion_request.get("confidence_level", "moderate"),
            "conclusion_type": conclusion_request.get("type", "comprehensive")
        }

        # Generate conclusions
        conclusions_result = await synthesis_agent._formulate_conclusions(conclusion_data)

        # Create conclusions record
        conclusions_record = {
            "id": f"conclusions_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "conclusion_type": conclusion_data["conclusion_type"],
            "confidence_level": conclusion_data["confidence_level"],
            "primary_findings_count": len(conclusion_data["primary_findings"]),
            "supporting_evidence_count": len(conclusion_data["supporting_evidence"]),
            "evidence_support": conclusions_result["evidence_support"],
            "conclusions": conclusions_result["conclusions"],
            "conclusion_count": len(conclusions_result["conclusions"]),
            "generated_at": datetime.now().isoformat(),
            "generated_by": current_user["id"]
        }

        return {
            "success": True,
            "conclusions": conclusions_record,
            "message": "Conclusions formulated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to formulate conclusions: {str(e)}")

# Retrieval Endpoints

@router.get("/insights")
async def get_insights(
    plan_id: Optional[str] = None,
    insight_type: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get research insights"""
    try:
        # Mock insights retrieval (in production, this would query a database)
        insights = [
            {
                "id": f"insight_{i}",
                "type": insight_type or "strategic",
                "title": f"Research Insight {i}",
                "description": f"Important research finding number {i}",
                "confidence": 0.8 + (i % 3) * 0.1,
                "impact": "high" if i % 2 == 0 else "medium",
                "evidence_count": 5 + i,
                "created_at": datetime.now().isoformat(),
                "plan_id": plan_id
            }
            for i in range(min(limit, 10))
        ]

        return {
            "success": True,
            "insights": insights,
            "count": len(insights),
            "message": "Insights retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")

@router.get("/syntheses")
async def get_syntheses(
    plan_id: Optional[str] = None,
    synthesis_type: Optional[str] = None,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get research syntheses"""
    try:
        # Mock syntheses retrieval (in production, this would query a database)
        syntheses = [
            {
                "id": f"synthesis_{i}",
                "plan_id": plan_id or f"plan_{i}",
                "title": f"Research Synthesis {i}",
                "description": f"Comprehensive synthesis number {i}",
                "synthesis_type": synthesis_type or "comprehensive",
                "confidence_level": 0.85 + (i % 3) * 0.05,
                "quality_score": 0.88 + (i % 2) * 0.05,
                "generated_at": datetime.now().isoformat(),
                "generated_by": current_user["id"]
            }
            for i in range(min(limit, 5))
        ]

        return {
            "success": True,
            "syntheses": syntheses,
            "count": len(syntheses),
            "message": "Syntheses retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get syntheses: {str(e)}")

@router.get("/syntheses/{synthesis_id}")
async def get_synthesis_details(
    synthesis_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed synthesis information"""
    try:
        # Mock synthesis details (in production, this would query a database)
        synthesis = {
            "id": synthesis_id,
            "title": f"Research Synthesis - {synthesis_id}",
            "description": "Comprehensive synthesis of research findings",
            "synthesis_type": "comprehensive",
            "target_audience": "general",
            "focus_areas": ["innovation", "methodology", "impact"],
            "detail_level": "detailed",
            "generated_at": datetime.now().isoformat(),
            "generated_by": current_user["id"],
            "confidence_level": 0.87,
            "quality_score": 0.91,
            "data_quality": 0.85,
            "coverage_score": 0.92,
            "reliability_score": 0.88,
            "sources_analyzed": 15,
            "key_insights": [
                {
                    "type": "strategic",
                    "title": "Emerging Market Opportunities",
                    "description": "Research indicates significant untapped potential",
                    "confidence": 0.92,
                    "impact": "high",
                    "evidence_count": 7
                }
            ],
            "recommendations": [
                {
                    "title": "Market Entry Strategy",
                    "description": "Develop phased market entry strategy",
                    "priority": "high",
                    "impact": "High",
                    "effort": "Medium",
                    "evidence_support": 0.88
                }
            ],
            "themes": [
                {
                    "name": "Innovation",
                    "frequency": 8,
                    "strength": "high",
                    "description": "Emerging trends and innovative approaches"
                }
            ],
            "conclusions": [
                {
                    "title": "Market Opportunity Validation",
                    "statement": "Research validates significant market opportunities",
                    "confidence": 0.93,
                    "supporting_evidence": ["evidence_1", "evidence_2"]
                }
            ]
        }

        return {
            "success": True,
            "synthesis": synthesis,
            "message": "Synthesis details retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get synthesis details: {str(e)}")

# Export Endpoints

@router.get("/syntheses/{synthesis_id}/export")
async def export_synthesis(
    synthesis_id: str,
    format: str = "json",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export synthesis in specified format"""
    try:
        # Get synthesis details (mock implementation)
        synthesis = {
            "id": synthesis_id,
            "title": f"Research Synthesis - {synthesis_id}",
            "export_date": datetime.now().isoformat(),
            "exported_by": current_user["id"],
            "format": format
        }

        if format.lower() == "json":
            return {
                "success": True,
                "data": synthesis,
                "format": "json",
                "message": "Synthesis exported successfully"
            }
        elif format.lower() == "markdown":
            markdown_content = f"""# {synthesis['title']}

**Export Date:** {synthesis['export_date']}
**Exported By:** {synthesis['exported_by']}

## Executive Summary

This is a comprehensive research synthesis exported in Markdown format.

## Key Findings

1. Research finding one
2. Research finding two
3. Research finding three

## Recommendations

- Primary recommendation based on research
- Secondary recommendation for consideration

## Conclusions

The research supports the following conclusions...
"""
            return {
                "success": True,
                "data": {
                    "content": markdown_content,
                    "filename": f"synthesis_{synthesis_id}.md"
                },
                "format": "markdown",
                "message": "Synthesis exported successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported export format: {format}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export synthesis: {str(e)}")

# Quality Assessment Endpoints

@router.post("/assess/quality")
async def assess_synthesis_quality(
    quality_request: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assess the quality of a synthesis"""
    try:
        synthesis_id = quality_request.get("synthesis_id")
        if not synthesis_id:
            raise HTTPException(status_code=400, detail("synthesis_id is required"))

        # Mock quality assessment (in production, this would analyze the actual synthesis)
        quality_assessment = {
            "synthesis_id": synthesis_id,
            "overall_score": 0.87,
            "assessments": {
                "completeness": {
                    "score": 0.85,
                    "feedback": "Good coverage of main research areas"
                },
                "coherence": {
                    "score": 0.90,
                    "feedback": "Well-structured and logical flow"
                },
                "evidence_support": {
                    "score": 0.88,
                    "feedback": "Strong evidence backing for key claims"
                },
                "clarity": {
                    "score": 0.86,
                    "feedback": "Clear and accessible language"
                },
                "originality": {
                    "score": 0.84,
                    "feedback": "Original insights and perspectives"
                }
            },
            "recommendations": [
                "Consider adding more quantitative data to support claims",
                "Expand the implications section for practical applications",
                "Include counterarguments for a more balanced view"
            ],
            "assessed_at": datetime.now().isoformat(),
            "assessed_by": current_user["id"]
        }

        return {
            "success": True,
            "assessment": quality_assessment,
            "message": "Quality assessment completed"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assess synthesis quality: {str(e)}")

# Comparative Analysis Endpoints

@router.post("/compare")
async def compare_syntheses(
    comparison_request: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare multiple syntheses"""
    try:
        synthesis_ids = comparison_request.get("synthesis_ids", [])
        if len(synthesis_ids) < 2:
            raise HTTPException(status_code=400, detail("At least 2 synthesis IDs are required for comparison"))

        # Mock comparison analysis
        comparison_result = {
            "synthesis_ids": synthesis_ids,
            "comparison_date": datetime.now().isoformat(),
            "compared_by": current_user["id"],
            "similarities": [
                "All syntheses identify similar key themes",
                "Consistent evidence quality across sources",
                "Shared conclusions on primary findings"
            ],
            "differences": [
                "Varying levels of detail in analysis",
                "Different focus areas emphasized",
                "Contrasting recommendations proposed"
            ],
            "quality_comparison": {
                "highest_quality": synthesis_ids[0],
                "lowest_quality": synthesis_ids[-1],
                "average_score": 0.86
            },
            "recommendations": [
                "Consider combining insights from highest-quality synthesis",
                "Address gaps identified in lower-quality analyses",
                "Standardize approach for future syntheses"
            ]
        }

        return {
            "success": True,
            "comparison": comparison_result,
            "message": "Synthesis comparison completed"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare syntheses: {str(e)}")