from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.core.db import get_db
from apps.api.models import Brand

router = APIRouter(prefix="/brands", tags=["brands"])

FALLBACK_BRANDS_PAYLOAD = [
    {
        "brand_id": "ea083cec-c84d-41c1-b2c3-0efa21c3e874",
        "name": "Jade",
        "slug": "jade",
        "description": "Jewellers block insurance for Singapore jewellers and goldsmiths.",
    },
    {
        "brand_id": "f0b48a11-8e92-4f16-89d4-1a91e5e227a1",
        "name": "Jaguar Transit",
        "slug": "jaguar-transit",
        "description": "High-value goods transit insurance for logistics and freight operators.",
    },
    {
        "brand_id": "b2e873f1-4190-4821-bca2-841961e93892",
        "name": "DoctorShield",
        "slug": "doctorshield",
        "description": "Medical indemnity insurance for doctors and healthcare practitioners in Singapore.",
    },
]


@router.get("")
def list_brands(db: Session = Depends(get_db)):
    try:
        brands = db.query(Brand).order_by(Brand.name).all()
        if not brands:
            try:
                from db.seed.seed_brands import run as run_seed

                run_seed()
                brands = db.query(Brand).order_by(Brand.name).all()
            except Exception:
                pass

        if brands:
            return [
                {"brand_id": str(b.id), "name": b.name, "slug": b.slug, "description": b.description}
                for b in brands
            ]
    except Exception as e:
        print(f"Database query note in list_brands: {e}")

    return FALLBACK_BRANDS_PAYLOAD
