import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, UUIDPKMixin, TimestampMixin


class Campaign(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "campaigns"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','active','paused','completed','archived')",
            name="ck_campaigns_status",
        ),
    )

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_opportunities.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    objective: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="draft")
    target_audience: Mapped[str | None] = mapped_column(Text)
    key_message: Mapped[str | None] = mapped_column(Text)
    cta: Mapped[str | None] = mapped_column(Text)
    budget: Mapped[float | None] = mapped_column(Numeric)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)

    brand = relationship("Brand")
    opportunity = relationship("ContentOpportunity")
