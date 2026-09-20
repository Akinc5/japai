"""Pure DB/logic test for lessons aggregation — makes NO LLM calls.

Creates an isolated throwaway brand so it never depends on (or pollutes) the
seeded Jade data, and rolls everything back at the end.
"""
from dotenv import load_dotenv

load_dotenv()

from apps.api.agents import lessons as lessons_agent
from apps.api.core.db import SessionLocal
from apps.api.models import (
    Brand,
    Campaign,
    ContentAsset,
    ContentVersion,
    Feedback,
    Lesson,
    Organization,
)

# 4x too_salesy (dominant), 2x generic, 1x wrong_cta
SEEDED_REASON_TAGS = ["too_salesy"] * 4 + ["generic"] * 2 + ["wrong_cta"]


def test_aggregation_counts_and_ranks_reason_tags():
    db = SessionLocal()
    try:
        org = Organization(name="Lessons Test Org")
        db.add(org)
        db.flush()

        brand = Brand(
            organization_id=org.id,
            name="Lessons Test Brand",
            slug=f"lessons-test-{org.id.hex[:8]}",
        )
        db.add(brand)
        db.flush()

        campaign = Campaign(brand_id=brand.id, name="Test Campaign", status="active")
        db.add(campaign)
        db.flush()

        for i, reason_tag in enumerate(SEEDED_REASON_TAGS):
            asset = ContentAsset(
                campaign_id=campaign.id,
                brand_id=brand.id,
                asset_type="social_post",
                platform="linkedin",
                status="draft",
                # 'agent' on purpose: aggregation only counts organic content, and
                # this test must exercise that same path. Isolation comes from the
                # throwaway brand plus the cleanup in `finally`, not from the tag.
                origin="agent",
            )
            db.add(asset)
            db.flush()

            version = ContentVersion(
                content_asset_id=asset.id,
                version_number=1,
                body=f"Test body {i}",
                status="rejected",
                is_current=True,
            )
            db.add(version)
            db.flush()

            db.add(
                Feedback(
                    content_asset_id=asset.id,
                    content_version_id=version.id,
                    source="human_review",
                    feedback_text=f"Test feedback {i}",
                    reason_tag=reason_tag,
                )
            )
        db.flush()

        lessons_agent.recompute_lessons_for_brand(db, brand.id)

        rows = (
            db.query(Lesson)
            .filter(Lesson.brand_id == brand.id)
            .order_by(Lesson.frequency_count.desc())
            .all()
        )
        by_tag = {row.reason_tag: row for row in rows}

        assert len(rows) == 3, f"expected 3 lesson rows, got {len(rows)}"
        assert by_tag["too_salesy"].frequency_count == 4
        assert by_tag["generic"].frequency_count == 2
        assert by_tag["wrong_cta"].frequency_count == 1
        assert rows[0].reason_tag == "too_salesy", "dominant tag should rank first"
        assert by_tag["too_salesy"].lesson_text, "lesson_text must be populated"
        assert by_tag["too_salesy"].source_feedback_id is not None
        print("Aggregation counts OK:", {t: r.frequency_count for t, r in by_tag.items()})

        # Idempotency: recomputing must not double-count.
        lessons_agent.recompute_lessons_for_brand(db, brand.id)
        recount = (
            db.query(Lesson)
            .filter(Lesson.brand_id == brand.id, Lesson.reason_tag == "too_salesy")
            .one()
        )
        assert recount.frequency_count == 4, "recompute must be idempotent, not additive"
        print("Idempotency OK: still 4 after second recompute")

        guidance = lessons_agent.build_lessons_guidance(db, brand.id)
        assert guidance is not None
        assert "57%" in guidance, f"expected 4/7 = 57% share in guidance, got:\n{guidance}"
        print("Guidance OK:\n" + guidance)

        print("\nPASS: lessons aggregation")
    finally:
        # recompute_lessons_for_brand commits, so clean up explicitly.
        db.query(Lesson).filter(Lesson.brand_id == brand.id).delete()
        db.query(Organization).filter(Organization.id == org.id).delete()
        db.commit()
        db.close()


if __name__ == "__main__":
    test_aggregation_counts_and_ranks_reason_tags()
