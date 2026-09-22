import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, UUIDPKMixin, TimestampMixin


class Lead(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "leads"
    __table_args__ = (
        CheckConstraint(
            "status IN ('new','contacted','qualified','unqualified','converted','lost')",
            name="ck_leads_status",
        ),
        Index("ix_leads_email", "email"),
    )

    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL")
    )
    company_name: Mapped[str | None] = mapped_column(Text)
    contact_name: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="new")
    score: Mapped[float | None] = mapped_column(Numeric)

    category: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    employee_count: Mapped[int | None] = mapped_column(Integer)
    score_breakdown: Mapped[dict | None] = mapped_column(JSON)
    outreach_content_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_versions.id", ondelete="SET NULL")
    )

    brand = relationship("Brand")
    outreach_version = relationship("ContentVersion")
    signals = relationship("LeadSignal", back_populates="lead", cascade="all, delete-orphan")
    activities = relationship("LeadActivity", back_populates="lead", cascade="all, delete-orphan")
