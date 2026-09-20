from dotenv import load_dotenv

load_dotenv()

from apps.api.agents import compliance as compliance_agent
from apps.api.agents import content as content_agent
from apps.api.core.db import SessionLocal
from apps.api.models import Brand, ContentAsset, ContentVersion


def test_generate_and_pass():
    db = SessionLocal()
    try:
        brand = db.query(Brand).filter_by(slug="jade").first()
        assert brand is not None, "Seed data missing — run `python -m db.seed.seed_brands` first"

        version = content_agent.generate_content(
            db, brand_id=brand.id, platform="linkedin", topic="jewellery inventory risk"
        )
        review = compliance_agent.run_compliance_check(db, version)

        print("--- Generated LinkedIn post (Jade) ---")
        print(version.body)
        print(f"\nversion.status={version.status}  outcome={review.outcome}  issues={review.detected_issues}")
    finally:
        db.close()


def test_blocklist_blocks():
    db = SessionLocal()
    try:
        brand = db.query(Brand).filter_by(slug="jade").first()
        assert brand is not None, "Seed data missing — run `python -m db.seed.seed_brands` first"

        campaign = content_agent.get_or_create_ad_hoc_campaign(db, brand)

        asset = ContentAsset(
            campaign_id=campaign.id,
            brand_id=brand.id,
            asset_type="social_post",
            platform="linkedin",
            status="draft",
            origin="test_fixture",
        )
        db.add(asset)
        db.flush()

        version = ContentVersion(
            content_asset_id=asset.id,
            version_number=1,
            body="Our jewellers block policy is guaranteed to pay every claim, no exceptions.",
            status="draft",
            is_current=True,
        )
        db.add(version)
        db.flush()

        review = compliance_agent.run_compliance_check(db, version)

        assert review.outcome == "fail"
        assert version.status == "rejected"
        assert any(issue["term"] == "guaranteed" for issue in review.detected_issues)

        print("Blocklist regression test passed: outcome=fail, status=rejected")
        print(review.detected_issues)
    finally:
        db.close()


if __name__ == "__main__":
    test_generate_and_pass()
    print()
    test_blocklist_blocks()
