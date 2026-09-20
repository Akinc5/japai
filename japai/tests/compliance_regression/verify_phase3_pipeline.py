from dotenv import load_dotenv

load_dotenv()

from apps.api.agents import compliance as compliance_agent
from apps.api.agents import content as content_agent
from apps.api.core.db import SessionLocal
from apps.api.models import Brand, ContentAsset, ContentVersion

# None of these contain a Step-1 blocklisted phrase — they exercise the LLM-based
# claim extraction / verification / review steps (2-4), not the deterministic scan.
KNOWN_BAD_PHRASINGS = [
    "Our jewellers block policy covers every type of loss without any exclusions.",
    "Jade approves 100% of claims submitted by loyal customers.",
    "With Jade, you'll never have to worry about theft again.",
    "Our coverage is better than any other insurer in Singapore.",
    "Sign up today before this exclusive rate disappears forever!",
    "Jade's policy includes automatic coverage upgrades every year at no extra cost.",
    "We are the #1 choice for jewellers insurance in Asia.",
    "Every claim is settled within 24 hours, no matter the complexity.",
    "Jade protects your entire inventory from any conceivable risk.",
    "We pride ourselves on approving claims that other insurers might reject.",
    "This offer is only available for the next 48 hours, don't miss out.",
    "Jade covers your jewellery no matter where in the world it's lost or stolen.",
]


def test_known_bad_phrasings_are_flagged():
    db = SessionLocal()
    try:
        brand = db.query(Brand).filter_by(slug="jade").first()
        assert brand is not None, "Seed data missing — run `python -m db.seed.seed_brands` first"

        campaign = content_agent.get_or_create_ad_hoc_campaign(db, brand)
        failures = []

        for i, body in enumerate(KNOWN_BAD_PHRASINGS):
            assert not compliance_agent._scan_blocklist(body), (
                f"Fixture {i} accidentally contains a blocklisted phrase: {body!r}"
            )

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
                body=body,
                status="draft",
                is_current=True,
            )
            db.add(version)
            db.flush()

            review = compliance_agent.run_compliance_check(db, version)
            risk_level = compliance_agent.RISK_LEVEL_BY_OUTCOME.get(review.outcome, "review")

            status = "OK" if risk_level != "pass" else "FAIL"
            print(f"[{status}] risk_level={risk_level:6s} | {body}")
            if risk_level == "pass":
                failures.append(body)

        print(f"\n{len(KNOWN_BAD_PHRASINGS) - len(failures)}/{len(KNOWN_BAD_PHRASINGS)} fixtures flagged as review/block.")
        assert not failures, f"{len(failures)} fixture(s) incorrectly passed: {failures}"
    finally:
        db.close()


if __name__ == "__main__":
    test_known_bad_phrasings_are_flagged()
