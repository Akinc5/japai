from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api.agents import events as events_agent
from apps.api.core.brand_utils import get_or_resolve_brand
from apps.api.core.db import get_db
from apps.api.models import Brand, Campaign

router = APIRouter(prefix="/events", tags=["events"])


class TriggerCampaignRequest(BaseModel):
    event_id: str
    target_languages: list[str] = ["en"]


@router.get("")
def list_events():
    """List all upcoming industry events and campaign opportunities."""
    return {
        "events": events_agent.get_active_events()
    }


@router.get("/{event_id}")
def get_event(event_id: str):
    event = events_agent.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/trigger")
def trigger_event_campaign(
    req: TriggerCampaignRequest,
    db: Session = Depends(get_db)
):
    """1-Click generation of a targeted multi-channel campaign for an upcoming industry event."""
    event = events_agent.get_event_by_id(req.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    brand = get_or_resolve_brand(db, event["brand_slug"])
    if not brand:
        raise HTTPException(status_code=404, detail=f"Brand '{event['brand_slug']}' not found in database")

    key_message = f"Event Campaign for {event['title']} ({event['date_window']}). Key Angles: {'; '.join(event['suggested_angles'])}."

    campaign = Campaign(
        brand_id=brand.id,
        name=f"Event Push: {event['title']}",
        objective=f"Event Marketing & Timely Audience Outreach for {event['title']}",
        target_audience=event.get("target_audience"),
        key_message=key_message,
        cta=event.get("default_cta"),
        status="active"
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    return {
        "event": event,
        "campaign_id": str(campaign.id),
        "campaign_name": campaign.name,
        "key_message": campaign.key_message,
        "status": "created",
        "message": f"Successfully launched marketing campaign for '{event['title']}'."
    }

