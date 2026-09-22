import uuid

from sqlalchemy import ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, GUID, UUIDPKMixin, TimestampMixin


class PerformanceInsight(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "performance_insights"

    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("campaigns.id", ondelete="CASCADE")
    )
    content_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("content_assets.id", ondelete="CASCADE")
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("brands.id", ondelete="CASCADE")
    )
    insight_text: Mapped[str] = mapped_column(Text, nullable=False)
    insight_type: Mapped[str | None] = mapped_column(Text)
    generated_by_agent: Mapped[str | None] = mapped_column(Text)
    supporting_metric: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)
    derived_from: Mapped[dict | None] = mapped_column(JSON)

    campaign = relationship("Campaign")
    content_asset = relationship("ContentAsset")
    brand = relationship("Brand")

