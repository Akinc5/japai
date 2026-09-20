from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api.agents import visual_studio
from apps.api.core.db import get_db
from apps.api.models import Brand

router = APIRouter(prefix="/visual", tags=["visual-studio"])


class VisualCreativeRequest(BaseModel):
    brand_slug: str
    topic: str
    platform: str = "instagram_carousel"


@router.post("/generate")
def generate_visual(
    req: VisualCreativeRequest,
    db: Session = Depends(get_db)
):
    """Generates brand-tailored image prompts (Midjourney/DALL-E) and 5-slide carousel breakdowns."""
    brand = db.query(Brand).filter(Brand.slug == req.brand_slug).first()
    brand_name = brand.name if brand else req.brand_slug.capitalize()

    creative = visual_studio.generate_visual_creative(
        brand_slug=req.brand_slug,
        topic=req.topic,
        platform=req.platform,
        db=db
    )

    return {
        "brand_slug": req.brand_slug,
        "brand_name": brand_name,
        "topic": req.topic,
        "platform": req.platform,
        "creative": creative
    }
