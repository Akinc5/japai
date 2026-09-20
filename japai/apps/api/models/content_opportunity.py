import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, UUIDPKMixin, TimestampMixin


class ContentOpportunity(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "content_opportunities"
    __table_args__ = (
        CheckConstraint(
            "status IN ('suggested','new','under_review','approved','rejected',"
            "'converted_to_campaign')",
            name="ck_content_opportunities_status",
        ),
    )

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    opportunity_type: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)
    priority_score: Mapped[float | None] = mapped_column(Numeric)
    score_breakdown: Mapped[dict | None] = mapped_column(JSONB)
    suggested_angle: Mapped[str | None] = mapped_column(Text)
    suggested_formats: Mapped[list | None] = mapped_column(JSONB)
    source_chunk_ids: Mapped[list | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="new")

    brand = relationship("Brand")
