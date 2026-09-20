"""Pure DB/logic test for the optimization aggregation — makes NO LLM calls.

Asserts that the aggregation actually recovers the effects the seeder baked in.
This is the guard against the agent "finding" patterns that aren't in the data:
if someone changes the seed effects, this test changes with them, and if the
aggregation breaks, the insight text would silently keep sounding plausible.

Runs against an isolated throwaway brand so it never touches the demo dataset.
"""
from dotenv import load_dotenv

load_dotenv()

from apps.api.agents import optimization as optimization_agent
from apps.api.core.db import SessionLocal
from apps.api.models import (
    Analytics,
    Brand,
    Campaign,
    ContentAsset,
    ContentVersion,
    Organization,
)

# (angle, hook_style, engagement_rate) — educational and short_hook are set
# clearly higher so the assertions test the aggregation, not the noise model.
FIXTURES = [
    ("educational", "short_hook", 5.0),
    ("educational", "short_hook", 5.4),
    ("educational", "long_intro", 3.6),
    ("educational", "long_intro", 3.4),
    ("promotional", "short_hook", 2.8),
    ("promotional", "short_hook", 3.0),
    ("promotional", "long_intro", 1.6),
    ("promotional", "long_intro", 1.4),
]


def test_aggregation_recovers_seeded_effects():
    db = SessionLocal()
    org = None
    try:
        org = Organization(name="Optimization Test Org")
        db.add(org)
        db.flush()

        brand = Brand(
            organization_id=org.id,
            name="Optimization Test Brand",
            slug=f"opt-test-{org.id.hex[:8]}",
            target_audience="Test audience",
        )
        db.add(brand)
        db.flush()

        campaign = Campaign(brand_id=brand.id, name="Opt Test Campaign", status="active")
        db.add(campaign)
        db.flush()

        for i, (angle, hook, rate) in enumerate(FIXTURES):
            asset = ContentAsset(
                campaign_id=campaign.id,
                brand_id=brand.id,
                asset_type="social_post",
                platform="linkedin",
                status="approved",
                origin="simulated",
            )
            db.add(asset)
            db.flush()

            db.add(
                ContentVersion(
                    content_asset_id=asset.id,
                    version_number=1,
                    body=f"fixture {i}",
                    version_metadata={"angle": angle, "hook_style": hook},
                    status="approved",
                    is_current=True,
                )
            )
            db.add(
                Analytics(
                    content_asset_id=asset.id,
                    campaign_id=campaign.id,
                    metric_name="engagement_rate",
                    metric_value=rate,
                    platform="linkedin",
                    is_simulated=True,
                )
            )
        db.commit()

        aggregate = optimization_agent.aggregate_performance(db, brand.id)

        by_angle = {r["bucket"]: r for r in aggregate["groups"]["angle"]}
        by_hook = {r["bucket"]: r for r in aggregate["groups"]["hook_style"]}

        # Expected means straight from FIXTURES: educational (5.0+5.4+3.6+3.4)/4 = 4.35,
        # promotional (2.8+3.0+1.6+1.4)/4 = 2.20
        assert by_angle["educational"]["avg_engagement_rate"] == 4.35, by_angle
        assert by_angle["promotional"]["avg_engagement_rate"] == 2.20, by_angle
        # short_hook (5.0+5.4+2.8+3.0)/4 = 4.05, long_intro (3.6+3.4+1.6+1.4)/4 = 2.50
        assert by_hook["short_hook"]["avg_engagement_rate"] == 4.05, by_hook
        assert by_hook["long_intro"]["avg_engagement_rate"] == 2.50, by_hook
        print("Group averages OK:", {k: v["avg_engagement_rate"] for k, v in by_angle.items()})

        # Ordering matters: the agent presents strongest-first.
        assert aggregate["groups"]["angle"][0]["bucket"] == "educational"
        assert aggregate["groups"]["hook_style"][0]["bucket"] == "short_hook"
        print("Ordering OK: strongest bucket first in each dimension")

        assert aggregate["analytics_are_simulated"] is True
        assert all(r["posts"] == 4 for r in aggregate["groups"]["angle"])
        print("Counts + simulated flag OK")

        # A real (non-simulated) row must flip the honesty flag.
        real_asset = db.query(ContentAsset).filter(ContentAsset.brand_id == brand.id).first()
        db.add(
            Analytics(
                content_asset_id=real_asset.id,
                metric_name="engagement_rate",
                metric_value=9.9,
                platform="linkedin",
                is_simulated=False,
            )
        )
        db.commit()
        assert optimization_agent.aggregate_performance(db, brand.id)["analytics_are_simulated"] is False
        print("Simulated flag correctly flips when a real row exists")

        print("\nPASS: optimization aggregation")
    finally:
        if org is not None:
            db.query(Organization).filter(Organization.id == org.id).delete()
            db.commit()
        db.close()


