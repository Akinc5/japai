from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api.agents import lessons as lessons_agent
from apps.api.agents.compliance import RISK_LEVEL_BY_OUTCOME
from apps.api.core.db import get_db
from apps.api.models import (
    ComplianceReview,
    ContentAsset,
    ContentVersion,
    Feedback,
    KnowledgeChunk,
)

router = APIRouter(prefix="/review", tags=["review"])

ReasonTag = Literal["too_salesy", "unsupported_claim", "wrong_tone", "generic", "wrong_cta", "other"]


class DecisionRequest(BaseModel):
    action: Literal["approve", "edit", "reject"]
    edited_body: Optional[str] = None
    reason_tag: Optional[ReasonTag] = None
    note: Optional[str] = None


def _latest_review(db: Session, content_version_id: UUID) -> ComplianceReview | None:
    return (
        db.query(ComplianceReview)
        .filter(ComplianceReview.content_version_id == content_version_id)
        .order_by(ComplianceReview.reviewed_at.desc())
        .first()
    )


def _risk_level(review: ComplianceReview | None) -> str | None:
    if review is None:
        return None
    return RISK_LEVEL_BY_OUTCOME.get(review.outcome, "review")


def _refresh_lessons(db: Session, brand_id) -> None:
    """The reviewer's decision is already committed by this point. Lessons are
    derived data that can always be recomputed, so a failure here must not fail
    the request and prompt a retry that would double-write feedback."""
    try:
        lessons_agent.recompute_lessons_for_brand(db, brand_id)
    except Exception as exc:  # noqa: BLE001 - derived data, never fail the decision
        db.rollback()
        print(f"[review] lessons recompute failed for brand {brand_id}: {exc}")


@router.get("/pending")
def list_pending(db: Session = Depends(get_db)):
    versions = (
        db.query(ContentVersion)
        .join(ContentAsset, ContentVersion.content_asset_id == ContentAsset.id)
        .filter(
            ContentVersion.status == "submitted_for_review",
            ContentVersion.is_current.is_(True),
            # Regression fixtures that score 'review' would otherwise land straight
            # in the demo queue alongside real content.
            ContentAsset.origin == "agent",
        )
        .order_by(ContentVersion.created_at.desc())
        .all()
    )
    results = []
    for version in versions:
        asset = version.content_asset
        review = _latest_review(db, version.id)
        results.append(
            {
                "content_version_id": version.id,
                "content_asset_id": asset.id,
                "brand_id": asset.brand_id,
                "brand_name": asset.brand.name if asset.brand else None,
                "platform": asset.platform,
                "language": asset.language,
                "is_localized": asset.source_content_asset_id is not None,
                "body_preview": version.body[:200],
                "risk_level": _risk_level(review),
                "created_at": version.created_at,
            }
        )
    return results


@router.get("/{content_version_id}")
def get_review_detail(content_version_id: UUID, db: Session = Depends(get_db)):
    version = db.get(ContentVersion, content_version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Content version not found")

    asset = version.content_asset
    review = _latest_review(db, version.id)
    metadata = version.version_metadata or {}

    source_refs = metadata.get("sources", [])
    chunk_ids = [s["chunk_id"] for s in source_refs if "chunk_id" in s]
    chunks_by_id = {}
    if chunk_ids:
        chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.id.in_(chunk_ids)).all()
        chunks_by_id = {str(c.id): c for c in chunks}
    sources = [
        {
            "chunk_id": s["chunk_id"],
            "category": s.get("category"),
            "title": s.get("title"),
            "content": chunks_by_id[s["chunk_id"]].content if s["chunk_id"] in chunks_by_id else None,
        }
        for s in source_refs
    ]

    return {
        "content_version_id": version.id,
        "content_asset_id": asset.id,
        "brand_id": asset.brand_id,
        "brand_name": asset.brand.name if asset.brand else None,
        "platform": asset.platform,
        "language": asset.language,
        "is_localized": asset.source_content_asset_id is not None,
        "source_content_asset_id": asset.source_content_asset_id,
        "status": version.status,
        "body": version.body,
        "topic": metadata.get("topic"),
        "suggested_revision": metadata.get("suggested_revision"),
        "sources": sources,
        "compliance": None
        if review is None
        else {
            "id": review.id,
            "outcome": review.outcome,
            "risk_level": _risk_level(review),
            "reviewer_type": review.reviewer_type,
            "detected_issues": review.detected_issues or [],
            "notes": review.notes,
            "reviewed_at": review.reviewed_at,
        },
    }


@router.post("/{content_version_id}/decision")
def submit_decision(content_version_id: UUID, payload: DecisionRequest, db: Session = Depends(get_db)):
    version = db.get(ContentVersion, content_version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Content version not found")

    brand_id = version.content_asset.brand_id

    if payload.action == "approve":
        version.status = "approved"
        db.add(version)
        wrote_feedback = bool(payload.note)
        if wrote_feedback:
            db.add(
                Feedback(
                    content_asset_id=version.content_asset_id,
                    content_version_id=version.id,
                    source="human_review",
                    feedback_text=payload.note,
                    reason_tag=payload.reason_tag,
                )
            )
        db.commit()
        if wrote_feedback:
            _refresh_lessons(db, brand_id)
        return {"content_version_id": version.id, "status": version.status}

    if payload.action == "reject":
        if not payload.reason_tag or not payload.note:
            raise HTTPException(status_code=400, detail="reject requires both reason_tag and note")
        version.status = "rejected"
        db.add(version)
        db.add(
            Feedback(
                content_asset_id=version.content_asset_id,
                content_version_id=version.id,
                source="human_review",
                feedback_text=payload.note,
                reason_tag=payload.reason_tag,
            )
        )
        db.commit()
        _refresh_lessons(db, brand_id)
        return {"content_version_id": version.id, "status": version.status}

    if payload.action == "edit":
        if not payload.edited_body:
            raise HTTPException(status_code=400, detail="edit requires edited_body")

        version.is_current = False
        db.add(version)

        new_metadata = dict(version.version_metadata or {})
        new_metadata.pop("suggested_revision", None)

        new_version = ContentVersion(
            content_asset_id=version.content_asset_id,
            version_number=version.version_number + 1,
            body=payload.edited_body,
            version_metadata=new_metadata,
            generated_by_agent="human_edit",
            status="approved",
            is_current=True,
        )
        db.add(new_version)
        db.flush()

        db.add(
            Feedback(
                content_asset_id=version.content_asset_id,
                content_version_id=version.id,
                source="human_review",
                feedback_text=payload.note or "Content edited by reviewer before approval.",
                reason_tag=payload.reason_tag,
            )
        )
        db.commit()
        db.refresh(new_version)
        _refresh_lessons(db, brand_id)
        return {
            "content_version_id": new_version.id,
            "previous_content_version_id": version.id,
            "status": new_version.status,
        }

    raise HTTPException(status_code=400, detail="Unknown action")
