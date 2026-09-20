"""Optimization agent.

Reads engagement data, aggregates it deterministically, and turns the aggregate
into insights that feed back into content generation.

Division of labour, same as the Opportunity and Lead agents: **all arithmetic is
deterministic and LLM-free**. The model is given a compact aggregate table (never
raw rows) and writes narrative only. Every insight persists the aggregate it came
from in `derived_from`, so a reader can check the claim against the numbers
instead of taking the model's word for it.

DATA HONESTY: the only analytics in this system are simulated (see
db/seed/seed_simulated_analytics.py). `analytics_are_simulated` is reported on
every response and rendered in the dashboard. Nothing here has seen real
engagement.

The `angle` / `hook_style` dimensions come from content_versions.metadata, which
today is written only by the simulated seeder. Real agent-generated content does
not carry those tags, so those two groupings cover simulated posts only; the
platform grouping would work on any content.
"""
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from apps.api.core import llm_client
from apps.api.core.config import settings
from apps.api.models import Analytics, Brand, ContentAsset, ContentVersion, PerformanceInsight

PROMPT_VERSION = "optimization-v1"
PRIMARY_METRIC = "engagement_rate"
MIN_GROUP_SIZE = 3  # below this a group average is too thin to draw a conclusion
MAX_INSIGHTS = 6

# Whitelist, same idea as metrics/review/lessons (origin == "agent"), widened by
# one value: this agent's dataset IS the simulated posts. Anything else —
# test_fixture posts the publishing worker seeds and syncs metrics for, manual
# /demo checks — must never move an insight (observed: worker --seed took Jade's
# LinkedIn bucket from 9 posts / 3.40% to 10 posts / 3.82%).
AGGREGATED_ORIGINS = ("agent", "simulated")

INSIGHTS_SCHEMA = {
    "type": "object",
    "properties": {
        "insights": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "insight_text": {"type": "string"},
                    "supporting_metric": {"type": "string"},
                    "recommendation": {"type": "string"},
                    "insight_type": {
                        "type": "string",
                        "enum": ["angle", "hook_style", "platform", "volume", "other"],
                    },
                },
                "required": [
                    "insight_text",
                    "supporting_metric",
                    "recommendation",
                    "insight_type",
                ],
            },
        }
    },
    "required": ["insights"],
}


def _group_by_metadata_key(db: Session, brand_id: UUID, key: str) -> list[dict]:
    """Average the primary metric grouped by a content_versions.metadata key."""
    rows = (
        db.query(
            ContentVersion.version_metadata[key].astext.label("bucket"),
            func.count(Analytics.id).label("posts"),
            func.avg(Analytics.metric_value).label("avg_value"),
        )
        .join(ContentAsset, ContentAsset.id == Analytics.content_asset_id)
        .join(ContentVersion, ContentVersion.content_asset_id == ContentAsset.id)
        .filter(
            ContentAsset.brand_id == brand_id,
            ContentAsset.origin.in_(AGGREGATED_ORIGINS),
            Analytics.metric_name == PRIMARY_METRIC,
            ContentVersion.version_metadata[key].astext.isnot(None),
        )
        .group_by("bucket")
        .all()
    )
    return [
        {"bucket": r.bucket, "posts": r.posts, "avg_engagement_rate": round(float(r.avg_value), 2)}
        for r in rows
        if r.bucket is not None
    ]


def _group_by_platform(db: Session, brand_id: UUID) -> list[dict]:
    rows = (
        db.query(
            Analytics.platform.label("bucket"),
            func.count(Analytics.id).label("posts"),
            func.avg(Analytics.metric_value).label("avg_value"),
        )
        .join(ContentAsset, ContentAsset.id == Analytics.content_asset_id)
        .filter(
            ContentAsset.brand_id == brand_id,
            ContentAsset.origin.in_(AGGREGATED_ORIGINS),
            Analytics.metric_name == PRIMARY_METRIC,
        )
        .group_by(Analytics.platform)
        .all()
    )
    return [
        {"bucket": r.bucket, "posts": r.posts, "avg_engagement_rate": round(float(r.avg_value), 2)}
        for r in rows
        if r.bucket is not None
    ]


