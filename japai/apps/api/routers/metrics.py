from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from apps.api.core.db import get_db
from apps.api.models import Brand, ContentAsset, ContentVersion

router = APIRouter(prefix="/metrics", tags=["metrics"])

DECIDED_STATUSES = ("approved", "rejected")


def _rate(rejected: int, approved: int) -> float | None:
    decided = rejected + approved
    if decided == 0:
        return None
    return round(rejected / decided, 4)


def _compute_for_brand(db: Session, brand: Brand, bucket_size: int) -> dict:
    versions = (
        db.query(ContentVersion.id, ContentVersion.status, ContentVersion.created_at)
        .join(ContentAsset, ContentVersion.content_asset_id == ContentAsset.id)
        .filter(
            ContentAsset.brand_id == brand.id,
            ContentVersion.status.in_(DECIDED_STATUSES),
            ContentAsset.origin == "agent",
        )
        .order_by(ContentVersion.created_at.asc())
        .all()
    )

    total_rejected = sum(1 for v in versions if v.status == "rejected")
    total_approved = sum(1 for v in versions if v.status == "approved")

    buckets = []
    for index in range(0, len(versions), bucket_size):
        chunk = versions[index : index + bucket_size]
        rejected = sum(1 for v in chunk if v.status == "rejected")
        approved = sum(1 for v in chunk if v.status == "approved")
        buckets.append(
            {
                "bucket": index // bucket_size + 1,
                "versions": len(chunk),
                "approved": approved,
                "rejected": rejected,
                "rejection_rate": _rate(rejected, approved),
                "first_created_at": chunk[0].created_at,
                "last_created_at": chunk[-1].created_at,
            }
        )

    return {
        "brand_id": brand.id,
        "brand_name": brand.name,
        "bucket_size": bucket_size,
        "total_decided": len(versions),
        "total_approved": total_approved,
        "total_rejected": total_rejected,
        "overall_rejection_rate": _rate(total_rejected, total_approved),
        "buckets": buckets,
    }


@router.get("/rejection-rate")
def rejection_rate(
    brand_id: UUID | None = Query(None, description="Brand to compute for; omit for all brands"),
    bucket_size: int = Query(5, ge=1, le=100, description="Versions per sequential bucket"),
    db: Session = Depends(get_db),
):
    """Rejection rate = rejected / (approved + rejected) over content_versions.

    Bucketed into sequential batches of `bucket_size` ordered oldest-first, so a
    trend is visible before there's enough volume for date bucketing.
    """
    if brand_id is not None:
        brand = db.get(Brand, brand_id)
        if brand is None:
            raise HTTPException(status_code=404, detail="Brand not found")
        return _compute_for_brand(db, brand, bucket_size)

    brands = db.query(Brand).order_by(Brand.name).all()
    results = [_compute_for_brand(db, brand, bucket_size) for brand in brands]
    return {"brands": [r for r in results if r["total_decided"] > 0]}
