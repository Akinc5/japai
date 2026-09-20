"""lessons aggregation fields: reason_tag, frequency_count

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("lessons", sa.Column("reason_tag", sa.Text(), nullable=True))
    op.add_column(
        "lessons",
        sa.Column("frequency_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_unique_constraint(
        "uq_lessons_brand_reason_tag", "lessons", ["brand_id", "reason_tag"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_lessons_brand_reason_tag", "lessons", type_="unique")
    op.drop_column("lessons", "frequency_count")
    op.drop_column("lessons", "reason_tag")