def _totals(db: Session, brand_id: UUID) -> dict:
    rows = (
        db.query(
            Analytics.metric_name,
            func.count(Analytics.id),
            func.avg(Analytics.metric_value),
            func.min(Analytics.metric_value),
            func.max(Analytics.metric_value),
        )
        .join(ContentAsset, ContentAsset.id == Analytics.content_asset_id)
        .filter(ContentAsset.brand_id == brand_id, ContentAsset.origin.in_(AGGREGATED_ORIGINS))
        .group_by(Analytics.metric_name)
        .all()
    )
    return {
        name: {
            "rows": count,
            "avg": round(float(avg), 2),
            "min": round(float(lo), 2),
            "max": round(float(hi), 2),
        }
        for name, count, avg, lo, hi in rows
    }


def _all_simulated(db: Session, brand_id: UUID) -> bool:
    """True when every analytics row for this brand is flagged simulated."""
    real = (
        db.query(func.count(Analytics.id))
        .join(ContentAsset, ContentAsset.id == Analytics.content_asset_id)
        .filter(
            ContentAsset.brand_id == brand_id,
            ContentAsset.origin.in_(AGGREGATED_ORIGINS),
            Analytics.is_simulated.is_(False),
        )
        .scalar()
    )
    return not real


def aggregate_performance(db: Session, brand_id: UUID) -> dict:
    """Deterministic aggregation. Makes NO LLM calls — safe to run freely and
    the basis for `GET /optimization/aggregate`, which previews exactly what the
    model will be shown."""
    groups = {
        "angle": _group_by_metadata_key(db, brand_id, "angle"),
        "hook_style": _group_by_metadata_key(db, brand_id, "hook_style"),
        "platform": _group_by_platform(db, brand_id),
    }
    for rows in groups.values():
        rows.sort(key=lambda r: r["avg_engagement_rate"], reverse=True)

    # Flag groups too small to support a conclusion, so the model can be told
    # explicitly not to generalise from them.
    thin = {
        dim: [r["bucket"] for r in rows if r["posts"] < MIN_GROUP_SIZE]
        for dim, rows in groups.items()
    }

    return {
        "primary_metric": PRIMARY_METRIC,
        "groups": groups,
        "thin_groups": {k: v for k, v in thin.items() if v},
        "min_group_size": MIN_GROUP_SIZE,
        "totals": _totals(db, brand_id),
        "analytics_are_simulated": _all_simulated(db, brand_id),
    }


def _render_aggregate(aggregate: dict) -> str:
    lines = [f"Primary metric: {aggregate['primary_metric']} (percent).", ""]
    for dim, rows in aggregate["groups"].items():
        if not rows:
            continue
        lines.append(f"Average {aggregate['primary_metric']} by {dim}:")
        for r in rows:
            lines.append(
                f"  - {r['bucket']}: {r['avg_engagement_rate']}% across {r['posts']} posts"
            )
        lines.append("")
    if aggregate["totals"]:
        lines.append("Overall metric ranges:")
        for name, t in aggregate["totals"].items():
            lines.append(f"  - {name}: avg {t['avg']}, min {t['min']}, max {t['max']} ({t['rows']} rows)")
        lines.append("")
    if aggregate["thin_groups"]:
        lines.append(
            f"Groups with fewer than {aggregate['min_group_size']} posts (do NOT draw "
            f"conclusions from these): {aggregate['thin_groups']}"
        )
    return "\n".join(lines)


