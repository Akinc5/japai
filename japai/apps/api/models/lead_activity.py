import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, GUID, UUIDPKMixin, TimestampMixin


class LeadActivity(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "lead_activities"
    __table_args__ = (
        CheckConstraint(
            "activity_type IN ('email_sent','call','meeting','note','status_change',"
            "'outreach_drafted')",
            name="ck_lead_activities_activity_type",
        ),
    )

    lead_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False
    )
    activity_type: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    performed_by: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    lead = relationship("Lead", back_populates="activities")

