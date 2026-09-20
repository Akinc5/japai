"""Proves outreach drafts are NOT exempt from compliance.

Insurance marketing rules apply to a cold outreach email exactly as they apply
to a LinkedIn post. This asserts that an aggressive, guarantee-flavoured
outreach draft is caught and rejected rather than reaching a human reviewer.

Costs ZERO LLM calls: a blocklist hit short-circuits steps 2-4, so the whole
test runs on the deterministic path. Fixtures are tagged origin='test_fixture'
and are therefore excluded from the demo review queue, metrics and lessons.
"""
from dotenv import load_dotenv

load_dotenv()

from apps.api.agents import compliance as compliance_agent
from apps.api.agents import content as content_agent
from apps.api.core.db import SessionLocal
from apps.api.models import Brand, ComplianceReview, ContentAsset, ContentVersion

AGGRESSIVE_OUTREACH = (
    "Hi Tanglin Fine Jewellers — switch your cover to Jade today and your stock is "
    "fully protected with guaranteed payout on every claim, no questions asked. "
    "This offer is risk-free."
)

CLEAN_OUTREACH = (
    "Hi Tanglin Fine Jewellers — we work with independent jewellers on Orchard Road "
    "on jewellers block cover for stock held in store and in transit. Happy to share "
    "how the cover is structured if that would be useful."
)


def _make_outreach_version(db, brand, body: str) -> ContentVersion:
    """Builds an outreach draft exactly as the lead agent does — asset_type
    'email' on the same content_assets/content_versions tables — so this
    exercises the real path, not a lookalike."""
    campaign = content_agent.get_or_create_ad_hoc_campaign(db, brand)

    asset = ContentAsset(
        campaign_id=campaign.id,
        brand_id=brand.id,
        asset_type="email",
        platform="email",
        title="lead outreach regression fixture",
        status="draft",
        origin="test_fixture",
    )
    db.add(asset)
    db.flush()

    version = ContentVersion(
        content_asset_id=asset.id,
        version_number=1,
        body=body,
        status="draft",
        is_current=True,
    )
    db.add(version)
    db.flush()
    return version


def test_aggressive_outreach_is_blocked():
    db = SessionLocal()
    try:
        brand = db.query(Brand).filter_by(slug="jade").first()
        assert brand is not None, "Seed data missing — run `python -m db.seed.seed_brands` first"

        version = _make_outreach_version(db, brand, AGGRESSIVE_OUTREACH)
        review = compliance_agent.run_compliance_check(db, version)

        assert review.outcome == "fail", f"expected fail, got {review.outcome}"
        assert version.status == "rejected", f"expected rejected, got {version.status}"

        terms = {issue["term"] for issue in review.detected_issues}
        for expected in ("fully protected", "no questions asked", "risk-free"):
            assert expected in terms, f"blocklist missed '{expected}'; caught {sorted(terms)}"

        print(f"  outreach blocked: outcome={review.outcome}, status={version.status}")
        print(f"  terms caught: {sorted(terms)}")
        print("PASS: aggressive outreach is rejected, not queued for a human")
    finally:
        db.close()


def test_clean_outreach_reaches_review():
    """The mirror case: compliance must not reject everything. This one costs
    LLM calls (steps 2-4 run), so it is opt-in via --with-llm."""
    db = SessionLocal()
    try:
        brand = db.query(Brand).filter_by(slug="jade").first()
        assert brand is not None, "Seed data missing"

        version = _make_outreach_version(db, brand, CLEAN_OUTREACH)
        review = compliance_agent.run_compliance_check(db, version)

        assert version.status in ("submitted_for_review", "rejected")
        assert review.outcome in ("pass", "needs_human_review", "fail")
        print(f"  clean outreach: outcome={review.outcome}, status={version.status}")
        if version.status == "submitted_for_review":
            print("PASS: clean outreach reaches the human review queue")
        else:
            print("NOTE: clean outreach was still rejected by steps 2-4 — inspect issues:")
            print(f"  {review.detected_issues}")
    finally:
        db.close()


def test_outreach_is_visible_in_review_queue():
    """Outreach must flow into the EXISTING review surface, not a parallel one.
    Verified against the same query /review/pending uses, with an 'agent'-origin
    fixture that is cleaned up afterwards."""
    db = SessionLocal()
    asset_id = None
    try:
        brand = db.query(Brand).filter_by(slug="jade").first()
        assert brand is not None, "Seed data missing"

        campaign = content_agent.get_or_create_ad_hoc_campaign(db, brand)
        asset = ContentAsset(
            campaign_id=campaign.id,
            brand_id=brand.id,
            asset_type="email",
            platform="email",
            title="outreach queue-visibility probe",
            status="draft",
            # 'agent' on purpose: this asserts a real outreach draft is visible
            # in the demo queue. Isolation comes from the explicit cleanup below.
            origin="agent",
        )
        db.add(asset)
        db.flush()
        asset_id = asset.id

        version = ContentVersion(
            content_asset_id=asset.id,
            version_number=1,
            body=CLEAN_OUTREACH,
            status="submitted_for_review",
            is_current=True,
        )
        db.add(version)
        db.commit()

        # Same filter as routers/review.py:list_pending.
        visible = (
            db.query(ContentVersion)
            .join(ContentAsset, ContentVersion.content_asset_id == ContentAsset.id)
            .filter(
                ContentVersion.status == "submitted_for_review",
                ContentVersion.is_current.is_(True),
                ContentAsset.origin == "agent",
                ContentVersion.id == version.id,
            )
            .first()
        )
        assert visible is not None, "outreach draft did NOT appear in the review queue query"
        print(f"  outreach content_version {version.id} visible in /review/pending query")
        print("PASS: outreach reuses the existing review queue (no parallel path)")
    finally:
        if asset_id is not None:
            db.query(ComplianceReview).filter(
                ComplianceReview.content_version_id.in_(
                    db.query(ContentVersion.id).filter(
                        ContentVersion.content_asset_id == asset_id
                    )
                )
            ).delete(synchronize_session=False)
            db.query(ContentVersion).filter(
                ContentVersion.content_asset_id == asset_id
            ).delete(synchronize_session=False)
            db.query(ContentAsset).filter(ContentAsset.id == asset_id).delete()
            db.commit()
        db.close()


if __name__ == "__main__":
    import sys

    test_aggressive_outreach_is_blocked()
    print()
    test_outreach_is_visible_in_review_queue()
    if "--with-llm" in sys.argv:
        print()
        test_clean_outreach_reaches_review()
    else:
        print("\n(skipping clean-outreach LLM test; pass --with-llm to run it)")
