import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, GUID, UUIDPKMixin, TimestampMixin


class Feedback(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint(
            "source IN ('human_review','compliance','performance','lead')",
            name="ck_feedback_source",
        ),
        CheckConstraint(
            "sentiment IN ('positive','negative','neutral')",
            name="ck_feedback_sentiment",
        ),
    )

    content_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("content_assets.id", ondelete="CASCADE")
    )
    content_version_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("content_versions.id", ondelete="SET NULL")
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("campaigns.id", ondelete="CASCADE")
    )
    source: Mapped[str] = mapped_column(Text, nullable=False)
    feedback_text: Mapped[str] = mapped_column(Text, nullable=False)
    reason_tag: Mapped[str | None] = mapped_column(Text)
    sentiment: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(Text)

    content_asset = relationship("ContentAsset")
    content_version = relationship("ContentVersion")
    campaign = relationship("Campaign")

