"""allow 'llm' as a compliance_reviews.reviewer_type value

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-13

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("ck_compliance_reviews_reviewer_type", "compliance_reviews", type_="check")
    op.create_check_constraint(
        "ck_compliance_reviews_reviewer_type",
        "compliance_reviews",
        "reviewer_type IN ('ai_agent','human','deterministic','llm')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_compliance_reviews_reviewer_type", "compliance_reviews", type_="check")
    op.create_check_constraint(
        "ck_compliance_reviews_reviewer_type",
        "compliance_reviews",
        "reviewer_type IN ('ai_agent','human','deterministic')",
    )
