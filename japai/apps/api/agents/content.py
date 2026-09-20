import re
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from apps.api.agents import lessons as lessons_agent
from apps.api.agents import optimization as optimization_agent
from apps.api.core import llm_client
from apps.api.core.config import settings
from apps.api.models import Brand, Campaign, ContentAsset, ContentVersion, KnowledgeChunk

AD_HOC_CAMPAIGN_MARKER = "Ad Hoc Content"
PROMPT_VERSION = "content-v4"
MAX_LESSONS = 5
MAX_INSIGHTS = 3

# Format -> (platform, asset_type, structural instruction). Lets one agent emit
# several platform-native shapes without duplicating the generation pipeline.
FORMAT_SPECS: dict[str, dict[str, str]] = {
    "linkedin_post": {
        "platform": "linkedin",
        "asset_type": "social_post",
        "instruction": "Write a single LinkedIn post of 3-5 short paragraphs in a "
        "professional register. No hashtag spam, no emoji.",
    },
    "instagram_carousel": {
        "platform": "instagram",
        "asset_type": "social_post",
        "instruction": "Write an Instagram carousel of 5-7 slides. Label each 'Slide N:' "
        "with one punchy line plus a supporting sentence, then end with a short caption.",
    },
    "reel_script": {
        "platform": "instagram",
        "asset_type": "other",
        "instruction": "Write a 30-45 second Reel script with timestamped beats "
        "(e.g. '0-3s Hook:'), spoken voiceover lines and on-screen text cues.",
    },
    "x_thread": {
        "platform": "x",
        "asset_type": "social_post",
        "instruction": "Write an X thread of 5-7 numbered posts. Each post must be under "
        "280 characters and the first must work as a standalone hook.",
    },
    # Lead-agent outreach. Routed through this agent (rather than a parallel one)
    # so outreach inherits brand voice, approved/restricted claims and the
    # lessons loop, and lands as a ContentVersion the existing compliance and
    # review pipeline already understands. asset_type 'email' is already allowed
    # by ck_content_assets_asset_type.
    "outreach_email": {
        "platform": "email",
        "asset_type": "email",
        "instruction": "Write a single short outreach email. Plain prose, no subject "
        "line, no markdown headings, no bullet lists.",
    },
}
STOPWORDS = {"the", "and", "for", "with", "about", "your", "from", "that", "this"}


def _keywords(topic: str) -> list[str]:
    words = re.findall(r"[a-zA-Z]{4,}", topic.lower())
    return [w for w in words if w not in STOPWORDS]


def _retrieve_knowledge(db: Session, brand_id: UUID, topic: str, faq_limit: int = 5) -> dict:
    approved_and_guidelines = (
        db.query(KnowledgeChunk)
        .filter(
            KnowledgeChunk.brand_id == brand_id,
            KnowledgeChunk.category.in_(["approved_claim", "brand_guideline"]),
        )
        .all()
    )
    restricted = (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.brand_id == brand_id, KnowledgeChunk.category == "restricted_claim")
        .all()
    )
    faq_base = db.query(KnowledgeChunk).filter(
        KnowledgeChunk.brand_id == brand_id, KnowledgeChunk.category == "faq"
    )
    keywords = _keywords(topic)
    matched_faq = []
    if keywords:
        conditions = [KnowledgeChunk.title.ilike(f"%{kw}%") for kw in keywords]
        conditions += [KnowledgeChunk.content.ilike(f"%{kw}%") for kw in keywords]
        matched_faq = faq_base.filter(or_(*conditions)).limit(faq_limit).all()
    if not matched_faq:
        matched_faq = faq_base.limit(faq_limit).all()

    return {
        "approved_claim": [c for c in approved_and_guidelines if c.category == "approved_claim"],
        "brand_guideline": [c for c in approved_and_guidelines if c.category == "brand_guideline"],
        "faq": matched_faq,
        "restricted_claim": restricted,
    }


def _build_system_prompt(
    brand: Brand,
    platform: str,
    chunks: dict,
    lessons_guidance: str | None = None,
    format_instruction: str | None = None,
    campaign: Campaign | None = None,
    extra_context: str | None = None,
    performance_guidance: str | None = None,
) -> str:
    lines = [
        f"You are a marketing copywriter for {brand.name}, a Singapore InsurTech brand.",
        f"Brand voice: {brand.voice_description or 'N/A'}",
        f"Tone guidelines: {brand.tone_guidelines or 'N/A'}",
        f"Target audience: {brand.target_audience or 'N/A'}",
        f"You are writing a single post for the platform: {platform}.",
        "",
        "Approved facts and claims you may use (do not invent facts beyond these):",
    ]
    lines += [f"- {c.content}" for c in chunks["approved_claim"]] or ["- (none on file; rely on brand voice only)"]
    lines += ["", "Brand guidelines:"]
    lines += [f"- {c.content}" for c in chunks["brand_guideline"]] or ["- (none on file)"]
    if chunks["faq"]:
        lines += ["", "Relevant FAQ context:"]
        lines += [f"- {c.title}: {c.content}" for c in chunks["faq"]]
    if chunks["restricted_claim"]:
        lines += ["", "Do NOT say or imply any of the following (compliance-restricted claims):"]
        lines += [f"- {c.content}" for c in chunks["restricted_claim"]]
    if campaign is not None:
        lines += ["", f"This post belongs to the campaign: {campaign.name}."]
        if campaign.objective:
            lines.append(f"Campaign strategy: {campaign.objective}")
        if campaign.key_message:
            lines.append(f"Key message to land: {campaign.key_message}")
        if campaign.cta:
            lines.append(f"Call to action: {campaign.cta}")
        if campaign.target_audience:
            lines.append(f"Campaign audience: {campaign.target_audience}")
    if format_instruction:
        lines += ["", f"Format requirements: {format_instruction}"]
    if extra_context:
        lines += ["", extra_context]
    if lessons_guidance:
        lines += ["", lessons_guidance]
    # Sits alongside lessons rather than replacing it: lessons are what reviewers
    # rejected, performance guidance is what engaged. Both inform the same draft.
    if performance_guidance:
        lines += ["", performance_guidance]
    lines += [
        "",
        "Write compliant, on-brand marketing copy. Never use absolute guarantee language "
        "(e.g. 'guaranteed', 'risk-free', '100% covered', 'no exceptions').",
    ]
    return "\n".join(lines)


