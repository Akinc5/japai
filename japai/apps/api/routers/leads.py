from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from apps.api.agents import lead as lead_agent
from apps.api.agents.compliance import RISK_LEVEL_BY_OUTCOME
from apps.api.core.brand_utils import get_or_resolve_brand
from apps.api.core.db import get_db
from apps.api.models import Brand, ComplianceReview, ContentVersion, Lead

router = APIRouter(prefix="/leads", tags=["leads"])

# Leads written by the test suite are tagged so they never appear in the demo
# list — the same separation content_assets.origin provides for content.
DEMO_SOURCES = ("seed_data", "web_search")


def _outreach_state(db: Session, lead: Lead) -> dict | None:
    """Where this lead's outreach draft currently sits in the review flow."""
    if lead.outreach_content_version_id is None:
        return None
    drafted = db.get(ContentVersion, lead.outreach_content_version_id)
    if drafted is None:
        return None

    version = (
        db.query(ContentVersion)
        .filter(
            ContentVersion.content_asset_id == drafted.content_asset_id,
            ContentVersion.is_current.is_(True),
        )
        .first()
    ) or drafted

    review = (
        db.query(ComplianceReview)
        .filter(ComplianceReview.content_version_id == version.id)
        .order_by(ComplianceReview.reviewed_at.desc())
        .first()
    )
    return {
        "content_version_id": version.id,
        "drafted_content_version_id": drafted.id,
        "was_edited_by_reviewer": version.id != drafted.id,
        "status": version.status,
        "is_current": version.is_current,
        "body_preview": version.body[:200] if version.body else None,
        "risk_level": RISK_LEVEL_BY_OUTCOME.get(review.outcome, "review") if review else None,
        "compliance_outcome": review.outcome if review else None,
    }


def _serialize(db: Session, lead: Lead) -> dict:
    return {
        "lead_id": lead.id,
        "brand_id": lead.brand_id,
        "company_name": lead.company_name,
        "contact_name": lead.contact_name,
        "email": lead.email,
        "phone": lead.phone,
        "category": lead.category,
        "location": lead.location,
        "employee_count": lead.employee_count,
        "source": lead.source,
        "status": lead.status,
        "fit_score": float(lead.score) if lead.score is not None else None,
        "score_breakdown": lead.score_breakdown,
        "outreach": _outreach_state(db, lead),
        "created_at": lead.created_at,
    }


@router.post("/generate")
def generate(
    brand_id: Optional[str] = Query(None, description="Brand to source and score leads for"),
    draft_outreach: bool = Query(True, description="Also draft outreach for the top leads"),
    max_outreach: int = Query(3, ge=0, le=8, description="Cap on LLM calls (one per draft)"),
    db: Session = Depends(get_db),
):
    """Sources a synthetic prospect list, scores it deterministically, then spends
    one LLM call per drafted lead. Set draft_outreach=false for a zero-cost run."""
    brand = get_or_resolve_brand(db, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    result = lead_agent.generate_leads(
        db, brand.id, draft_outreach=draft_outreach, max_outreach=max_outreach
    )
    result["formula"] = lead_agent.SCORE_FORMULA
    result["scope_note"] = (
        "Prospect profiles are hand-authored synthetic seed data, not live-sourced "
        "businesses. See leads.source."
    )
    return result


@router.get("")
def list_leads(
    brand_id: Optional[str] = Query(None, description="Brand to list leads for"),
    db: Session = Depends(get_db),
):
    brand = get_or_resolve_brand(db, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    rows = (
        db.query(Lead)
        .filter(Lead.brand_id == brand.id, Lead.source.in_(DEMO_SOURCES))
        .order_by(Lead.score.desc().nullslast())
        .all()
    )
    return {
        "brand_id": str(brand.id),
        "formula": lead_agent.SCORE_FORMULA,
        "count": len(rows),
        "leads": [_serialize(db, lead) for lead in rows],
    }


@router.get("/scores")
def preview_scores(
    brand_id: UUID = Query(..., description="Brand to preview lead scoring for"),
    db: Session = Depends(get_db),
):
    """Runs the whole scoring pass with ZERO LLM calls and without writing to the
    database — useful for sanity-checking the formula before spending quota."""
    brand = db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    profiles = lead_agent.SEED_LEADS_BY_BRAND_SLUG.get(brand.slug)
    if not profiles:
        raise HTTPException(
            status_code=404,
            detail=f"No seed prospect dataset defined for brand '{brand.slug}'",
        )

    scored = [
        {"company_name": p["company_name"], **lead_agent.score_lead(p, brand)} for p in profiles
    ]
    scored.sort(key=lambda row: row["score"], reverse=True)
    return {
        "brand_id": brand_id,
        "formula": lead_agent.SCORE_FORMULA,
        "llm_calls": 0,
        "scored": scored,
    }


@router.get("/osm-live")
def search_live_singapore_leads(
    brand_id: UUID = Query(..., description="Brand to search live Singapore prospects for"),
    limit: int = Query(10, ge=1, le=30),
    db: Session = Depends(get_db),
):
    """Searches live commercial entities across Singapore via OpenStreetMap Overpass."""
    from apps.api.core import osm_client

    brand = db.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    live_results = osm_client.search_singapore_businesses(brand.slug, limit=limit)
    return {
        "brand_id": brand_id,
        "brand_name": brand.name,
        "brand_slug": brand.slug,
        "count": len(live_results),
        "source": "OpenStreetMap Overpass Live API (Singapore)",
        "results": live_results,
    }


@router.get("/{lead_id}")
def get_lead(lead_id: UUID, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return _serialize(db, lead)

