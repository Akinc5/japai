"""localization: language on content assets + link back to the source asset

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-13

Language lives on `content_assets`, not `content_versions`, deliberately:

  - Language is a property of the variant, not the revision. When a reviewer
    edits the Chinese asset, version 2 is still Chinese; storing language per
    version would allow a nonsensical v1=zh / v2=en chain.
  - content_versions already has UNIQUE (content_asset_id, version_number) and
    a single is_current per asset. Treating each language as a version would
    make the four languages compete for one version counter and one current
    flag, and there would be no way for each language to hold its own
    approve/edit/reject state.
  - It reuses the Phase 5 multi-format pattern exactly: one campaign, N assets,
    each a variant distinguished by a column on content_assets (platform /
    asset_type, and now language).

Existing rows are English, so the backfill is a DEFAULT rather than a guess.

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# BCP-47-ish codes. 'ms' (Malay) and 'id' (Indonesian) are deliberately separate
# entries: they are closely related but distinct languages, and conflating them
# would be a real localization error rather than a shortcut.
LANGUAGES = ("en", "zh-Hans", "ms", "id")


def upgrade() -> None:
    op.add_column(
        "content_assets",
        sa.Column("language", sa.Text(), nullable=False, server_default="en"),
    )
    op.create_check_constraint(
        "ck_content_assets_language",
        "content_assets",
        "language IN ('en','zh-Hans','ms','id')",
    )
    op.create_index("ix_content_assets_language", "content_assets", ["language"])

    # Self-referencing link: a localized asset points at the English asset it was
    # adapted from. This is what groups "the same underlying idea, N languages"
    # without collapsing them into one row.
    op.add_column(
        "content_assets",
        sa.Column("source_content_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "content_assets_source_content_asset_id_fkey",
        "content_assets",
        "content_assets",
        ["source_content_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "content_assets_source_content_asset_id_fkey", "content_assets", type_="foreignkey"
    )
    op.drop_column("content_assets", "source_content_asset_id")
    op.drop_index("ix_content_assets_language", table_name="content_assets")
    op.drop_constraint("ck_content_assets_language", "content_assets", type_="check")
    op.drop_column("content_assets", "language")
