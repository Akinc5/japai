import hashlib
import random
import time
from typing import Any
import uuid

from worker.publishers.base import BasePublisher, EngagementMetrics, PublishRequest, PublishResult

SUPPORTED_PLATFORMS = {"linkedin", "x", "twitter", "instagram", "facebook", "email"}


class SimulationPublisher(BasePublisher):
    """Realistic simulation publisher for local tests, demos, and failure verification.

    Features:
    - Generates realistic platform post IDs.
    - Validates platform compatibility and fails visibly on unsupported platforms.
    - Detects deliberate failure triggers (e.g. text containing '[SIMULATE_FAIL]' or platform 'unsupported').
    - Produces realistic engagement metrics for analytics pull-back.
    """

    def __init__(self, simulate_latency_ms: int = 50):
        self.simulate_latency_ms = simulate_latency_ms

    def publish(self, request: PublishRequest) -> PublishResult:
        if self.simulate_latency_ms > 0:
            time.sleep(self.simulate_latency_ms / 1000.0)

        platform = request.platform.lower().strip()

        # 1. Deliberate failure triggers for testing
        if "[SIMULATE_FAIL]" in request.text or request.metadata.get("trigger_failure"):
            return PublishResult(
                success=False,
                status="failed",
                error_message="Simulated provider error: Target channel rejected the post due to simulated policy restriction.",
                raw_response={"simulated": True, "error_code": "SIM_REJECTED"},
            )

        # 2. Platform validation
        if platform not in SUPPORTED_PLATFORMS:
            return PublishResult(
                success=False,
                status="failed",
                error_message=f"Platform '{platform}' is not supported by the publisher. Supported: {sorted(SUPPORTED_PLATFORMS)}",
                raw_response={"simulated": True, "error_code": "UNSUPPORTED_PLATFORM"},
            )

        # 3. Content validation
        if not request.text.strip():
            return PublishResult(
                success=False,
                status="failed",
                error_message="Cannot publish empty content text.",
                raw_response={"simulated": True, "error_code": "EMPTY_CONTENT"},
            )

        # 4. Generate deterministic mock post ID
        content_hash = hashlib.sha256(f"{request.job_id}:{request.text}".encode()).hexdigest()[:16]
        post_id = f"sim_{platform}_{content_hash}"

        is_scheduled = request.scheduled_at is not None
        status = "scheduled" if is_scheduled else "published"

        return PublishResult(
            success=True,
            status=status,
            external_post_id=post_id,
            raw_response={
                "simulated": True,
                "platform": platform,
                "post_id": post_id,
                "text_length": len(request.text),
                "scheduled": is_scheduled,
            },
        )

    def fetch_analytics(self, external_post_id: str, platform: str) -> EngagementMetrics | None:
        # Generate stable, realistic pseudo-random metrics based on post_id
        seed = int(hashlib.md5(external_post_id.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        impressions = rng.randint(250, 4500)
        likes = rng.randint(5, int(impressions * 0.08))
        comments = rng.randint(0, int(likes * 0.3))
        shares = rng.randint(0, int(likes * 0.2))
        clicks = rng.randint(2, int(impressions * 0.05))

        total_engagements = likes + comments + shares + clicks
        rate = round((total_engagements / max(impressions, 1)) * 100, 2)

        return EngagementMetrics(
            impressions=impressions,
            likes=likes,
            clicks=clicks,
            comments=comments,
            shares=shares,
            engagement_rate=rate,
            is_simulated=True,
            raw_data={"simulated_seed": seed, "platform": platform},
        )

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "connected",
            "provider": "simulation",
            "supported_platforms": sorted(SUPPORTED_PLATFORMS),
        }
