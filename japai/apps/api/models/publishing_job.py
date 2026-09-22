import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, GUID, UUIDPKMixin, TimestampMixin


class PublishingJob(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "publishing_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','scheduled','publishing','published','failed','cancelled')",
            name="ck_publishing_jobs_status",
        ),
    )

    content_asset_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("content_assets.id", ondelete="CASCADE"), nullable=False
    )
    content_version_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("content_versions.id", ondelete="CASCADE"), nullable=False
    )
    platform: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="pending")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    external_post_id: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)

    content_asset = relationship("ContentAsset")
    content_version = relationship("ContentVersion")

