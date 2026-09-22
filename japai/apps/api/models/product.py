import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, GUID, UUIDPKMixin, TimestampMixin


class Product(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "products"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(Text)

    brand = relationship("Brand", back_populates="products")

