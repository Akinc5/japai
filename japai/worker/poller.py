from datetime import datetime, timezone
import logging
from typing import Any
import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session

from apps.api.models import Analytics, ContentAsset, ContentVersion, PublishingJob
from worker.config import worker_settings
from worker.db import get_db_session
from worker.publishers import BasePublisher, PublishRequest, PublishResult, get_publisher

logger = logging.getLogger("ja_assure.worker.poller")

# Status semantics:
#   pending   — in OUR queue. scheduled_at (optional) is when we should publish.
#   scheduled — already HANDED TO THE PROVIDER, which will post it later.
# Only 'pending' is claimable. Claiming 'scheduled' re-sent every due job to the
# provider on every poll, which with a real Buffer token meant a new post every
# POLL_INTERVAL_SECONDS, indefinitely.
CLAIMABLE_STATUSES = ("pending",)


def provider_scheduled_at(job: PublishingJob, now: datetime) -> datetime | None:
    """The scheduled_at to hand the provider: only a time still in the future.

    Jobs are claimed once due, so their scheduled_at is normally already past.
    Passing a past time through makes the provider report 'scheduled' for a
    post that should go out now, leaving the job parked in 'scheduled' forever.
    """
    if job.scheduled_at is not None and job.scheduled_at > now:
        return job.scheduled_at
    return None


def apply_metrics(
    existing: list[Analytics],
    job: PublishingJob,
    campaign_id: uuid.UUID | None,
    metrics: Any,
    now: datetime,
) -> tuple[list[Analytics], list[Analytics]]:
    """Keep exactly ONE analytics row per (content_asset, platform, metric).

    `existing` is every analytics row already stored for this job's asset and
    platform. Each sync refreshes those rows in place instead of appending. The
    optimization agent counts engagement_rate rows as posts, so appending a
    fresh set on every sync made one published post read as N posts after N
    syncs (observed: +6 rows per post every 30s).

    Returns (rows_to_add, duplicate_rows_to_delete). Duplicates left behind by
    earlier append-only syncs are collapsed so the table heals on next sync.
    """
    values = {
        "impressions": metrics.impressions,
        "likes": metrics.likes,
        "clicks": metrics.clicks,
        "comments": metrics.comments,
        "shares": metrics.shares,
        "engagement_rate": metrics.engagement_rate,
    }

    by_metric: dict[str, list[Analytics]] = {}
    for row in existing:
        by_metric.setdefault(row.metric_name, []).append(row)

    to_add: list[Analytics] = []
    to_delete: list[Analytics] = []
    for name, val in values.items():
        rows = by_metric.get(name, [])
        if rows:
            keep, *extra = rows
            keep.metric_value = float(val)
            keep.is_simulated = metrics.is_simulated
            keep.campaign_id = campaign_id
            keep.recorded_at = now
            to_delete.extend(extra)
        else:
            to_add.append(
                Analytics(
                    content_asset_id=job.content_asset_id,
                    campaign_id=campaign_id,
                    metric_name=name,
                    metric_value=float(val),
                    platform=job.platform,
                    is_simulated=metrics.is_simulated,
                    recorded_at=now,
                )
            )
    return to_add, to_delete


