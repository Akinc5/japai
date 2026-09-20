"""content_assets.origin, to keep test fixtures out of real metrics

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "content_assets",
        sa.Column("origin", sa.Text(), nullable=False, server_default="agent"),
    )
    op.create_check_constraint(
        "ck_content_assets_origin",
        "content_assets",
        "origin IN ('agent','test_fixture','manual')",
    )
    op.create_index("ix_content_assets_origin", "content_assets", ["origin"])

    # One-time backfill: every asset created before this column existed that has no
    # created_by was produced by the Phase 2/3 regression fixtures, never by an agent.
    op.execute(
        "UPDATE content_assets SET origin = 'test_fixture' WHERE created_by IS NULL"
    )


def downgrade() -> None:
    op.drop_index("ix_content_assets_origin", table_name="content_assets")
    op.drop_constraint("ck_content_assets_origin", "content_assets", type_="check")
    op.drop_column("content_assets", "origin")
