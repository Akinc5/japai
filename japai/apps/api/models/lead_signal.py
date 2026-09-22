import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, GUID, UUIDPKMixin, TimestampMixin


class LeadSignal(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "lead_signals"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False
    )
    signal_type: Mapped[str] = mapped_column(Text, nullable=False)
    signal_value: Mapped[str | None] = mapped_column(Text)
    weight: Mapped[float | None] = mapped_column(Numeric)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    lead = relationship("Lead", back_populates="signals")

