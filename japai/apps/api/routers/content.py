from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from fastapi import Query

from apps.api.agents import compliance as compliance_agent
from apps.api.agents import content as content_agent
from apps.api.agents import localization as localization_agent
from apps.api.agents.compliance import RISK_LEVEL_BY_OUTCOME
from apps.api.core.db import get_db
from apps.api.models import Brand, ComplianceReview, ContentVersion

router = APIRouter(prefix="/content", tags=["content"])


class GenerateContentRequest(BaseModel):
    brand_id: UUID
    platform: str
    topic: str


def _compliance_payload(review: ComplianceReview | None) -> dict | None:
    if review is None:
        return None
    return {
        "id": review.id,
        "outcome": review.outcome,
        "risk_level": RISK_LEVEL_BY_OUTCOME.get(review.outcome, "review"),
        "reviewer_type": review.reviewer_type,
        "detected_issues": review.detected_issues or [],
        "reviewed_at": review.reviewed_at,
    }


@router.post("/generate")
def generate_content(payload: GenerateContentRequest, db: Session = Depends(get_db)):
    brand = db.get(Brand, payload.brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    version = content_agent.generate_content(
        db, brand_id=payload.brand_id, platform=payload.platform, topic=payload.topic
    )
    review = compliance_agent.run_compliance_check(db, version)

    metadata = version.version_metadata or {}
    return {
        "content_version_id": version.id,
        "content_asset_id": version.content_asset_id,
        "status": version.status,
        "body": version.body,
        "compliance": _compliance_payload(review),
        "debug": {
            "system_prompt": metadata.get("system_prompt"),
            "lessons_applied": metadata.get("lessons_applied", []),
            "insights_applied": metadata.get("insights_applied", []),
            "prompt_version": metadata.get("prompt_version"),
        },
    }


@router.post("/{content_version_id}/localize")
def localize(
    content_version_id: UUID,
    language: str = Query(..., description="Target language: zh-Hans, ms, or id"),
    db: Session = Depends(get_db),
):
    """Culturally adapt existing English content into one target language.

    Creates a sibling content_asset (not a new version of the English one), then
    runs the FULL compliance pipeline against it in its own language — an English
    pass grants the localized version nothing.
    """
    # A missing content_version is a not-found, not a bad request — the agent
    # raises ValueError for both, so disambiguate here to stay consistent with
    # every other endpoint's 404.
    if db.get(ContentVersion, content_version_id) is None:
        raise HTTPException(status_code=404, detail="Content version not found")

    version = localization_agent.localize_content_version(db, content_version_id, language)
    asset = version.content_asset
    review = (
        db.query(ComplianceReview)
        .filter(ComplianceReview.content_version_id == version.id)
        .order_by(ComplianceReview.reviewed_at.desc())
        .first()
    )
    spec = localization_agent.LANGUAGES.get(language, {})
    return {
        "content_version_id": version.id,
        "content_asset_id": asset.id,
        "language": asset.language,
        "language_name": spec.get("name"),
        "source_content_asset_id": asset.source_content_asset_id,
        "status": version.status,
        "body": version.body,
        "compliance": _compliance_payload(review),
        "note": (
            "Cultural adaptation, not translation. Compliance ran independently "
            "in the target language, including a language-specific blocklist."
        ),
    }


@router.get("/languages")
def list_languages():
    """Supported localization targets and what each adaptation optimises for."""
    return {
        "default": localization_agent.DEFAULT_LANGUAGE,
        "languages": [
            {
                "code": code,
                "name": spec["name"],
                "endonym": spec["endonym"],
                "market": spec["market"],
                "blocklist_terms": len(localization_agent.blocklist_for_language(code)),
            }
            for code, spec in localization_agent.LANGUAGES.items()
        ],
        "note": (
            "Non-English blocklists are demo-grade: short, category-matched to the "
            "approved English list, and NOT reviewed by a native speaker or "
            "compliance officer."
        ),
    }


@router.get("/{content_version_id}")
def get_content(content_version_id: UUID, db: Session = Depends(get_db)):
    version = db.get(ContentVersion, content_version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Content version not found")

    review = (
        db.query(ComplianceReview)
        .filter(ComplianceReview.content_version_id == version.id)
        .order_by(ComplianceReview.reviewed_at.desc())
        .first()
    )

    return {
        "content_version_id": version.id,
        "content_asset_id": version.content_asset_id,
        "status": version.status,
        "body": version.body,
        "version_metadata": version.version_metadata,
        "compliance": _compliance_payload(review),
    }
