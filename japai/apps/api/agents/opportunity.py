"""Opportunity agent.

Scoring is fully deterministic and LLM-free — every number that produces a score
is recorded in `score_breakdown` so the result is explainable rather than a black
box. Exactly one LLM call is spent per candidate that clears MIN_SCORE, purely to
write the human-facing narrative (title / rationale / angle / formats).
"""
import re
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from apps.api.core import llm_client
from apps.api.core.config import settings
from apps.api.models import Brand, ContentOpportunity, KnowledgeChunk, Product

PROMPT_VERSION = "opportunity-v1"

# Weights are intentionally simple and transparent (see SCORE_FORMULA).
W_MENTIONS = 10
W_RECENCY = 20
W_COVERAGE = 30
SCORE_CAP = 100
SCORE_FORMULA = (
    "competitor_mentions*10 + recency_weight*20 + coverage_match*30, capped at 100"
)

MIN_SCORE = 25.0
# An opportunity must rest on at least one research observation. Without this a
# brand with good coverage_match but zero research would clear MIN_SCORE on
# coverage alone and spend LLM calls inventing evidence-free "opportunities".
MIN_COMPETITOR_MENTIONS = 1
MAX_OPPORTUNITIES = 5
RECENCY_WINDOW_DAYS = 30

VALID_FORMATS = ["linkedin_post", "instagram_carousel", "reel_script", "x_thread"]

TOPIC_CLUSTERS: dict[str, list[str]] = {
    "Transit and shipping risk": [
        "transit", "shipping", "cargo", "marine", "transport", "freight", "voyage", "consignment",
    ],
    "Trade shows and exhibitions": [
        "exhibition", "trade", "show", "display", "event", "fair", "showcase",
    ],
    "Regulation and compliance": [
        "regulatory", "regulation", "authority", "compliance", "statute", "monetary", "licence",
        "supervision", "central bank",
    ],
    "Gemstone valuation and appraisal": [
        "diamond", "gemstone", "carat", "valuation", "appraisal", "stone", "mineral", "gem",
    ],
    "Theft, loss and security": [
        "theft", "burglary", "security", "loss", "stolen", "robbery", "damage", "peril",
    ],
    "Craftsmanship and brand heritage": [
        "craftsmanship", "design", "heritage", "artisan", "adornment", "goldsmith", "jewellery",
    ],
    # Medical-indemnity clusters. Without these, DoctorShield research fell
    # through to "Theft, loss and security" and produced a property-damage
    # angle that has nothing to do with medical indemnity. Clusters are global,
    # but scoring is per-brand (competitor_mentions comes from that brand's own
    # research, coverage_match from its own chunks), so these score ~0 for Jade
    # and Jaguar Transit rather than polluting their results.
    "Professional liability and indemnity": [
        "malpractice", "negligence", "indemnity", "liability", "litigation", "defence",
        "lawsuit", "damages", "tort", "professional",
    ],
    "Patient safety and clinical risk": [
        "patient", "clinical", "safety", "error", "harm", "diagnosis", "treatment",
        "medical", "practitioner", "physician", "healthcare",
    ],
}

NARRATIVE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "rationale": {"type": "string"},
        "suggested_angle": {"type": "string"},
        "suggested_formats": {
            "type": "array",
            "items": {"type": "string", "enum": VALID_FORMATS},
        },
    },
    "required": ["title", "rationale", "suggested_angle", "suggested_formats"],
}


def _matches(text: str, keywords: list[str]) -> list[str]:
    lowered = text.lower()
    return [kw for kw in keywords if re.search(rf"\b{re.escape(kw)}", lowered)]


def _recency_weight(created_at: datetime, now: datetime) -> float:
    age_days = max((now - created_at).total_seconds() / 86400.0, 0.0)
    return max(0.0, 1.0 - age_days / RECENCY_WINDOW_DAYS)


def score_cluster(
    cluster_name: str,
    keywords: list[str],
    observations: list[KnowledgeChunk],
    coverage_chunks: list[str],
    now: datetime,
) -> dict:
    """Pure function: signals in, transparent score out. No LLM, no DB."""
    matched_obs, matched_keywords, recency_values = [], set(), []

    for chunk in observations:
        hits = _matches(f"{chunk.title or ''} {chunk.content}", keywords)
        if hits:
            matched_obs.append(chunk)
            matched_keywords.update(hits)
            recency_values.append(_recency_weight(chunk.created_at, now))

    competitor_mentions = len(matched_obs)
    recency_weight = sum(recency_values) / len(recency_values) if recency_values else 0.0

    covered = sum(1 for text in coverage_chunks if _matches(text, keywords))
    coverage_match = min(1.0, covered / 2.0) if coverage_chunks else 0.0

    mention_points = competitor_mentions * W_MENTIONS
    recency_points = recency_weight * W_RECENCY
    coverage_points = coverage_match * W_COVERAGE
    raw_total = mention_points + recency_points + coverage_points
    score = min(float(SCORE_CAP), raw_total)

    return {
        "cluster": cluster_name,
        "score": round(score, 2),
        "source_chunk_ids": [str(c.id) for c in matched_obs],
        "breakdown": {
            "competitor_mentions": competitor_mentions,
            "competitor_mentions_points": round(mention_points, 2),
            "recency_weight": round(recency_weight, 4),
            "recency_points": round(recency_points, 2),
            "coverage_match": round(coverage_match, 4),
            "coverage_points": round(coverage_points, 2),
            "raw_total": round(raw_total, 2),
            "capped_at": SCORE_CAP,
            "score": round(score, 2),
            "formula": SCORE_FORMULA,
            "matched_keywords": sorted(matched_keywords),
        },
    }


