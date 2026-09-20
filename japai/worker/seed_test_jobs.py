"""Seeder utility for Project 2 worker testing and verification.

Creates self-contained test records:
1. An approved ContentAsset + ContentVersion (tagged origin='test_fixture').
2. A pending PublishingJob for immediate publishing.
3. A scheduled PublishingJob with a future scheduled_at time.
4. A deliberate failure test PublishingJob (unsupported platform / fail trigger).

Usage:
    python -m worker.seed_test_jobs
"""
from datetime import datetime, timedelta, timezone
from typing import Any
import uuid

from apps.api.models import Brand, Campaign, ContentAsset, ContentVersion, PublishingJob
from worker.db import get_db_session


def seed_test_publishing_data(db=None) -> dict[str, Any]:
    close_db = False
    if db is None:
        db = get_db_session()
        close_db = True

    try:
        # Find or create a brand
        brand = db.query(Brand).first()
        if not brand:
            brand = Brand(
                name="Jade",
                slug="jade",
                description="Jewellers block insurance for Singapore jewellers and goldsmiths.",
            )
            db.add(brand)
            db.flush()

        # Find or create a test campaign
        campaign = (
            db.query(Campaign)
            .filter_by(brand_id=brand.id, name="Project 2 Worker Test Campaign")
            .first()
        )
        if not campaign:
            campaign = Campaign(
                brand_id=brand.id,
                name="Project 2 Worker Test Campaign",
                objective="Test campaign for auto-publishing worker",
                status="active",
            )
            db.add(campaign)
            db.flush()

        # 1. Normal valid post asset & version
        asset_valid = ContentAsset(
            campaign_id=campaign.id,
            brand_id=brand.id,
            asset_type="social_post",
            platform="linkedin",
            title="[Worker Test] Security & Transit Protocols for Fine Jewellers",
            status="approved",
            created_by="test_harness",
            origin="test_fixture",
            language="en",
        )
        db.add(asset_valid)
        db.flush()

        version_valid = ContentVersion(
            content_asset_id=asset_valid.id,
            version_number=1,
            body=(
                "Transporting high-value gemstones requires more than standard courier arrangements. "
                "At Jade, we provide specialized jewellers block coverage tailored for Singapore's fine jewelry trade. "
                "Learn how our transit warranties safeguard your inventory."
            ),
            version_metadata={"test": True, "topic": "transit_security"},
            generated_by_agent="test_harness",
            status="approved",
            is_current=True,
        )
        db.add(version_valid)
        db.flush()

        job_valid = PublishingJob(
            content_asset_id=asset_valid.id,
            content_version_id=version_valid.id,
            platform="linkedin",
            status="pending",
            scheduled_at=None,
        )
        db.add(job_valid)

        # 2. Scheduled post for tomorrow
        asset_scheduled = ContentAsset(
            campaign_id=campaign.id,
            brand_id=brand.id,
            asset_type="social_post",
            platform="linkedin",
            title="[Worker Test] Scheduled Exhibition Cover Update",
            status="approved",
            created_by="test_harness",
            origin="test_fixture",
            language="en",
        )
        db.add(asset_scheduled)
        db.flush()

        version_scheduled = ContentVersion(
            content_asset_id=asset_scheduled.id,
            version_number=1,
            body="Upcoming trade show season in Marina Bay Sands: ensure your exhibition stock extensions are verified in advance.",
            status="approved",
            is_current=True,
        )
        db.add(version_scheduled)
        db.flush()

        job_scheduled = PublishingJob(
            content_asset_id=asset_scheduled.id,
            content_version_id=version_scheduled.id,
            platform="linkedin",
            # 'pending' + a future scheduled_at is how local scheduling is
            # expressed; 'scheduled' means already handed to the provider.
            status="pending",
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        db.add(job_scheduled)

        # 3. Deliberate failure test (unsupported platform)
        asset_failing = ContentAsset(
            campaign_id=campaign.id,
            brand_id=brand.id,
            asset_type="social_post",
            platform="myspace_unsupported",
            title="[Worker Test] Intentional Failure Case",
            status="approved",
            created_by="test_harness",
            origin="test_fixture",
            language="en",
        )
        db.add(asset_failing)
        db.flush()

        version_failing = ContentVersion(
            content_asset_id=asset_failing.id,
            version_number=1,
            body="[SIMULATE_FAIL] This post intentionally tests the worker's failure state handling.",
            status="approved",
            is_current=True,
        )
        db.add(version_failing)
        db.flush()

        job_failing = PublishingJob(
            content_asset_id=asset_failing.id,
            content_version_id=version_failing.id,
            platform="myspace_unsupported",
            status="pending",
            scheduled_at=None,
        )
        db.add(job_failing)

        db.commit()
        db.refresh(job_valid)
        db.refresh(job_scheduled)
        db.refresh(job_failing)

        result = {
            "valid_job_id": str(job_valid.id),
            "scheduled_job_id": str(job_scheduled.id),
            "failing_job_id": str(job_failing.id),
        }
        print(f"Seeded test publishing jobs successfully:")
        print(f"  - Ready job:     {result['valid_job_id']} (status=pending, platform=linkedin)")
        print(f"  - Scheduled job: {result['scheduled_job_id']} (status=pending, due tomorrow)")
        print(f"  - Failing job:   {result['failing_job_id']} (status=pending, platform=myspace_unsupported)")
        return result
    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    from typing import Any
    seed_test_publishing_data()
