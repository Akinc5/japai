"""Aggregates raw human-review `feedback` rows into durable per-brand `lessons`.

Kept deliberately LLM-free: summaries come from a template table keyed on
reason_tag, so this can run synchronously inside the review-decision request
without adding latency or consuming model quota.
"""
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from apps.api.models import ContentAsset, Feedback, Lesson

LESSON_TEMPLATES: dict[str, tuple[str, str]] = {
    "too_salesy": (
        "Avoid aggressive sales pressure",
        "Keep the tone consultative rather than promotional. Avoid urgency framing, "
        "hard calls to action, and pressure tactics.",
    ),
    "unsupported_claim": (
        "Only make substantiated claims",
        "Every coverage or capability claim must trace back to approved brand knowledge. "
        "Do not invent specifics about scope, geography, or outcomes.",
    ),
    "wrong_tone": (
        "Match the documented brand voice",
        "Follow the brand's voice and tone guidelines closely; avoid drifting into a "
        "generic corporate or consumer-retail register.",
    ),
    "generic": (
        "Avoid generic insurance boilerplate",
        "Lead with specifics relevant to this brand's trade and audience rather than "
        "interchangeable insurance language.",
    ),
    "wrong_cta": (
        "Use an appropriate call to action",
        "Close with the brand's preferred next step. Avoid mismatched, transactional, "
        "or overly aggressive CTAs.",
    ),
    "other": (
        "Address recurring reviewer concerns",
        "Reviewers flagged issues that did not fit a standard category. Review recent "
        "feedback notes for this brand before writing.",
    ),
}

_FALLBACK_TEMPLATE = (
    "Address recurring reviewer feedback",
    "Reviewers have repeatedly flagged this issue; address it proactively.",
)


def _brand_feedback_counts(db: Session, brand_id: UUID) -> list[tuple[str, int]]:
    """Feedback rows reach a brand via content_assets.brand_id (denormalized in
    Phase 1), so this is a single join — no need to traverse campaigns."""
    rows = (
        db.query(Feedback.reason_tag, func.count(Feedback.id))
        .join(ContentAsset, Feedback.content_asset_id == ContentAsset.id)
        .filter(
            ContentAsset.brand_id == brand_id,
            Feedback.reason_tag.isnot(None),
            ContentAsset.origin == "agent",
        )
        .group_by(Feedback.reason_tag)
        .all()
    )
    return [(reason_tag, count) for reason_tag, count in rows]


def _latest_feedback_id(db: Session, brand_id: UUID, reason_tag: str):
    row = (
        db.query(Feedback.id)
        .join(ContentAsset, Feedback.content_asset_id == ContentAsset.id)
        .filter(ContentAsset.brand_id == brand_id, Feedback.reason_tag == reason_tag)
        .order_by(Feedback.created_at.desc())
        .first()
    )
    return row[0] if row else None


def recompute_lessons_for_brand(db: Session, brand_id: UUID) -> list[Lesson]:
    """Upsert one `lessons` row per (brand_id, reason_tag) for this brand.

    Commits its own work so callers can treat it as a fire-and-forget step.
    """
    counts = _brand_feedback_counts(db, brand_id)
    if not counts:
        return []

    updated: list[Lesson] = []

    for reason_tag, count in counts:
        title, guidance = LESSON_TEMPLATES.get(reason_tag, _FALLBACK_TEMPLATE)

        lesson = (
            db.query(Lesson)
            .filter(Lesson.brand_id == brand_id, Lesson.reason_tag == reason_tag)
            .first()
        )
        if lesson is None:
            lesson = Lesson(brand_id=brand_id, reason_tag=reason_tag)
            db.add(lesson)

        lesson.title = title
        lesson.lesson_text = guidance
        lesson.category = "human_review_feedback"
        lesson.frequency_count = count
        lesson.source_feedback_id = _latest_feedback_id(db, brand_id, reason_tag)
        updated.append(lesson)

    db.commit()
    for lesson in updated:
        db.refresh(lesson)
    return updated


def top_lessons_for_brand(db: Session, brand_id: UUID, limit: int = 5) -> list[Lesson]:
    return (
        db.query(Lesson)
        .filter(Lesson.brand_id == brand_id, Lesson.frequency_count > 0)
        .order_by(Lesson.frequency_count.desc())
        .limit(limit)
        .all()
    )


def build_lessons_guidance(db: Session, brand_id: UUID, limit: int = 5) -> str | None:
    """Render this brand's top lessons as explicit prompt guidance.

    Percentages are computed against the brand's full feedback volume, not just
    the top `limit` rows, so a truncated list doesn't inflate the shares.
    """
    top = top_lessons_for_brand(db, brand_id, limit=limit)
    if not top:
        return None

    total = (
        db.query(func.coalesce(func.sum(Lesson.frequency_count), 0))
        .filter(Lesson.brand_id == brand_id)
        .scalar()
    ) or 0
    if total <= 0:
        return None

    lines = ["Past reviewer feedback for this brand (address these proactively):"]
    for lesson in top:
        share = lesson.frequency_count / total
        lines.append(
            f"- {lesson.lesson_text.rstrip('.')} "
            f"(cited in {share:.0%} of past reviewer feedback, n={lesson.frequency_count})."
        )
    return "\n".join(lines)