_SYSTEM_INSTRUCTION = (
    "You are a marketing performance analyst. You will be given ONLY an aggregate "
    "table of engagement figures. Report what the numbers actually show.\n"
    "Rules:\n"
    "- Every insight must cite a real figure from the table in supporting_metric, "
    "including the comparison (e.g. '4.38% vs 2.18%').\n"
    "- Do NOT invent patterns, causes, or data that are not in the table.\n"
    "- Do NOT draw conclusions from groups flagged as too small.\n"
    "- If a difference is small, say it is small rather than presenting it as a finding.\n"
    "- Each recommendation must be a concrete, actionable instruction for a writer.\n"
    "- Rank insights strongest-evidence first."
)


def generate_insights(db: Session, brand_id: UUID, limit: int = 4) -> list[PerformanceInsight]:
    """One LLM call. Replaces this brand's previous insights so the table always
    reflects the current data rather than accumulating stale rounds."""
    brand = db.get(Brand, brand_id)
    if brand is None:
        raise ValueError(f"Brand {brand_id} not found")

    aggregate = aggregate_performance(db, brand_id)
    if not any(aggregate["groups"].values()):
        raise ValueError(
            f"No analytics data for brand '{brand.slug}'. "
            "Run `python -m db.seed.seed_simulated_analytics` first."
        )

    limit = max(1, min(limit, MAX_INSIGHTS))
    prompt = (
        f"Brand: {brand.name}. Target audience: {brand.target_audience or 'N/A'}.\n\n"
        f"{_render_aggregate(aggregate)}\n\n"
        f"Produce at most {limit} insights, strongest evidence first."
    )

    parsed = llm_client.generate_json(
        prompt,
        db,
        schema=INSIGHTS_SCHEMA,
        required_keys=("insights",),
        system=_SYSTEM_INSTRUCTION,
        model=settings.GEMINI_MODEL,
        agent_name="optimization_agent",
        prompt_version=PROMPT_VERSION,
        related_entity_type="brand",
        related_entity_id=brand_id,
    )

    db.query(PerformanceInsight).filter(PerformanceInsight.brand_id == brand_id).delete()

    created: list[PerformanceInsight] = []
    for item in (parsed.get("insights") or [])[:limit]:
        insight = PerformanceInsight(
            brand_id=brand_id,
            insight_text=item["insight_text"],
            insight_type=item.get("insight_type"),
            supporting_metric=item.get("supporting_metric"),
            recommendation=item.get("recommendation"),
            # Provenance: the exact aggregate the model was shown.
            derived_from={
                "primary_metric": aggregate["primary_metric"],
                "groups": aggregate["groups"],
                "analytics_are_simulated": aggregate["analytics_are_simulated"],
                "prompt_version": PROMPT_VERSION,
            },
            generated_by_agent="optimization_agent",
        )
        db.add(insight)
        created.append(insight)

    db.commit()
    for insight in created:
        db.refresh(insight)
    return created


def top_insights_for_brand(db: Session, brand_id: UUID, limit: int = 3) -> list[PerformanceInsight]:
    return (
        db.query(PerformanceInsight)
        .filter(PerformanceInsight.brand_id == brand_id)
        .order_by(PerformanceInsight.created_at.desc())
        .limit(limit)
        .all()
    )


def build_performance_guidance(db: Session, brand_id: UUID, limit: int = 3) -> str | None:
    """Render this brand's insights as prompt guidance for the content agent.

    Mirrors lessons_agent.build_lessons_guidance: it sits alongside the lessons
    block rather than replacing it, since the two answer different questions —
    lessons are what reviewers rejected, this is what performed.
    """
    top = top_insights_for_brand(db, brand_id, limit=limit)
    if not top:
        return None

    lines = [
        "Performance guidance from past engagement data (SIMULATED data — treat as "
        "directional, not proven):"
    ]
    for insight in top:
        line = f"- {insight.recommendation or insight.insight_text}"
        if insight.supporting_metric:
            line += f" (evidence: {insight.supporting_metric})"
        lines.append(line)
    return "\n".join(lines)
