from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid


@dataclass
class PublishRequest:
    job_id: uuid.UUID
    platform: str
    text: str
    scheduled_at: datetime | None = None
    media_urls: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PublishResult:
    success: bool
    status: str  # "published", "scheduled", "failed"
    external_post_id: str | None = None
    error_message: str | None = None
    raw_response: dict[str, Any] | None = None


@dataclass
class EngagementMetrics:
    impressions: int = 0
    likes: int = 0
    clicks: int = 0
    comments: int = 0
    shares: int = 0
    engagement_rate: float = 0.0
    is_simulated: bool = False
    raw_data: dict[str, Any] = field(default_factory=dict)


class BasePublisher(ABC):
    @abstractmethod
    def publish(self, request: PublishRequest) -> PublishResult:
        """Publishes or schedules content to the target social platform.
        Must return a PublishResult and never raise unhandled exceptions."""
        pass

    @abstractmethod
    def fetch_analytics(self, external_post_id: str, platform: str) -> EngagementMetrics | None:
        """Fetches post engagement metrics from the provider if available."""
        pass

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Verifies provider connectivity and credentials."""
        pass
