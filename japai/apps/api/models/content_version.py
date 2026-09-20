import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, UUIDPKMixin, TimestampMixin


class ContentVersion(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "content_versions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','submitted_for_review','approved','rejected')",
            name="ck_content_versions_status",
        ),
        UniqueConstraint("content_asset_id", "version_number", name="uq_content_versions_asset_version"),
    )

    content_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_assets.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    version_metadata: Mapped[dict | None] = mapped_column(JSONB, name="metadata")
    generated_by_agent: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="draft")
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    content_asset = relationship("ContentAsset", back_populates="versions")
