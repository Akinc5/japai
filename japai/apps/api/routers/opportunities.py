from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from apps.api.agents import opportunity as opportunity_agent
from apps.api.core.brand_utils import get_or_resolve_brand
from apps.api.core.db import get_db
from apps.api.models import Brand, ContentOpportunity

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


def _serialize(opportunity: ContentOpportunity) -> dict:
    return {
        "opportunity_id": opportunity.id,
        "brand_id": opportunity.brand_id,
        "title": opportunity.title,
        "rationale": opportunity.description,
        "opportunity_type": opportunity.opportunity_type,
        "score": float(opportunity.priority_score) if opportunity.priority_score is not None else None,
        "score_breakdown": opportunity.score_breakdown,
        "suggested_angle": opportunity.suggested_angle,
        "suggested_formats": opportunity.suggested_formats or [],
        "source_chunk_ids": opportunity.source_chunk_ids or [],
        "status": opportunity.status,
        "created_at": opportunity.created_at,
    }


@router.post("/generate")
def generate(
    brand_id: Optional[str] = Query(None, description="Brand to generate opportunities for"),
    limit: int = Query(3, ge=1, le=5, description="Max opportunities to write narratives for"),
    db: Session = Depends(get_db),
):
    """Scores every topic cluster deterministically, then spends one LLM call per
    candidate clearing the minimum score — not one per candidate overall."""
    brand = get_or_resolve_brand(db, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    try:
        created = opportunity_agent.generate_opportunities(db, brand.id, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "brand_id": str(brand.id),
        "min_score": opportunity_agent.MIN_SCORE,
        "formula": opportunity_agent.SCORE_FORMULA,
        "generated": [_serialize(o) for o in created],
    }


@router.get("")
def list_opportunities(
    brand_id: Optional[str] = Query(None, description="Brand to list opportunities for"),
    status: str = Query("suggested", description="Filter by status"),
    db: Session = Depends(get_db),
):
    brand = get_or_resolve_brand(db, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    rows = (
        db.query(ContentOpportunity)
        .filter(
            ContentOpportunity.brand_id == brand.id,
            ContentOpportunity.status == status,
        )
        .order_by(ContentOpportunity.priority_score.desc().nullslast())
        .all()
    )
    return [_serialize(o) for o in rows]


@router.get("/scores")
def preview_scores(
    brand_id: UUID = Query(..., description="Brand to score"),
    db: Session = Depends(get_db),
):
    """Deterministic scores for every cluster with no LLM calls — useful for
    inspecting the scoring layer without spending quota."""
    if db.get(Brand, brand_id) is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    return {
        "formula": opportunity_agent.SCORE_FORMULA,
        "min_score": opportunity_agent.MIN_SCORE,
        "clusters": opportunity_agent.score_all_clusters(db, brand_id),
    }
