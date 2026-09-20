from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from apps.api.agents import research as research_agent
from apps.api.core.db import get_db
from apps.api.models import Brand, KnowledgeChunk

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/run")
def run_research(
    brand_id: UUID = Query(..., description="Brand to run research for"),
    db: Session = Depends(get_db),
):
    try:
        return research_agent.run_research(db, brand_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/observations")
def list_observations(
    brand_id: UUID = Query(..., description="Brand to list observations for"),
    db: Session = Depends(get_db),
):
    if db.get(Brand, brand_id) is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    chunks = (
        db.query(KnowledgeChunk)
        .filter(
            KnowledgeChunk.brand_id == brand_id,
            KnowledgeChunk.category == "competitor_observation",
        )
        .order_by(KnowledgeChunk.created_at.desc())
        .all()
    )
    return [
        {
            "chunk_id": c.id,
            "title": c.title,
            "content": c.content,
            "source": c.source,
            "created_at": c.created_at,
        }
        for c in chunks
    ]