def test_non_whitelisted_origins_do_not_move_aggregate():
    """Regression: worker `--seed` creates origin='test_fixture' posts and its
    analytics sync writes simulated metrics for them. Those rows were counted,
    moving Jade's LinkedIn bucket from 9 posts / 3.40% to 10 / 3.82%. Only
    AGGREGATED_ORIGINS may contribute; test_fixture and manual must not."""
    db = SessionLocal()
    org = None
    try:
        org = Organization(name="Optimization Origin Test Org")
        db.add(org)
        db.flush()
        brand = Brand(
            organization_id=org.id,
            name="Optimization Origin Test Brand",
            slug=f"opt-origin-{org.id.hex[:8]}",
            target_audience="Test audience",
        )
        db.add(brand)
        db.flush()
        campaign = Campaign(brand_id=brand.id, name="Opt Origin Campaign", status="active")
        db.add(campaign)
        db.flush()

        def add_post(origin: str, rate: float, is_simulated: bool = True) -> None:
            asset = ContentAsset(
                campaign_id=campaign.id,
                brand_id=brand.id,
                asset_type="social_post",
                platform="linkedin",
                status="approved",
                origin=origin,
            )
            db.add(asset)
            db.flush()
            db.add(
                ContentVersion(
                    content_asset_id=asset.id,
                    version_number=1,
                    body=f"{origin} post",
                    version_metadata={"angle": "educational", "hook_style": "short_hook"},
                    status="approved",
                    is_current=True,
                )
            )
            db.add(
                Analytics(
                    content_asset_id=asset.id,
                    campaign_id=campaign.id,
                    metric_name="engagement_rate",
                    metric_value=rate,
                    platform="linkedin",
                    is_simulated=is_simulated,
                )
            )

        add_post("simulated", 3.0)
        add_post("simulated", 4.0)
        db.commit()
        before = optimization_agent.aggregate_performance(db, brand.id)

        # Wildly different values, one of them non-simulated, so any leak shows
        # up in posts, averages, totals AND the simulated flag.
        add_post("test_fixture", 50.0)
        add_post("manual", 90.0, is_simulated=False)
        db.commit()
        after = optimization_agent.aggregate_performance(db, brand.id)

        assert after["groups"] == before["groups"], (before["groups"], after["groups"])
        assert after["totals"] == before["totals"], (before["totals"], after["totals"])
        assert after["analytics_are_simulated"] is True
        assert after["groups"]["platform"] == [
            {"bucket": "linkedin", "posts": 2, "avg_engagement_rate": 3.5}
        ], after["groups"]["platform"]
        print("test_fixture / manual posts excluded from groups, totals and simulated flag")

        print("\nPASS: optimization origin whitelist")
    finally:
        if org is not None:
            db.query(Organization).filter(Organization.id == org.id).delete()
            db.commit()
        db.close()


if __name__ == "__main__":
    test_aggregation_recovers_seeded_effects()
    test_non_whitelisted_origins_do_not_move_aggregate()
