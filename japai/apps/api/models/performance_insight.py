import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, UUIDPKMixin, TimestampMixin


class PerformanceInsight(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "performance_insights"

    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE")
    )
    content_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_assets.id", ondelete="CASCADE")
    )
    # Insights are brand-level patterns, so they hang off the brand rather than
    # a single asset or campaign (both of which stay available for narrower ones).
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE")
    )
    insight_text: Mapped[str] = mapped_column(Text, nullable=False)
    insight_type: Mapped[str | None] = mapped_column(Text)
    generated_by_agent: Mapped[str | None] = mapped_column(Text)
    # The evidence, kept separate from the prose so the UI can show it and a
    # reader can check the claim against the numbers.
    supporting_metric: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)
    # Provenance: the aggregation rows this was computed from, so an insight is
    # auditable rather than an unfalsifiable model assertion.
    derived_from: Mapped[dict | None] = mapped_column(JSONB)

    campaign = relationship("Campaign")
    content_asset = relationship("ContentAsset")
    brand = relationship("Brand")
