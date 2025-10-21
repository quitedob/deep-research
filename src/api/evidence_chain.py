# -*- coding: utf-8 -*-
"""
Evidence Chain API Endpoints for Deep Research Platform
Handles evidence collection, analysis, and chain management API calls
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..core.research.evidence_chain import EvidenceChainManager, EvidenceType, EvidenceQuality
from ..core.database import get_db
from ..core.security import get_current_user

router = APIRouter(prefix="/api/evidence-chains", tags=["evidence-chains"])

# Global evidence managers (in production, these would be properly managed)
_evidence_managers = {}

def get_evidence_manager(plan_id: str) -> EvidenceChainManager:
    """Get or create an evidence manager for a specific plan"""
    if plan_id not in _evidence_managers:
        _evidence_managers[plan_id] = EvidenceChainManager(plan_id)
    return _evidence_managers[plan_id]

# Evidence Chain Management Endpoints

@router.post("")
async def create_evidence_chain(
    chain_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new evidence chain"""
    try:
        plan_id = chain_data.get("plan_id")
        if not plan_id:
            raise HTTPException(status_code=400, detail="plan_id is required")

        evidence_manager = get_evidence_manager(plan_id)
        chain = evidence_manager.evidence_chain

        # Update chain metadata
        if "title" in chain_data:
            chain.title = chain_data["title"]
        if "description" in chain_data:
            chain.description = chain_data["description"]
        if "created_by" in chain_data:
            chain.created_by = chain_data["created_by"]

        return {
            "success": True,
            "chain": chain.to_dict(),
            "message": "Evidence chain created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create evidence chain: {str(e)}")

