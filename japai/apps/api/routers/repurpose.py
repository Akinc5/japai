from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api.agents import compliance as compliance_agent
from apps.api.agents import repurpose as repurpose_agent
from apps.api.core.db import get_db
from apps.api.models import Brand, Campaign, ContentAsset, ContentVersion

router = APIRouter(prefix="/repurpose", tags=["repurpose"])


class RepurposeRequest(BaseModel):
    source_text: str = Field(..., min_length=20, description="The educational text, masterclass article, or policy whitepaper.")
    brand_slug: str = Field(default="jade", description="Target brand slug (jade, ja-assure, doctor-shield)")
    title: Optional[str] = Field(default=None, description="Optional title or topic")


class SaveToQueueRequest(BaseModel):
    brand_slug: str
    asset_type: str = "social_post"
    platform: str = "linkedin"
    content_text: str
    title: Optional[str] = "Repurposed Masterclass Content"


@router.get("/templates")
def list_templates():
    """Returns curated InsurTech 101 masterclasses and educational whitepapers ready for 1-click repurposing."""
    return {
        "templates": repurpose_agent.get_masterclass_templates()
    }


@router.post("/generate")
def generate_repurposed_content(
    req: RepurposeRequest,
    db: Session = Depends(get_db)
):
    """Repurposes educational insurance whitepapers / masterclasses into a full multi-channel nurture kit."""
    if not req.source_text.strip():
        raise HTTPException(status_code=400, detail="Source text cannot be empty")
    
    result = repurpose_agent.repurpose_document(
        db=db,
        source_text=req.source_text,
        brand_slug=req.brand_slug,
        title=req.title,
    )
    return result


@router.post("/save-to-queue")
def save_repurposed_asset_to_queue(
    req: SaveToQueueRequest,
    db: Session = Depends(get_db)
):
    """Pushes a chosen repurposed asset directly into the Compliance Review Queue."""
    brand = db.query(Brand).filter(Brand.slug == req.brand_slug).first()
    if not brand:
        brand = db.query(Brand).first()

    # Find or create a Masterclass Nurture Campaign
    campaign = db.query(Campaign).filter(
        Campaign.brand_id == brand.id,
        Campaign.name == "Insurtech 101 Masterclass Series"
    ).first()

    if not campaign:
        campaign = Campaign(
            brand_id=brand.id,
            name="Insurtech 101 Masterclass Series",
            objective="Educational Nurture & Authority Building",
            brief="Repurposed high-value insurance educational articles, whitepapers, and masterclasses into compliance-gated multi-channel assets.",
            target_audience="Industry B2B Decision Makers & Commercial Policyholders",
            status="active",
        )
        db.add(campaign)
        db.flush()

    asset = ContentAsset(
        brand_id=brand.id,
        campaign_id=campaign.id,
        asset_type=req.asset_type,
        platform=req.platform,
        status="pending_review",
        origin="agent",
    )
    db.add(asset)
    db.flush()

    version = ContentVersion(
        asset_id=asset.id,
        version_number=1,
        content_text=req.content_text,
        language="en",
    )
    db.add(version)
    db.flush()

    # Run compliance check
    review = compliance_agent.run_compliance_check(
        db=db,
        brand_id=brand.id,
        text=req.content_text,
    )
    # Store review linked to version
    db_review = compliance_agent.store_compliance_review(
        db=db,
        version_id=version.id,
        review_result=review,
    )
    db.commit()

    return {
        "status": "success",
        "asset_id": str(asset.id),
        "version_id": str(version.id),
        "compliance_outcome": review.outcome,
        "message": "Asset successfully submitted to Compliance Review Queue!"
    }
