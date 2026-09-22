import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, GUID, UUIDPKMixin, TimestampMixin


class ComplianceReview(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "compliance_reviews"
    __table_args__ = (
        CheckConstraint(
            "reviewer_type IN ('ai_agent','human','deterministic','llm')",
            name="ck_compliance_reviews_reviewer_type",
        ),
        CheckConstraint(
            "outcome IN ('pass','fail','warning','needs_human_review')",
            name="ck_compliance_reviews_outcome",
        ),
    )

    content_version_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("content_versions.id", ondelete="CASCADE"), nullable=False
    )
    compliance_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("compliance_rules.id", ondelete="SET NULL")
    )
    reviewer_type: Mapped[str] = mapped_column(Text, nullable=False, default="ai_agent")
    reviewer_name: Mapped[str | None] = mapped_column(Text)
    outcome: Mapped[str] = mapped_column(Text, nullable=False)
    detected_issues: Mapped[list | None] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    content_version = relationship("ContentVersion")
    compliance_rule = relationship("ComplianceRule")

