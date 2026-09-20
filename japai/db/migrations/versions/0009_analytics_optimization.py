"""optimization agent: brand-level insights, supporting evidence, simulated origin

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-14

All changes are additive/nullable. `analytics` and `performance_insights` have
never been written to, so there is no backfill and no data-loss risk.

`analytics` itself needs no changes: its long/EAV shape (metric_name +
metric_value) already carries impressions / engagement_rate / clicks as separate
rows, and `is_simulated` already exists with NOT NULL DEFAULT true.

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Insights are brand-level patterns ("educational outperforms promotional").
    # The table could previously only hang off a campaign or a single asset, so
    # a brand-wide finding had nowhere to live and GET ?brand_id= could not filter.
    op.add_column(
        "performance_insights",
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "performance_insights_brand_id_fkey",
        "performance_insights",
        "brands",
        ["brand_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # The evidence behind the insight, kept as distinct fields rather than prose
    # so the UI can show them separately and a reader can check the claim.
    op.add_column("performance_insights", sa.Column("supporting_metric", sa.Text(), nullable=True))
    op.add_column("performance_insights", sa.Column("recommendation", sa.Text(), nullable=True))
    # Which aggregation/rows produced this — provenance, so an insight is
    # auditable rather than an unfalsifiable model assertion.
    op.add_column(
        "performance_insights", sa.Column("derived_from", postgresql.JSONB(), nullable=True)
    )

    # Simulated demo posts must not count as real agent output. The exclusion
    # sites (metrics/review/lessons) whitelist origin='agent', so a distinct
    # value keeps fabricated analytics posts out of every real metric by default.
    op.drop_constraint("ck_content_assets_origin", "content_assets", type_="check")
    op.create_check_constraint(
        "ck_content_assets_origin",
        "content_assets",
        "origin IN ('agent','test_fixture','manual','simulated')",
    )


def downgrade() -> None:
    op.execute("DELETE FROM content_assets WHERE origin = 'simulated'")
    op.drop_constraint("ck_content_assets_origin", "content_assets", type_="check")
    op.create_check_constraint(
        "ck_content_assets_origin",
        "content_assets",
        "origin IN ('agent','test_fixture','manual')",
    )

    op.drop_column("performance_insights", "derived_from")
    op.drop_column("performance_insights", "recommendation")
    op.drop_column("performance_insights", "supporting_metric")
    op.drop_constraint(
        "performance_insights_brand_id_fkey", "performance_insights", type_="foreignkey"
    )
    op.drop_column("performance_insights", "brand_id")
