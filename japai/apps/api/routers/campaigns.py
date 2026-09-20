from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api.agents import campaign as campaign_agent
from apps.api.core.db import get_db

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


class FromOpportunityRequest(BaseModel):
    opportunity_id: UUID


@router.post("/from-opportunity")
def from_opportunity(payload: FromOpportunityRequest, db: Session = Depends(get_db)):
    """Expands an opportunity into a campaign brief, then generates one asset per
    suggested format. Each asset runs through the standard compliance pipeline."""
    try:
        return campaign_agent.create_campaign_from_opportunity(db, payload.opportunity_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
