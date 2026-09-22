from uuid import UUID
from typing import Optional, Union
from sqlalchemy.orm import Session
from apps.api.models import Brand


def get_or_resolve_brand(db: Session, brand_identifier: Optional[Union[str, UUID]] = None) -> Optional[Brand]:
    """Safely resolves a brand by UUID, slug, or falls back to the primary brand."""
    brand = None
    if brand_identifier:
        # Try direct UUID lookup
        try:
            brand = db.get(Brand, UUID(str(brand_identifier)))
        except Exception:
            pass
        # Try slug lookup
        if brand is None:
            brand = db.query(Brand).filter(Brand.slug == str(brand_identifier).lower().strip()).first()
        # Try partial name match
        if brand is None:
            brand = db.query(Brand).filter(Brand.name.ilike(f"%{brand_identifier}%")).first()

    # Fallback to first brand
    if brand is None:
        brand = db.query(Brand).first()

    # If database has no brands at all, auto-seed default brands
    if brand is None:
        try:
            from db.seed.seed_brands import run as run_seed

            run_seed()
            if brand_identifier:
                brand = db.query(Brand).filter(Brand.slug == str(brand_identifier).lower().strip()).first()
            if brand is None:
                brand = db.query(Brand).first()
        except Exception as e:
            print(f"Auto-seeding brands failed: {e}")

    return brand
