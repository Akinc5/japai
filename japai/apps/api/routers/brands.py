from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.core.db import get_db
from apps.api.models import Brand

router = APIRouter(prefix="/brands", tags=["brands"])


@router.get("")
def list_brands(db: Session = Depends(get_db)):
    return [
        {"brand_id": b.id, "name": b.name, "slug": b.slug, "description": b.description}
        for b in db.query(Brand).order_by(Brand.name).all()
    ]
