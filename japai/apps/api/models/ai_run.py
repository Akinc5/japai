import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.models.base import Base, UUIDPKMixin, TimestampMixin


class AiRun(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "ai_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','running','succeeded','failed')",
            name="ck_ai_runs_status",
        ),
        Index("ix_ai_runs_agent_name", "agent_name"),
    )

    agent_name: Mapped[str] = mapped_column(Text, nullable=False)
    run_type: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="pending")
    input_summary: Mapped[str | None] = mapped_column(Text)
    output_summary: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    related_entity_type: Mapped[str | None] = mapped_column(Text)
    related_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
