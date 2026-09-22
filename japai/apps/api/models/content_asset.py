import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, GUID, UUIDPKMixin, TimestampMixin


class ContentAsset(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "content_assets"
    __table_args__ = (
        CheckConstraint(
            "asset_type IN ('social_post','email','blog_article','ad_copy','landing_page','other')",
            name="ck_content_assets_asset_type",
        ),
        CheckConstraint(
            "status IN ('draft','in_review','approved','rejected','published','archived')",
            name="ck_content_assets_status",
        ),
        CheckConstraint(
            "origin IN ('agent','test_fixture','manual','simulated')",
            name="ck_content_assets_origin",
        ),
        CheckConstraint(
            "language IN ('en','zh-Hans','ms','id')",
            name="ck_content_assets_language",
        ),
        Index("ix_content_assets_language", "language"),
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    asset_type: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="draft")
    created_by: Mapped[str | None] = mapped_column(Text)
    origin: Mapped[str] = mapped_column(Text, nullable=False, server_default="agent")
    # Language is a property of the variant, not the revision — all versions of
    # this asset are in this language. See migration 0010 for the reasoning.
    language: Mapped[str] = mapped_column(Text, nullable=False, server_default="en")
    # Points at the English asset this was localized from (NULL for originals).
    source_content_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("content_assets.id", ondelete="SET NULL")
    )

    campaign = relationship("Campaign")
    brand = relationship("Brand")
    versions = relationship("ContentVersion", back_populates="content_asset", cascade="all, delete-orphan")

