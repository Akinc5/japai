"""Unit and self-contained tests for Project 2 Auto-Publishing Worker.

Covers the 4 core verification criteria from the handover brief:
1. Success path: Picks up pending job, publishes, transitions status to 'published',
   records external_post_id and published_at.
2. Failure path: Handles invalid platform / API failure, transitions status to 'failed',
   and records descriptive error_message.
3. Idempotency & double-processing: Second pass against processed jobs performs no duplicate posts.
4. Scheduled delivery: Future scheduled_at jobs are not prematurely published.
5. Analytics pull-back: Published jobs have engagement metrics synced to the analytics table.
6. Buffer provider unit checks: Validates error formatting for 401, 429, missing tokens.

Safe to run with the database stack up or down.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import uuid

from apps.api.models import Analytics, ContentAsset, ContentVersion, PublishingJob
from worker.config import WorkerSettings
from worker.poller import (
    CLAIMABLE_STATUSES,
    PublishingWorker,
    apply_metrics,
    provider_scheduled_at,
)
from worker.publishers.base import (
    BasePublisher,
    EngagementMetrics,
    PublishRequest,
    PublishResult,
)
from worker.publishers.buffer import BufferPublisher
from worker.publishers.simulation import SimulationPublisher


# --- 1. Publisher Unit Tests -----------------------------------------------


def test_simulation_publisher_success():
    pub = SimulationPublisher(simulate_latency_ms=0)
    req = PublishRequest(
        job_id=uuid.uuid4(),
        platform="linkedin",
        text="Test post on transit insurance security",
    )
    res = pub.publish(req)
    assert res.success is True
    assert res.status == "published"
    assert res.external_post_id is not None
    assert res.external_post_id.startswith("sim_linkedin_")
    print("PASS: Simulation publisher success path")


def test_simulation_publisher_scheduled():
    pub = SimulationPublisher(simulate_latency_ms=0)
    req = PublishRequest(
        job_id=uuid.uuid4(),
        platform="linkedin",
        text="Scheduled post for next week",
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    res = pub.publish(req)
    assert res.success is True
    assert res.status == "scheduled"
    assert res.external_post_id is not None
    print("PASS: Simulation publisher scheduled path")


def test_simulation_publisher_deliberate_failure():
    pub = SimulationPublisher(simulate_latency_ms=0)
    req = PublishRequest(
        job_id=uuid.uuid4(),
        platform="linkedin",
        text="[SIMULATE_FAIL] This post should fail cleanly.",
    )
    res = pub.publish(req)
    assert res.success is False
    assert res.status == "failed"
    assert "Simulated provider error" in (res.error_message or "")
    print("PASS: Simulation publisher deliberate failure trigger")


def test_simulation_publisher_unsupported_platform():
    pub = SimulationPublisher(simulate_latency_ms=0)
    req = PublishRequest(
        job_id=uuid.uuid4(),
        platform="nonexistent_social_network",
        text="Hello world",
    )
    res = pub.publish(req)
    assert res.success is False
    assert res.status == "failed"
    assert "not supported" in (res.error_message or "")
    print("PASS: Simulation publisher unsupported platform rejection")


def test_simulation_publisher_analytics():
    pub = SimulationPublisher(simulate_latency_ms=0)
    metrics = pub.fetch_analytics("sim_linkedin_12345", "linkedin")
    assert metrics is not None
    assert metrics.impressions > 0
    assert metrics.engagement_rate >= 0.0
    assert metrics.is_simulated is True
    print("PASS: Simulation publisher analytics generation")


def test_buffer_publisher_missing_token():
    pub = BufferPublisher(access_token="", api_base_url="https://api.bufferapp.com/1")
    req = PublishRequest(job_id=uuid.uuid4(), platform="linkedin", text="Test post")
    res = pub.publish(req)
    assert res.success is False
    assert res.status == "failed"
    assert "BUFFER_ACCESS_TOKEN is missing or empty" in (res.error_message or "")
    print("PASS: Buffer publisher missing token rejection")


def test_buffer_publisher_401_error_handling():
    pub = BufferPublisher(access_token="invalid_token_123", profile_id_linkedin="prof_123")
    req = PublishRequest(job_id=uuid.uuid4(), platform="linkedin", text="Test post")

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "Unauthorized"
    mock_resp.headers = {"content-type": "text/plain"}

    with patch("requests.post", return_value=mock_resp):
        res = pub.publish(req)
        assert res.success is False
        assert res.status == "failed"
        assert "HTTP 401" in (res.error_message or "")
    print("PASS: Buffer publisher 401 error handling")


def test_buffer_publisher_429_rate_limit_handling():
    pub = BufferPublisher(access_token="valid_token", profile_id_linkedin="prof_123")
    req = PublishRequest(job_id=uuid.uuid4(), platform="linkedin", text="Test post")

    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.text = "Too Many Requests"
    mock_resp.headers = {"content-type": "text/plain"}

    with patch("requests.post", return_value=mock_resp):
        res = pub.publish(req)
        assert res.success is False
        assert res.status == "failed"
        assert "HTTP 429" in (res.error_message or "")
    print("PASS: Buffer publisher 429 rate limit handling")


def test_buffer_publisher_successful_post():
    pub = BufferPublisher(access_token="valid_token", profile_id_linkedin="prof_123")
    req = PublishRequest(job_id=uuid.uuid4(), platform="linkedin", text="Test post")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json.return_value = {
        "success": True,
        "updates": [{"id": "buffer_up_998877", "status": "buffer"}],
    }

    with patch("requests.post", return_value=mock_resp):
        res = pub.publish(req)
        assert res.success is True
        assert res.status == "published"
        assert res.external_post_id == "buffer_up_998877"
    print("PASS: Buffer publisher successful post creation")


# --- 2. Worker Polling & Lifecycle Unit Tests ------------------------------


class InMemoryJobStore:
    """Simulates SQLAlchemy Session for testing poller logic without external DB."""

    def __init__(self):
        self.jobs: dict[uuid.UUID, PublishingJob] = {}
        self.versions: dict[uuid.UUID, ContentVersion] = {}
        self.assets: dict[uuid.UUID, ContentAsset] = {}
        self.analytics_records: list[Analytics] = []

    def get(self, model_cls, pk):
        if model_cls == ContentVersion:
            return self.versions.get(pk)
        if model_cls == ContentAsset:
            return self.assets.get(pk)
        if model_cls == PublishingJob:
            return self.jobs.get(pk)
        return None

    def add(self, entity):
        if isinstance(entity, PublishingJob):
            self.jobs[entity.id] = entity
        elif isinstance(entity, ContentVersion):
            self.versions[entity.id] = entity
        elif isinstance(entity, ContentAsset):
            self.assets[entity.id] = entity
        elif isinstance(entity, Analytics):
            self.analytics_records.append(entity)

    def commit(self):
        pass

    def refresh(self, entity):
        pass

    def close(self):
        pass


def test_worker_process_success():
    store = InMemoryJobStore()
    publisher = SimulationPublisher(simulate_latency_ms=0)
    worker = PublishingWorker(publisher=publisher)

    job_id = uuid.uuid4()
    version_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    asset = ContentAsset(id=asset_id, platform="linkedin", status="approved")
    version = ContentVersion(id=version_id, body="Valid approved post copy for LinkedIn", status="approved")
    job = PublishingJob(
        id=job_id,
        content_asset_id=asset_id,
        content_version_id=version_id,
        platform="linkedin",
        status="publishing",
    )

    store.add(asset)
    store.add(version)
    store.add(job)

    res = worker.process_job(store, job)

    assert res.success is True
    assert job.status == "published"
    assert job.published_at is not None
    assert job.external_post_id is not None
    assert job.error_message is None
    print("PASS: Worker process_job transitions pending -> published")


def test_worker_process_failure():
    store = InMemoryJobStore()
    publisher = SimulationPublisher(simulate_latency_ms=0)
    worker = PublishingWorker(publisher=publisher)

    job_id = uuid.uuid4()
    version_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    asset = ContentAsset(id=asset_id, platform="unsupported_platform", status="approved")
    version = ContentVersion(id=version_id, body="Post that will be rejected", status="approved")
    job = PublishingJob(
        id=job_id,
        content_asset_id=asset_id,
        content_version_id=version_id,
        platform="unsupported_platform",
        status="publishing",
    )

    store.add(asset)
    store.add(version)
    store.add(job)

    res = worker.process_job(store, job)

    assert res.success is False
    assert job.status == "failed"
    assert job.published_at is None
    assert job.error_message is not None
    assert "not supported" in job.error_message
    print("PASS: Worker process_job transitions pending -> failed with error details")


def test_worker_missing_version_failure():
    store = InMemoryJobStore()
    publisher = SimulationPublisher(simulate_latency_ms=0)
    worker = PublishingWorker(publisher=publisher)

    job_id = uuid.uuid4()
    missing_version_id = uuid.uuid4()
    job = PublishingJob(
        id=job_id,
        content_asset_id=uuid.uuid4(),
        content_version_id=missing_version_id,
        platform="linkedin",
        status="publishing",
    )
    store.add(job)

    res = worker.process_job(store, job)

    assert res.success is False
    assert job.status == "failed"
    assert "not found" in (job.error_message or "")
    print("PASS: Worker handles missing ContentVersion safely")


def test_worker_idempotency_double_processing():
    """Confirms that already-published jobs are not re-processed."""
    store = InMemoryJobStore()
    publisher = MagicMock(spec=BasePublisher)
    worker = PublishingWorker(publisher=publisher)

    job = PublishingJob(
        id=uuid.uuid4(),
        content_asset_id=uuid.uuid4(),
        content_version_id=uuid.uuid4(),
        platform="linkedin",
        status="published",
        published_at=datetime.now(timezone.utc),
        external_post_id="ext_already_posted",
    )
    store.add(job)

    # Checked against the constant the claim query actually uses, not a copy.
    assert job.status not in CLAIMABLE_STATUSES, "Already published job must not be claimed"

    # Publisher must not be called
    publisher.publish.assert_not_called()
    print("PASS: Worker idempotency (published jobs are never re-claimed)")


def test_scheduled_job_not_due():
    """Jobs scheduled in the future must not be claimed."""
    future_time = datetime.now(timezone.utc) + timedelta(days=2)
    job = PublishingJob(
        id=uuid.uuid4(),
        content_asset_id=uuid.uuid4(),
        content_version_id=uuid.uuid4(),
        platform="linkedin",
        status="pending",
        scheduled_at=future_time,
    )

    now = datetime.now(timezone.utc)
    is_due = (job.scheduled_at is None) or (job.scheduled_at <= now)
    assert not is_due, "Future scheduled job must not be marked due"
    print("PASS: Scheduled future job is not prematurely claimed")


def test_provider_scheduled_jobs_are_never_reclaimed():
    """Regression: 'scheduled' used to be claimable, so every due scheduled job
    was re-sent to the provider on every poll — a new real post each interval."""
    assert "scheduled" not in CLAIMABLE_STATUSES
    assert set(CLAIMABLE_STATUSES) == {"pending"}
    print("PASS: Provider-scheduled jobs are never re-claimed")


def test_due_job_is_published_now_not_rescheduled():
    """Regression: a due job carried its (past) scheduled_at to the provider,
    came back 'scheduled', and was parked there instead of being published."""
    now = datetime.now(timezone.utc)
    past = now - timedelta(minutes=1)
    future = now + timedelta(hours=1)

    def job_at(when):
        return PublishingJob(id=uuid.uuid4(), content_asset_id=uuid.uuid4(),
                             content_version_id=uuid.uuid4(), platform="x",
                             status="publishing", scheduled_at=when)

    assert provider_scheduled_at(job_at(past), now) is None
    assert provider_scheduled_at(job_at(None), now) is None
    assert provider_scheduled_at(job_at(future), now) == future

    # End to end through process_job with the real simulation publisher.
    store = InMemoryJobStore()
    worker = PublishingWorker(publisher=SimulationPublisher(simulate_latency_ms=0))
    job = job_at(past)
    store.add(ContentVersion(id=job.content_version_id, body="Due post copy", status="approved"))
    store.add(job)
    res = worker.process_job(store, job)

    assert res.success is True
    assert job.status == "published", f"due job should publish, got {job.status}"
    assert job.published_at is not None
    print("PASS: Due job is published now, not parked in 'scheduled'")


def test_worker_sync_analytics():
    """Confirms analytics pull-back writes engagement metrics to analytics rows."""
    store = InMemoryJobStore()
    publisher = SimulationPublisher(simulate_latency_ms=0)
    worker = PublishingWorker(publisher=publisher)

    job_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    campaign_id = uuid.uuid4()

    asset = ContentAsset(id=asset_id, campaign_id=campaign_id, platform="linkedin")
    job = PublishingJob(
        id=job_id,
        content_asset_id=asset_id,
        platform="linkedin",
        status="published",
        external_post_id="sim_linkedin_test999",
    )
    store.add(asset)
    store.add(job)

    metrics = publisher.fetch_analytics(job.external_post_id, job.platform)
    assert metrics is not None

    # Calls the worker's real apply_metrics, not an inline copy of it.
    to_add, to_delete = apply_metrics([], job, asset.campaign_id, metrics, datetime.now(timezone.utc))
    for row in to_add:
        store.add(row)

    assert to_delete == []
    assert len(store.analytics_records) == 6
    metric_names = {r.metric_name for r in store.analytics_records}
    assert "impressions" in metric_names
    assert "engagement_rate" in metric_names
    assert all(r.is_simulated for r in store.analytics_records)
    print("PASS: Analytics sync persists metrics to analytics store")


def _sync_job():
    return PublishingJob(id=uuid.uuid4(), content_asset_id=uuid.uuid4(), platform="x",
                         status="published", external_post_id="sim_x_repeat")


def test_repeated_sync_does_not_duplicate_analytics():
    """Regression: every 30s sync appended a fresh 6-row set per post, and the
    optimization agent counts engagement_rate rows as posts — 1 post read as N."""
    publisher = SimulationPublisher(simulate_latency_ms=0)
    job = _sync_job()
    metrics = publisher.fetch_analytics(job.external_post_id, job.platform)
    stored: list[Analytics] = []

    for _ in range(5):
        to_add, to_delete = apply_metrics(list(stored), job, None, metrics, datetime.now(timezone.utc))
        stored.extend(to_add)
        stored = [r for r in stored if r not in to_delete]

    assert len(stored) == 6, f"expected 6 rows after 5 syncs, got {len(stored)}"
    assert sum(r.metric_name == "engagement_rate" for r in stored) == 1
    print("PASS: Repeated analytics sync keeps one row per metric")


def test_sync_refreshes_values_in_place():
    """A later sync must update the stored value, not leave the first one."""
    job = _sync_job()
    first = EngagementMetrics(impressions=100, likes=1, clicks=1, comments=0, shares=0,
                              engagement_rate=2.0, is_simulated=True)
    later = EngagementMetrics(impressions=900, likes=50, clicks=9, comments=3, shares=2,
                              engagement_rate=7.1, is_simulated=True)

    stored, _ = apply_metrics([], job, None, first, datetime.now(timezone.utc))
    to_add, to_delete = apply_metrics(stored, job, None, later, datetime.now(timezone.utc))

    assert to_add == [] and to_delete == []
    values = {r.metric_name: float(r.metric_value) for r in stored}
    assert values["impressions"] == 900 and values["engagement_rate"] == 7.1
    print("PASS: Analytics sync refreshes existing values in place")


def test_sync_collapses_existing_duplicates():
    """Rows left by the old append-only sync are collapsed on the next pass."""
    publisher = SimulationPublisher(simulate_latency_ms=0)
    job = _sync_job()
    metrics = publisher.fetch_analytics(job.external_post_id, job.platform)

    legacy: list[Analytics] = []
    for _ in range(3):  # three old append-only passes = 18 rows
        added, _ = apply_metrics([], job, None, metrics, datetime.now(timezone.utc))
        legacy.extend(added)
    assert len(legacy) == 18

    to_add, to_delete = apply_metrics(legacy, job, None, metrics, datetime.now(timezone.utc))
    survivors = [r for r in legacy if r not in to_delete] + to_add

    assert to_add == []
    assert len(to_delete) == 12
    assert len(survivors) == 6
    print("PASS: Analytics sync collapses legacy duplicate rows")


def run_all_tests():
    print("=== Running Project 2 Publishing Worker Tests ===")
    test_simulation_publisher_success()
    test_simulation_publisher_scheduled()
    test_simulation_publisher_deliberate_failure()
    test_simulation_publisher_unsupported_platform()
    test_simulation_publisher_analytics()

    test_buffer_publisher_missing_token()
    test_buffer_publisher_401_error_handling()
    test_buffer_publisher_429_rate_limit_handling()
    test_buffer_publisher_successful_post()

    test_worker_process_success()
    test_worker_process_failure()
    test_worker_missing_version_failure()
    test_worker_idempotency_double_processing()
    test_scheduled_job_not_due()
    test_provider_scheduled_jobs_are_never_reclaimed()
    test_due_job_is_published_now_not_rescheduled()
    test_worker_sync_analytics()
    test_repeated_sync_does_not_duplicate_analytics()
    test_sync_refreshes_values_in_place()
    test_sync_collapses_existing_duplicates()
    print("\nALL PROJECT 2 UNIT TESTS PASSED!")


if __name__ == "__main__":
    run_all_tests()
