"""feedback reason_tag + content_version linkage

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("feedback", sa.Column("reason_tag", sa.Text(), nullable=True))
    op.add_column(
        "feedback",
        sa.Column("content_version_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_feedback_content_version_id",
        "feedback",
        "content_versions",
        ["content_version_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_feedback_content_version_id", "feedback", type_="foreignkey")
    op.drop_column("feedback", "content_version_id")
    op.drop_column("feedback", "reason_tag")
