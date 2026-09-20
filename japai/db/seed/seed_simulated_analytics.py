"""Seed SIMULATED engagement data for the optimization agent.

SCOPE HONESTY — nothing here is real performance data.

There is no publishing pipeline and no live engagement feed. Every number below
is fabricated by this script. The posts it attaches them to are also fabricated:
they are written as `content_assets` with `origin='simulated'`, which the
metrics / review-queue / lessons queries all exclude (they whitelist
`origin='agent'`), so simulated posts can never inflate the real rejection rate.
Every analytics row carries `is_simulated=true`.

What is real is the loop around the data: the optimization agent aggregates
these rows deterministically and turns the aggregate into insights that feed
back into content generation.

TWO PATTERNS ARE DELIBERATELY BAKED IN, for the agent to discover:
  1. educational angle outperforms promotional angle
  2. a short hook outperforms a long intro
They are applied as effects on engagement_rate below, with pseudo-random noise
so the signal has to survive being averaged rather than being trivially exact.
The agent is NOT told these patterns — it computes group averages and reports
what it finds. Changing the effects here should change the insights it produces.

NOTE ON `angle` / `hook_style`: these tags exist because this seeder writes them
into content_versions.metadata. Real agent-generated content does NOT carry
them, so this correlation currently works on seeded posts only. Inferring angle
from real generated copy is not built.

Usage:
    docker compose exec api python -m db.seed.seed_simulated_analytics
    docker compose exec api python -m db.seed.seed_simulated_analytics --clear
"""
import random
import sys

from dotenv import load_dotenv

load_dotenv()

from apps.api.core.db import SessionLocal
from apps.api.models import Analytics, Brand, Campaign, ContentAsset, ContentVersion

CAMPAIGN_NAME = "Simulated Performance Data (not real)"
SIMULATED_ORIGIN = "simulated"
RANDOM_SEED = 20260914  # fixed so the dataset is reproducible run to run

# --- the baked-in pattern -------------------------------------------------
BASE_ENGAGEMENT = 2.0  # percent
EDUCATIONAL_EFFECT = 1.8  # percentage points
SHORT_HOOK_EFFECT = 0.9  # percentage points
NOISE = 0.45  # +/- percentage points

PLATFORM_IMPRESSIONS = {
    "linkedin": (5000, 11000),
    "instagram": (3500, 9000),
    "x": (2500, 7000),
}

# 20 posts: a 2x2 of angle x hook_style across 3 platforms, deliberately not
# balanced perfectly so the aggregate isn't a contrived exact split.
POSTS: list[dict] = [
    # (title, platform, angle, hook_style)
    ("How jewellers block cover responds to a showroom theft", "linkedin", "educational", "short_hook"),
    ("What 'stock in transit' actually means on your policy", "linkedin", "educational", "short_hook"),
    ("Three exclusions independent jewellers miss", "linkedin", "educational", "short_hook"),
    ("Understanding valuation at the time of loss", "linkedin", "educational", "long_intro"),
    ("A walkthrough of the claims process, end to end", "linkedin", "educational", "long_intro"),
    ("Why exhibition cover is priced separately", "instagram", "educational", "short_hook"),
    ("Safe-storage requirements, explained simply", "instagram", "educational", "short_hook"),
    ("What underwriters look for in a stock declaration", "instagram", "educational", "long_intro"),
    ("The difference between agreed value and market value", "x", "educational", "short_hook"),
    ("How transit limits are calculated", "x", "educational", "long_intro"),
    ("Protect your stock with Jade today", "linkedin", "promotional", "short_hook"),
    ("Speak to a Jade specialist this week", "linkedin", "promotional", "short_hook"),
    ("Jade: specialist cover for Singapore jewellers", "linkedin", "promotional", "long_intro"),
    ("Request a tailored jewellers block quote", "linkedin", "promotional", "long_intro"),
    ("Trusted by independent jewellers island-wide", "instagram", "promotional", "short_hook"),
    ("Book a cover review with our team", "instagram", "promotional", "long_intro"),
    ("Specialist cover, built around your trade", "instagram", "promotional", "long_intro"),
    ("Get covered before your next exhibition", "x", "promotional", "short_hook"),
    ("Talk to Jade about your stock cover", "x", "promotional", "long_intro"),
    ("Your trade deserves a specialist insurer", "x", "promotional", "long_intro"),
]


