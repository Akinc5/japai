import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, GUID, UUIDPKMixin, TimestampMixin


class ComplianceRule(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "compliance_rules"
    __table_args__ = (
        CheckConstraint(
            "category IN ('regulatory','claims','disclosure','brand_safety','other')",
            name="ck_compliance_rules_category",
        ),
        CheckConstraint(
            "severity IN ('low','medium','high','critical')",
            name="ck_compliance_rules_severity",
        ),
    )

    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("brands.id", ondelete="CASCADE")
    )
    rule_code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False, server_default="medium")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    brand = relationship("Brand")

