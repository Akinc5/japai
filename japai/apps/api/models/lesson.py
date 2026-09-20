import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, UUIDPKMixin, TimestampMixin


class Lesson(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "lessons"
    __table_args__ = (
        UniqueConstraint("brand_id", "reason_tag", name="uq_lessons_brand_reason_tag"),
    )

    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE")
    )
    source_feedback_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("feedback.id", ondelete="SET NULL")
    )
    title: Mapped[str | None] = mapped_column(Text)
    lesson_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(Text)
    reason_tag: Mapped[str | None] = mapped_column(Text)
    frequency_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    confidence_score: Mapped[float | None] = mapped_column(Numeric)

    brand = relationship("Brand")
    source_feedback = relationship("Feedback")