def _engagement_rate(angle: str, hook_style: str, rng: random.Random) -> float:
    rate = BASE_ENGAGEMENT
    if angle == "educational":
        rate += EDUCATIONAL_EFFECT
    if hook_style == "short_hook":
        rate += SHORT_HOOK_EFFECT
    rate += rng.uniform(-NOISE, NOISE)
    return round(max(rate, 0.1), 2)


def clear(db) -> int:
    """Remove previously seeded simulated posts. Analytics rows cascade from
    content_assets, so deleting the assets is sufficient."""
    assets = db.query(ContentAsset).filter(ContentAsset.origin == SIMULATED_ORIGIN).all()
    n = len(assets)
    for asset in assets:
        db.delete(asset)
    campaign = db.query(Campaign).filter(Campaign.name == CAMPAIGN_NAME).first()
    if campaign is not None:
        db.delete(campaign)
    db.commit()
    return n


def run(clear_first: bool = True) -> dict:
    db = SessionLocal()
    rng = random.Random(RANDOM_SEED)
    try:
        brand = db.query(Brand).filter_by(slug="jade").first()
        if brand is None:
            raise SystemExit("Jade brand missing — run `python -m db.seed.seed_brands` first")

        if clear_first:
            removed = clear(db)
            if removed:
                print(f"  cleared {removed} previously simulated post(s)")

        campaign = Campaign(
            brand_id=brand.id,
            name=CAMPAIGN_NAME,
            objective="Container for fabricated engagement data used by the optimization agent.",
            status="active",
        )
        db.add(campaign)
        db.flush()

        rows = 0
        for title, platform, angle, hook_style in POSTS:
            asset = ContentAsset(
                campaign_id=campaign.id,
                brand_id=brand.id,
                asset_type="social_post",
                platform=platform,
                title=title,
                status="approved",
                created_by="simulated_seed",
                # Excluded from every real metric by the origin whitelist.
                origin=SIMULATED_ORIGIN,
            )
            db.add(asset)
            db.flush()

            db.add(
                ContentVersion(
                    content_asset_id=asset.id,
                    version_number=1,
                    body=f"[SIMULATED POST] {title}",
                    version_metadata={
                        "simulated": True,
                        "angle": angle,
                        "hook_style": hook_style,
                        "platform": platform,
                    },
                    generated_by_agent="simulated_seed",
                    status="approved",
                    is_current=True,
                )
            )

            lo, hi = PLATFORM_IMPRESSIONS[platform]
            impressions = rng.randint(lo, hi)
            engagement_rate = _engagement_rate(angle, hook_style, rng)
            # Clicks follow engagement with a mild independent CTR wobble.
            clicks = int(impressions * (engagement_rate / 100) * rng.uniform(0.25, 0.45))

            for metric_name, metric_value in (
                ("impressions", impressions),
                ("engagement_rate", engagement_rate),
                ("clicks", clicks),
            ):
                db.add(
                    Analytics(
                        content_asset_id=asset.id,
                        campaign_id=campaign.id,
                        metric_name=metric_name,
                        metric_value=metric_value,
                        platform=platform,
                        is_simulated=True,
                    )
                )
                rows += 1

        db.commit()
        print(f"Seeded {len(POSTS)} simulated posts and {rows} analytics rows (all is_simulated=true).")
        return {"posts": len(POSTS), "analytics_rows": rows}
    finally:
        db.close()


def main() -> None:
    if "--clear" in sys.argv:
        db = SessionLocal()
        try:
            n = clear(db)
            print(f"Cleared {n} simulated post(s) and their analytics.")
        finally:
            db.close()
        return
    run()


if __name__ == "__main__":
    main()
