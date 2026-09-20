import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, UUIDPKMixin, TimestampMixin


class Brand(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "brands"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    voice_description: Mapped[str | None] = mapped_column(Text)
    tone_guidelines: Mapped[str | None] = mapped_column(Text)
    target_audience: Mapped[str | None] = mapped_column(Text)

    organization = relationship("Organization", back_populates="brands")
    products = relationship("Product", back_populates="brand", cascade="all, delete-orphan")
    knowledge_chunks = relationship("KnowledgeChunk", back_populates="brand", cascade="all, delete-orphan")
