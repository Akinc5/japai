import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, GUID, UUIDPKMixin, TimestampMixin


class Analytics(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "analytics"

    content_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("content_assets.id", ondelete="CASCADE")
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("campaigns.id", ondelete="CASCADE")
    )
    metric_name: Mapped[str] = mapped_column(Text, nullable=False)
    metric_value: Mapped[float] = mapped_column(Numeric, nullable=False)
    platform: Mapped[str | None] = mapped_column(Text)
    is_simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    content_asset = relationship("ContentAsset")
    campaign = relationship("Campaign")

