"""Campaign agent: expands a scored opportunity into a short campaign brief
(one LLM call), then fans out to the existing content agent once per suggested
format. Generation and compliance are reused unchanged — opportunity-sourced
content is not special-cased anywhere in the compliance pipeline.
"""
from uuid import UUID

from sqlalchemy.orm import Session

from apps.api.agents import compliance as compliance_agent
from apps.api.agents import content as content_agent
from apps.api.core import llm_client
from apps.api.core.config import settings
from apps.api.models import Brand, Campaign, ContentOpportunity

PROMPT_VERSION = "campaign-brief-v1"

BRIEF_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "strategy": {"type": "string"},
        "target_audience": {"type": "string"},
        "key_message": {"type": "string"},
        "cta": {"type": "string"},
    },
    "required": ["name", "strategy", "target_audience", "key_message", "cta"],
}


def _expand_brief(db: Session, brand: Brand, opportunity: ContentOpportunity) -> dict:
    prompt = (
        f"Brand: {brand.name} — {brand.description or ''}\n"
        f"Brand voice: {brand.voice_description or 'n/a'}\n"
        f"Default audience: {brand.target_audience or 'n/a'}\n\n"
        f"Opportunity: {opportunity.title}\n"
        f"Rationale: {opportunity.description or 'n/a'}\n"
        f"Suggested angle: {opportunity.suggested_angle or 'n/a'}\n"
        f"Score: {opportunity.priority_score}/100\n\n"
        "Expand this into a short campaign brief: a `name` (max 8 words), a `strategy` "
        "(2 sentences on approach), a `target_audience` (one sentence), a `key_message` "
        "(one sentence the audience should remember), and a `cta` (a short call to action). "
        "Keep every claim general — do not invent specific coverage terms.\n\n"
        "The brief is fed verbatim into downstream copy generation, so it must itself be "
        "compliant. Never use absolute-protection or guarantee language, including any of: "
        f"{', '.join(compliance_agent.FORBIDDEN_PHRASES)}."
    )
    return llm_client.generate_json(
        prompt,
        db,
        schema=BRIEF_SCHEMA,
        required_keys=("name", "strategy", "target_audience", "key_message", "cta"),
        model=settings.GEMINI_MODEL,
        agent_name="campaign_agent",
        prompt_version=PROMPT_VERSION,
        related_entity_type="content_opportunity",
        related_entity_id=opportunity.id,
    )


def create_campaign_from_opportunity(db: Session, opportunity_id: UUID) -> dict:
    opportunity = db.get(ContentOpportunity, opportunity_id)
    if opportunity is None:
        raise ValueError(f"Opportunity {opportunity_id} not found")

    brand = db.get(Brand, opportunity.brand_id)
    if brand is None:
        raise ValueError(f"Brand {opportunity.brand_id} not found")

    brief = _expand_brief(db, brand, opportunity)

    # The brief is injected into every downstream asset's prompt, so a blocklisted
    # phrase here poisons all of them at once. Screen it with the free deterministic
    # scan (no LLM) and surface hits rather than letting them propagate silently.
    brief_issues = []
    for field in ("strategy", "key_message", "cta", "target_audience"):
        for issue in compliance_agent._scan_blocklist(brief.get(field) or ""):
            brief_issues.append({"field": field, **issue})

    campaign = Campaign(
        brand_id=brand.id,
        opportunity_id=opportunity.id,
        name=brief["name"],
        objective=brief["strategy"],
        target_audience=brief["target_audience"],
        key_message=brief["key_message"],
        cta=brief["cta"],
        status="active",
    )
    db.add(campaign)
    db.flush()

    topic = opportunity.suggested_angle or opportunity.title
    formats = opportunity.suggested_formats or ["linkedin_post"]

    assets = []
    for content_format in formats:
        version = content_agent.generate_content(
            db,
            brand_id=brand.id,
            platform=content_agent.FORMAT_SPECS[content_format]["platform"],
            topic=topic,
            content_format=content_format,
            campaign=campaign,
        )
        review = compliance_agent.run_compliance_check(db, version)
        assets.append(
            {
                "content_version_id": str(version.id),
                "content_format": content_format,
                "platform": version.content_asset.platform,
                "status": version.status,
                "compliance_outcome": review.outcome,
                "risk_level": compliance_agent.RISK_LEVEL_BY_OUTCOME.get(review.outcome, "review"),
                "detected_issue_count": len(review.detected_issues or []),
            }
        )

    opportunity.status = "converted_to_campaign"
    db.add(opportunity)
    db.commit()
    db.refresh(campaign)

    return {
        "campaign_id": str(campaign.id),
        "campaign_name": campaign.name,
        "opportunity_id": str(opportunity.id),
        "brief": {
            "strategy": campaign.objective,
            "target_audience": campaign.target_audience,
            "key_message": campaign.key_message,
            "cta": campaign.cta,
        },
        "brief_compliance_warnings": brief_issues,
        "assets": assets,
    }
