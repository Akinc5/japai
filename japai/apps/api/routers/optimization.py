from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from apps.api.agents import optimization as optimization_agent
from apps.api.core.brand_utils import get_or_resolve_brand
from apps.api.core.db import get_db
from apps.api.models import Brand, PerformanceInsight

router = APIRouter(prefix="/optimization", tags=["optimization"])

SIMULATED_NOTE = (
    "All engagement data in this system is fabricated seed data "
    "(analytics.is_simulated = true). No real performance data exists."
)


def _serialize(insight: PerformanceInsight) -> dict:
    return {
        "insight_id": insight.id,
        "brand_id": insight.brand_id,
        "insight_text": insight.insight_text,
        "insight_type": insight.insight_type,
        "supporting_metric": insight.supporting_metric,
        "recommendation": insight.recommendation,
        "derived_from": insight.derived_from,
        "generated_by_agent": insight.generated_by_agent,
        "created_at": insight.created_at,
    }


def _require_brand(db: Session, brand_id: Optional[str] = None) -> Brand:
    brand = get_or_resolve_brand(db, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.get("/aggregate")
def preview_aggregate(
    brand_id: Optional[str] = Query(None, description="Brand to aggregate performance for"),
    db: Session = Depends(get_db),
):
    """The deterministic aggregation, with ZERO LLM calls — exactly the table the
    model is shown by /analyze. Use it to check the numbers before spending quota."""
    brand = _require_brand(db, brand_id)
    aggregate = optimization_agent.aggregate_performance(db, brand.id)
    return {
        "brand_id": str(brand.id),
        "llm_calls": 0,
        "data_is_simulated": aggregate["analytics_are_simulated"],
        "simulated_note": SIMULATED_NOTE,
        **aggregate,
    }


@router.post("/analyze")
def analyze(
    brand_id: Optional[str] = Query(None, description="Brand to analyze"),
    limit: int = Query(4, ge=1, le=6, description="Max insights to produce"),
    db: Session = Depends(get_db),
):
    """Aggregates deterministically, then spends exactly one LLM call to turn the
    aggregate into insights. Replaces this brand's previous insights."""
    brand = _require_brand(db, brand_id)
    created = optimization_agent.generate_insights(db, brand.id, limit=limit)
    return {
        "brand_id": str(brand.id),
        "llm_calls": 1,
        "data_is_simulated": True,
        "simulated_note": SIMULATED_NOTE,
        "generated": [_serialize(i) for i in created],
    }


@router.get("/insights")
def list_insights(
    brand_id: Optional[str] = Query(None, description="Brand to list insights for"),
    db: Session = Depends(get_db),
):
    brand = _require_brand(db, brand_id)
    rows = (
        db.query(PerformanceInsight)
        .filter(PerformanceInsight.brand_id == brand.id)
        .order_by(PerformanceInsight.created_at.desc())
        .all()
    )
    return {
        "brand_id": str(brand.id),
        "count": len(rows),
        "data_is_simulated": True,
        "simulated_note": SIMULATED_NOTE,
        "insights": [_serialize(i) for i in rows],
    }