@router.get("/{chain_id}")
async def get_evidence_chain(
    chain_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get an evidence chain by ID"""
    try:
        # Find the evidence manager for this chain
        evidence_manager = None
        for manager in _evidence_managers.values():
            if manager.evidence_chain.id == chain_id:
                evidence_manager = manager
                break

        if not evidence_manager:
            raise HTTPException(status_code=404, detail="Evidence chain not found")

        return {
            "success": True,
            "chain": evidence_manager.evidence_chain.to_dict(),
            "message": "Evidence chain retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get evidence chain: {str(e)}")

@router.get("/plan/{plan_id}")
async def get_evidence_chain_by_plan(
    plan_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get evidence chain by plan ID"""
    try:
        evidence_manager = get_evidence_manager(plan_id)

        return {
            "success": True,
            "chain": evidence_manager.evidence_chain.to_dict(),
            "message": "Evidence chain retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get evidence chain: {str(e)}")

@router.put("/{chain_id}")
async def update_evidence_chain(
    chain_id: str,
    update_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an evidence chain"""
    try:
        # Find the evidence manager for this chain
        evidence_manager = None
        for manager in _evidence_managers.values():
            if manager.evidence_chain.id == chain_id:
                evidence_manager = manager
                break

        if not evidence_manager:
            raise HTTPException(status_code=404, detail="Evidence chain not found")

        chain = evidence_manager.evidence_chain

        # Update chain properties
        if "title" in update_data:
            chain.title = update_data["title"]
        if "description" in update_data:
            chain.description = update_data["description"]
        if "status" in update_data:
            chain.status = update_data["status"]

        chain.updated_at = datetime.now()

        return {
            "success": True,
            "chain": chain.to_dict(),
            "message": "Evidence chain updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update evidence chain: {str(e)}")

@router.delete("/{chain_id}")
async def delete_evidence_chain(
    chain_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an evidence chain"""
    try:
        # Find and remove the evidence manager
        plan_id_to_remove = None
        for plan_id, manager in _evidence_managers.items():
            if manager.evidence_chain.id == chain_id:
                plan_id_to_remove = plan_id
                break

        if plan_id_to_remove:
            del _evidence_managers[plan_id_to_remove]
            return {
                "success": True,
                "message": "Evidence chain deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Evidence chain not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete evidence chain: {str(e)}")

# Evidence Management Endpoints

@router.post("/{chain_id}/evidence")
async def add_evidence(
    chain_id: str,
    evidence_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add evidence to an evidence chain"""
    try:
        # Find the evidence manager for this chain
        evidence_manager = None
        for manager in _evidence_managers.values():
            if manager.evidence_chain.id == chain_id:
                evidence_manager = manager
                break

        if not evidence_manager:
            raise HTTPException(status_code=404, detail="Evidence chain not found")

        evidence_id = await evidence_manager.add_evidence(
            content=evidence_data.get("content", ""),
            source=evidence_data.get("source", ""),
            evidence_type=evidence_data.get("evidence_type", "other"),
            collected_by=current_user["id"],
            quality=evidence_data.get("quality", "medium"),
            metadata=evidence_data.get("metadata", {}),
            tags=evidence_data.get("tags", [])
        )

        evidence_item = evidence_manager.evidence_index.get(evidence_id)

        return {
            "success": True,
            "evidence_id": evidence_id,
            "evidence": evidence_item.to_dict() if evidence_item else None,
            "message": "Evidence added successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add evidence: {str(e)}")

@router.get("/{chain_id}/evidence")
async def get_evidence_list(
    chain_id: str,
    evidence_type: Optional[str] = None,
    quality: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get evidence list from an evidence chain"""
    try:
        # Find the evidence manager for this chain
        evidence_manager = None
        for manager in _evidence_managers.values():
            if manager.evidence_chain.id == chain_id:
                evidence_manager = manager
                break

        if not evidence_manager:
            raise HTTPException(status_code=404, detail="Evidence chain not found")

        # Filter evidence
        evidence_list = evidence_manager.evidence_chain.evidence_items

        if evidence_type:
            evidence_list = [e for e in evidence_list if e.get("evidence_type") == evidence_type]

        if quality:
            evidence_list = [e for e in evidence_list if e.get("quality") == quality]

        # Apply limit
        if limit > 0:
            evidence_list = evidence_list[:limit]

        return {
            "success": True,
            "evidence": evidence_list,
            "count": len(evidence_list),
            "message": "Evidence retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get evidence: {str(e)}")

@router.get("/{chain_id}/evidence/{evidence_id}")
async def get_evidence_details(
    chain_id: str,
    evidence_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about specific evidence"""
    try:
        # Find the evidence manager for this chain
        evidence_manager = None
        for manager in _evidence_managers.values():
            if manager.evidence_chain.id == chain_id:
                evidence_manager = manager
                break

        if not evidence_manager:
            raise HTTPException(status_code=404, detail="Evidence chain not found")

        evidence_item = evidence_manager.evidence_index.get(evidence_id)
        if not evidence_item:
            raise HTTPException(status_code=404, detail="Evidence not found")

        return {
            "success": True,
            "evidence": evidence_item.to_dict(),
            "message": "Evidence details retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get evidence details: {str(e)}")

@router.put("/{chain_id}/evidence/{evidence_id}")
async def update_evidence(
    chain_id: str,
    evidence_id: str,
    update_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update evidence details"""
    try:
        # Find the evidence manager for this chain
        evidence_manager = None
        for manager in _evidence_managers.values():
            if manager.evidence_chain.id == chain_id:
                evidence_manager = manager
                break

        if not evidence_manager:
            raise HTTPException(status_code=404, detail="Evidence chain not found")

        evidence_item = evidence_manager.evidence_index.get(evidence_id)
        if not evidence_item:
            raise HTTPException(status_code=404, detail="Evidence not found")

        # Update evidence properties
        if "content" in update_data:
            evidence_item.content = update_data["content"]
        if "source" in update_data:
            evidence_item.source = update_data["source"]
        if "evidence_type" in update_data:
            evidence_item.evidence_type = EvidenceType(update_data["evidence_type"])
        if "quality" in update_data:
            evidence_item.quality = EvidenceQuality(update_data["quality"])
        if "metadata" in update_data:
            evidence_item.metadata.update(update_data["metadata"])
        if "tags" in update_data:
            evidence_item.tags = set(update_data["tags"])

        # Re-analyze evidence
        await evidence_manager._analyze_evidence(evidence_item)
        await evidence_manager._update_chain_analysis()

        return {
            "success": True,
            "evidence": evidence_item.to_dict(),
            "message": "Evidence updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update evidence: {str(e)}")

@router.delete("/{chain_id}/evidence/{evidence_id}")
async def delete_evidence(
    chain_id: str,
    evidence_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete evidence from an evidence chain"""
    try:
        # Find the evidence manager for this chain
        evidence_manager = None
        for manager in _evidence_managers.values():
            if manager.evidence_chain.id == chain_id:
                evidence_manager = manager
                break

        if not evidence_manager:
            raise HTTPException(status_code=404, detail="Evidence chain not found")

        if evidence_id not in evidence_manager.evidence_index:
            raise HTTPException(status_code=404, detail="Evidence not found")

        # Remove evidence
        del evidence_manager.evidence_index[evidence_id]
        evidence_manager.evidence_chain.evidence_items = [
            e for e in evidence_manager.evidence_chain.evidence_items
            if e.get("id") != evidence_id
        ]

        # Update chain analysis
        await evidence_manager._update_chain_analysis()

        return {
            "success": True,
            "message": "Evidence deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete evidence: {str(e)}")

# Analysis and Synthesis Endpoints

@router.post("/{chain_id}/analyze")
async def analyze_evidence_chain(
    chain_id: str,
    analysis_config: Dict[str, Any] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze an evidence chain"""
    try:
        # Find the evidence manager for this chain
        evidence_manager = None
        for manager in _evidence_managers.values():
            if manager.evidence_chain.id == chain_id:
                evidence_manager = manager
                break

        if not evidence_manager:
            raise HTTPException(status_code=404, detail="Evidence chain not found")

        # Trigger comprehensive analysis
        await evidence_manager._update_chain_analysis()

        analysis = {
            "synthesis_summary": evidence_manager.evidence_chain.synthesis_summary,
            "key_findings": evidence_manager.evidence_chain.key_findings,
            "confidence_level": evidence_manager.evidence_chain.confidence_level,
            "quality_score": evidence_manager.evidence_chain.quality_score,
            "relationships_count": len(evidence_manager.evidence_chain.evidence_relationships),
            "evidence_summary": await evidence_manager.get_evidence_summary()
        }

        return {
            "success": True,
            "analysis": analysis,
            "chain": evidence_manager.evidence_chain.to_dict(),
            "message": "Evidence chain analysis completed"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze evidence chain: {str(e)}")

@router.get("/{chain_id}/summary")
async def get_evidence_summary(
    chain_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get evidence chain summary"""
    try:
        # Find the evidence manager for this chain
        evidence_manager = None
        for manager in _evidence_managers.values():
            if manager.evidence_chain.id == chain_id:
                evidence_manager = manager
                break

        if not evidence_manager:
            raise HTTPException(status_code=404, detail="Evidence chain not found")

        summary = await evidence_manager.get_evidence_summary()

        return {
            "success": True,
            "summary": summary,
            "message": "Evidence summary retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get evidence summary: {str(e)}")

@router.get("/{chain_id}/relationships")
async def get_evidence_relationships(
    chain_id: str,
    relationship_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get evidence relationships"""
    try:
        # Find the evidence manager for this chain
        evidence_manager = None
        for manager in _evidence_managers.values():
            if manager.evidence_chain.id == chain_id:
                evidence_manager = manager
                break

        if not evidence_manager:
            raise HTTPException(status_code=404, detail="Evidence chain not found")

        relationships = evidence_manager.evidence_chain.evidence_relationships

        if relationship_type:
            relationships = [
                r for r in relationships
                if r.get("relationship_type") == relationship_type
            ]

        return {
            "success": True,
            "relationships": relationships,
            "count": len(relationships),
            "message": "Evidence relationships retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get evidence relationships: {str(e)}")

@router.get("/{chain_id}/themes")
async def get_evidence_themes(
    chain_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get thematic analysis of evidence"""
    try:
        # Find the evidence manager for this chain
        evidence_manager = None
        for manager in _evidence_managers.values():
            if manager.evidence_chain.id == chain_id:
                evidence_manager = manager
                break

        if not evidence_manager:
            raise HTTPException(status_code=404, detail="Evidence chain not found")

        # Analyze themes (mock implementation)
        evidence_items = evidence_manager.evidence_chain.evidence_items
        themes = []

        # Group evidence by content similarity (simplified)
        theme_groups = {}
        for item in evidence_items:
            content_words = item.get("content", "").lower().split()[:5]  # First 5 words as theme key
            theme_key = "_".join(content_words[:3]) if content_words else "general"

            if theme_key not in theme_groups:
                theme_groups[theme_key] = {
                    "name": " ".join(content_words[:3]).title(),
                    "evidence_count": 0,
                    "evidence_ids": [],
                    "avg_confidence": 0.0,
                    "avg_quality": "medium"
                }

            theme_groups[theme_key]["evidence_count"] += 1
            theme_groups[theme_key]["evidence_ids"].append(item.get("id"))
            theme_groups[theme_key]["avg_confidence"] += item.get("confidence_score", 0.5)

        # Calculate averages and convert to list
        for theme in theme_groups.values():
            if theme["evidence_count"] > 0:
                theme["avg_confidence"] /= theme["evidence_count"]
            themes.append(theme)

        # Sort by evidence count
        themes.sort(key=lambda x: x["evidence_count"], reverse=True)

        return {
            "success": True,
            "themes": themes[:10],  # Top 10 themes
            "count": len(themes),
            "message": "Evidence themes retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get evidence themes: {str(e)}")

# Export Endpoints

@router.get("/{chain_id}/export")
async def export_evidence_chain(
    chain_id: str,
    format: str = "json",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export evidence chain"""
    try:
        # Find the evidence manager for this chain
        evidence_manager = None
        for manager in _evidence_managers.values():
            if manager.evidence_chain.id == chain_id:
                evidence_manager = manager
                break

        if not evidence_manager:
            raise HTTPException(status_code=404, detail="Evidence chain not found")

        chain_data = {
            "chain": evidence_manager.evidence_chain.to_dict(),
            "evidence_items": [
                evidence_manager.evidence_index[eid].to_dict()
                for eid in evidence_manager.evidence_index
            ],
            "export_date": datetime.now().isoformat(),
            "exported_by": current_user["id"]
        }

        if format.lower() == "json":
            return {
                "success": True,
                "data": chain_data,
                "format": "json",
                "message": "Evidence chain exported successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export evidence chain: {str(e)}")