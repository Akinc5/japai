"""content agent + compliance run metadata

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "compliance_reviews",
        sa.Column(
            "detected_issues",
            postgresql.JSONB(),
            nullable=True,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.drop_constraint("ck_compliance_reviews_reviewer_type", "compliance_reviews", type_="check")
    op.create_check_constraint(
        "ck_compliance_reviews_reviewer_type",
        "compliance_reviews",
        "reviewer_type IN ('ai_agent','human','deterministic')",
    )

    op.add_column("ai_runs", sa.Column("model", sa.Text(), nullable=True))
    op.add_column("ai_runs", sa.Column("prompt_version", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("ai_runs", "prompt_version")
    op.drop_column("ai_runs", "model")

    op.drop_constraint("ck_compliance_reviews_reviewer_type", "compliance_reviews", type_="check")
    op.create_check_constraint(
        "ck_compliance_reviews_reviewer_type",
        "compliance_reviews",
        "reviewer_type IN ('ai_agent','human')",
    )
    op.drop_column("compliance_reviews", "detected_issues")