def get_or_create_ad_hoc_campaign(db: Session, brand: Brand) -> Campaign:
    name = f"{AD_HOC_CAMPAIGN_MARKER} — {brand.name}"
    campaign = db.query(Campaign).filter_by(brand_id=brand.id, name=name).first()
    if campaign is None:
        campaign = Campaign(
            brand_id=brand.id,
            name=name,
            objective="Ungrouped content generated outside a formal campaign (pre-Phase 5).",
            status="active",
        )
        db.add(campaign)
        db.flush()
    return campaign


def generate_content(
    db: Session,
    brand_id: UUID,
    platform: str,
    topic: str,
    content_format: str | None = None,
    campaign: Campaign | None = None,
    extra_context: str | None = None,
) -> ContentVersion:
    """Generate one content version. `content_format` (see FORMAT_SPECS) selects a
    platform-native shape and overrides `platform`; `campaign` attaches the asset to
    an existing campaign and injects its brief instead of using the ad-hoc bucket.
    `extra_context` appends caller-supplied personalisation to the system prompt
    (the lead agent uses it to pass prospect details into outreach drafts)."""
    brand = db.get(Brand, brand_id)
    if brand is None:
        raise ValueError(f"Brand {brand_id} not found")

    spec = FORMAT_SPECS.get(content_format) if content_format else None
    if content_format and spec is None:
        raise ValueError(f"Unknown content_format: {content_format}")
    if spec:
        platform = spec["platform"]
    asset_type = spec["asset_type"] if spec else "social_post"
    format_instruction = spec["instruction"] if spec else None

    chunks = _retrieve_knowledge(db, brand_id, topic)
    applied_lessons = lessons_agent.top_lessons_for_brand(db, brand_id, limit=MAX_LESSONS)
    lessons_guidance = lessons_agent.build_lessons_guidance(db, brand_id, limit=MAX_LESSONS)
    applied_insights = optimization_agent.top_insights_for_brand(db, brand_id, limit=MAX_INSIGHTS)
    performance_guidance = optimization_agent.build_performance_guidance(
        db, brand_id, limit=MAX_INSIGHTS
    )
    system_prompt = _build_system_prompt(
        brand,
        platform,
        chunks,
        lessons_guidance,
        format_instruction,
        campaign,
        extra_context,
        performance_guidance,
    )
    user_prompt = f"Write a {content_format or platform + ' post'} about: {topic}"

    if campaign is None:
        campaign = get_or_create_ad_hoc_campaign(db, brand)

    asset = ContentAsset(
        campaign_id=campaign.id,
        brand_id=brand.id,
        asset_type=asset_type,
        platform=platform,
        title=topic[:200],
        status="draft",
        created_by="content_agent",
        origin="agent",
    )
    db.add(asset)
    db.flush()

    body = llm_client.generate(
        user_prompt,
        db,
        system=system_prompt,
        model=settings.GEMINI_MODEL,
        agent_name="content_agent",
        prompt_version=PROMPT_VERSION,
        related_entity_type="content_asset",
        related_entity_id=asset.id,
    )

    version = ContentVersion(
        content_asset_id=asset.id,
        version_number=1,
        body=body,
        version_metadata={
            "prompt_version": PROMPT_VERSION,
            "model_used": settings.GEMINI_MODEL,
            "platform": platform,
            "content_format": content_format,
            "campaign_id": str(campaign.id),
            "topic": topic,
            "system_prompt": system_prompt,
            "lessons_applied": [
                {
                    "reason_tag": lesson.reason_tag,
                    "frequency_count": lesson.frequency_count,
                    "title": lesson.title,
                }
                for lesson in applied_lessons
            ],
            # Same inspectability contract as lessons_applied: what the prompt
            # was told, persisted next to the output it produced.
            "insights_applied": [
                {
                    "insight_type": insight.insight_type,
                    "recommendation": insight.recommendation,
                    "supporting_metric": insight.supporting_metric,
                }
                for insight in applied_insights
            ],
            "sources": [
                {"chunk_id": str(c.id), "category": c.category, "title": c.title}
                for c in chunks["approved_claim"] + chunks["brand_guideline"] + chunks["faq"]
            ],
        },
        generated_by_agent="content_agent",
        status="draft",
        is_current=True,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version
