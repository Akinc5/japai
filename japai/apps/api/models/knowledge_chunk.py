import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import CheckConstraint, ForeignKey, Index, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, UUIDPKMixin, TimestampMixin


class KnowledgeChunk(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        CheckConstraint(
            "category IN ('faq','approved_claim','restricted_claim','brand_guideline',"
            "'competitor_observation')",
            name="ck_knowledge_chunks_category",
        ),
        Index("ix_knowledge_chunks_brand_id", "brand_id"),
        Index("ix_knowledge_chunks_category", "category"),
    )

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL")
    )
    category: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768).with_variant(JSON, "sqlite"))
    source: Mapped[str | None] = mapped_column(Text)

    brand = relationship("Brand", back_populates="knowledge_chunks")
