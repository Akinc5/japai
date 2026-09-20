from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, UUIDPKMixin, TimestampMixin


class Organization(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(Text, nullable=False)

    brands = relationship("Brand", back_populates="organization", cascade="all, delete-orphan")