def score_all_clusters(db: Session, brand_id: UUID) -> list[dict]:
    now = datetime.now(timezone.utc)

    observations = (
        db.query(KnowledgeChunk)
        .filter(
            KnowledgeChunk.brand_id == brand_id,
            KnowledgeChunk.category == "competitor_observation",
        )
        .all()
    )
    coverage_chunks = [
        f"{c.title or ''} {c.content}"
        for c in db.query(KnowledgeChunk)
        .filter(
            KnowledgeChunk.brand_id == brand_id,
            KnowledgeChunk.category.in_(["approved_claim", "faq", "brand_guideline"]),
        )
        .all()
    ]
    coverage_chunks += [
        f"{p.name} {p.description or ''}"
        for p in db.query(Product).filter(Product.brand_id == brand_id).all()
    ]

    scored = [
        score_cluster(name, keywords, observations, coverage_chunks, now)
        for name, keywords in TOPIC_CLUSTERS.items()
    ]
    return sorted(scored, key=lambda s: s["score"], reverse=True)


def _generate_narrative(db: Session, brand: Brand, candidate: dict) -> dict:
    b = candidate["breakdown"]
    prompt = (
        f"Brand: {brand.name} — {brand.description or ''}\n"
        f"Audience: {brand.target_audience or 'n/a'}\n\n"
        f"A deterministic scoring pass surfaced this content opportunity:\n"
        f"- Topic cluster: {candidate['cluster']}\n"
        f"- Score: {candidate['score']}/100 ({b['formula']})\n"
        f"- Competitor/industry sources mentioning it: {b['competitor_mentions']}\n"
        f"- Recency weight: {b['recency_weight']}\n"
        f"- Brand coverage match: {b['coverage_match']}\n"
        f"- Matched keywords: {', '.join(b['matched_keywords']) or 'none'}\n\n"
        "Write a short opportunity brief: a `title` (max 10 words), a plain-English "
        "`rationale` (2 sentences, referencing why these signals make it worth doing), a "
        "`suggested_angle` (one sentence on the creative angle), and `suggested_formats` "
        f"— pick the 2-3 most sensible from {VALID_FORMATS}. Do not pick all four."
    )
    result = llm_client.generate_json(
        prompt,
        db,
        schema=NARRATIVE_SCHEMA,
        required_keys=("title", "rationale", "suggested_angle"),
        model=settings.GEMINI_MODEL,
        agent_name="opportunity_agent",
        prompt_version=PROMPT_VERSION,
        related_entity_type="brand",
        related_entity_id=brand.id,
    )
    formats = [f for f in result.get("suggested_formats", []) if f in VALID_FORMATS]
    result["suggested_formats"] = formats[:3] or ["linkedin_post"]
    return result


def generate_opportunities(
    db: Session, brand_id: UUID, limit: int = MAX_OPPORTUNITIES
) -> list[ContentOpportunity]:
    brand = db.get(Brand, brand_id)
    if brand is None:
        raise ValueError(f"Brand {brand_id} not found")

    candidates = [
        c
        for c in score_all_clusters(db, brand_id)
        if c["score"] >= MIN_SCORE
        and c["breakdown"]["competitor_mentions"] >= MIN_COMPETITOR_MENTIONS
    ][:limit]
    if not candidates:
        return []

    # Suggestions are derived from current research; clear stale ones but never
    # touch opportunities a human has already promoted past 'suggested'.
    db.query(ContentOpportunity).filter(
        ContentOpportunity.brand_id == brand_id, ContentOpportunity.status == "suggested"
    ).delete(synchronize_session=False)

    created = []
    for candidate in candidates:
        narrative = _generate_narrative(db, brand, candidate)
        opportunity = ContentOpportunity(
            brand_id=brand_id,
            title=narrative["title"],
            description=narrative["rationale"],
            opportunity_type=candidate["cluster"],
            source="opportunity_agent",
            priority_score=candidate["score"],
            score_breakdown=candidate["breakdown"],
            suggested_angle=narrative["suggested_angle"],
            suggested_formats=narrative["suggested_formats"],
            source_chunk_ids=candidate["source_chunk_ids"],
            status="suggested",
        )
        db.add(opportunity)
        created.append(opportunity)

    db.commit()
    for opportunity in created:
        db.refresh(opportunity)
    return created