class PublishingWorker:
    """Core poller and orchestrator for social content auto-publishing.

    Guarantees:
    - Atomicity & Idempotency: Uses row-level locking (SKIP LOCKED) to claim jobs.
    - Full Status Lifecycle: pending (once due) -> publishing -> published / scheduled / failed.
      'scheduled' means the provider accepted it for later posting; it is terminal here.
    - Zero Corruption: On failure, preserves the row and records descriptive error details.
    - Analytics Pull-back: Integrates published post metrics with the analytics table.
    """

    def __init__(self, publisher: BasePublisher | None = None, batch_size: int | None = None):
        self.publisher = publisher or get_publisher()
        self.batch_size = batch_size or worker_settings.BATCH_SIZE

    def claim_jobs(self, db: Session) -> list[PublishingJob]:
        """Atomically finds and locks due jobs, transitioning them to 'publishing'.
        Uses SELECT FOR UPDATE SKIP LOCKED to prevent duplicate execution across workers."""
        now = datetime.now(timezone.utc)

        # 1. Query candidate jobs that are ready to be published
        jobs = (
            db.query(PublishingJob)
            .filter(
                PublishingJob.status.in_(CLAIMABLE_STATUSES),
                or_(
                    PublishingJob.scheduled_at.is_(None),
                    PublishingJob.scheduled_at <= now,
                ),
            )
            .order_by(PublishingJob.created_at.asc())
            .limit(self.batch_size)
            .with_for_update(skip_locked=True)
            .all()
        )

        if not jobs:
            return []

        # 2. Transition claimed jobs to 'publishing' so subsequent polls skip them
        claimed = []
        for job in jobs:
            job.status = "publishing"
            claimed.append(job)

        db.commit()
        for job in claimed:
            db.refresh(job)

        logger.info("Claimed %d publishing job(s)", len(claimed))
        return claimed

    def process_job(self, db: Session, job: PublishingJob) -> PublishResult:
        """Executes publishing for a single claimed job and records the outcome."""
        logger.info(
            "Processing job %s: platform=%s, content_version_id=%s",
            job.id,
            job.platform,
            job.content_version_id,
        )

        # 1. Load content text from ContentVersion
        version = db.get(ContentVersion, job.content_version_id)
        if not version:
            err = f"Linked ContentVersion '{job.content_version_id}' not found in database."
            job.status = "failed"
            job.error_message = err
            db.commit()
            return PublishResult(success=False, status="failed", error_message=err)

        content_body = (version.body or "").strip()
        if not content_body:
            err = f"Linked ContentVersion '{job.content_version_id}' has empty body text."
            job.status = "failed"
            job.error_message = err
            db.commit()
            return PublishResult(success=False, status="failed", error_message=err)

        # 2. Build publish request
        metadata = dict(version.version_metadata or {})
        req = PublishRequest(
            job_id=job.id,
            platform=job.platform,
            text=content_body,
            scheduled_at=provider_scheduled_at(job, datetime.now(timezone.utc)),
            metadata=metadata,
        )

        # 3. Dispatch to social publisher
        try:
            result = self.publisher.publish(req)
        except Exception as exc:
            logger.error("Publisher raised unexpected exception on job %s: %s", job.id, exc)
            result = PublishResult(
                success=False,
                status="failed",
                error_message=f"Publisher raised unhandled exception ({type(exc).__name__}): {str(exc)}",
            )

        # 4. Update job status in database
        now = datetime.now(timezone.utc)
        if result.success:
            if result.status == "scheduled":
                job.status = "scheduled"
                job.external_post_id = result.external_post_id
                job.error_message = None
            else:
                job.status = "published"
                job.published_at = now
                job.external_post_id = result.external_post_id
                job.error_message = None
            logger.info("Job %s succeeded: status=%s, external_id=%s", job.id, job.status, job.external_post_id)
        else:
            job.status = "failed"
            job.error_message = result.error_message or "Publishing failed without specific error message."
            logger.warning("Job %s failed: %s", job.id, job.error_message)

        db.commit()
        db.refresh(job)
        return result

    def poll_once(self) -> dict[str, int]:
        """Runs a single polling sweep against the database."""
        db = get_db_session()
        stats = {"claimed": 0, "published": 0, "scheduled": 0, "failed": 0}

        try:
            jobs = self.claim_jobs(db)
            stats["claimed"] = len(jobs)

            for job in jobs:
                res = self.process_job(db, job)
                if res.success:
                    if res.status == "scheduled":
                        stats["scheduled"] += 1
                    else:
                        stats["published"] += 1
                else:
                    stats["failed"] += 1

            return stats
        finally:
            db.close()

    def sync_analytics(self, limit: int = 10) -> int:
        """Polls provider for engagement metrics for published jobs and writes to analytics table."""
        db = get_db_session()
        synced_count = 0

        try:
            # Query recently published jobs with external IDs
            published_jobs = (
                db.query(PublishingJob)
                .filter(
                    PublishingJob.status == "published",
                    PublishingJob.external_post_id.isnot(None),
                )
                .order_by(PublishingJob.published_at.desc())
                .limit(limit)
                # analytics has no unique key (adding one needs a migration), so
                # lock the job row: two workers can't sync the same post at once
                # and both insert a "first" row set.
                .with_for_update(skip_locked=True)
                .all()
            )

            for job in published_jobs:
                metrics = self.publisher.fetch_analytics(job.external_post_id, job.platform)
                if not metrics:
                    continue

                asset = db.get(ContentAsset, job.content_asset_id)
                campaign_id = asset.campaign_id if asset else None

                existing = (
                    db.query(Analytics)
                    .filter(
                        Analytics.content_asset_id == job.content_asset_id,
                        Analytics.platform == job.platform,
                    )
                    .order_by(Analytics.created_at.asc())
                    .all()
                )
                to_add, to_delete = apply_metrics(
                    existing, job, campaign_id, metrics, datetime.now(timezone.utc)
                )
                for row in to_add:
                    db.add(row)
                for row in to_delete:
                    db.delete(row)
                synced_count += 1

            db.commit()
            logger.info("Synced engagement analytics for %d published job(s)", synced_count)
            return synced_count
        finally:
            db.close()
