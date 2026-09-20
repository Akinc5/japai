from worker.config import worker_settings
from worker.publishers.base import BasePublisher, EngagementMetrics, PublishRequest, PublishResult
from worker.publishers.buffer import BufferPublisher
from worker.publishers.simulation import SimulationPublisher


def get_publisher(provider: str | None = None) -> BasePublisher:
    """Returns the configured social publishing provider."""
    target = (provider or worker_settings.PUBLISHER_MODE).lower().strip()

    if target == "buffer":
        return BufferPublisher()
    elif target in ("simulation", "mock"):
        return SimulationPublisher()
    else:
        # Auto mode: use Buffer if access token is configured, otherwise fallback to Simulation
        if not worker_settings.is_simulation_mode:
            return BufferPublisher()
        return SimulationPublisher()


__all__ = [
    "BasePublisher",
    "BufferPublisher",
    "SimulationPublisher",
    "PublishRequest",
    "PublishResult",
    "EngagementMetrics",
    "get_publisher",
]
