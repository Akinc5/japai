"""research observations, opportunity scoring fields, campaign brief fields

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Research agent stores competitor/industry observations as knowledge chunks.
    op.drop_constraint("ck_knowledge_chunks_category", "knowledge_chunks", type_="check")
    op.create_check_constraint(
        "ck_knowledge_chunks_category",
        "knowledge_chunks",
        "category IN ('faq','approved_claim','restricted_claim','brand_guideline',"
        "'competitor_observation')",
    )

    # Opportunity agent: transparent scoring + provenance + suggested formats.
    op.drop_constraint("ck_content_opportunities_status", "content_opportunities", type_="check")
    op.create_check_constraint(
        "ck_content_opportunities_status",
        "content_opportunities",
        "status IN ('suggested','new','under_review','approved','rejected',"
        "'converted_to_campaign')",
    )
    op.add_column(
        "content_opportunities", sa.Column("score_breakdown", postgresql.JSONB(), nullable=True)
    )
    op.add_column("content_opportunities", sa.Column("suggested_angle", sa.Text(), nullable=True))
    op.add_column(
        "content_opportunities", sa.Column("suggested_formats", postgresql.JSONB(), nullable=True)
    )
    op.add_column(
        "content_opportunities", sa.Column("source_chunk_ids", postgresql.JSONB(), nullable=True)
    )

    # Campaign brief fields (strategy reuses the existing `objective` column).
    op.add_column("campaigns", sa.Column("key_message", sa.Text(), nullable=True))
    op.add_column("campaigns", sa.Column("cta", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("campaigns", "cta")
    op.drop_column("campaigns", "key_message")

    op.drop_column("content_opportunities", "source_chunk_ids")
    op.drop_column("content_opportunities", "suggested_formats")
    op.drop_column("content_opportunities", "suggested_angle")
    op.drop_column("content_opportunities", "score_breakdown")
    op.drop_constraint("ck_content_opportunities_status", "content_opportunities", type_="check")
    op.create_check_constraint(
        "ck_content_opportunities_status",
        "content_opportunities",
        "status IN ('new','under_review','approved','rejected','converted_to_campaign')",
    )

    op.drop_constraint("ck_knowledge_chunks_category", "knowledge_chunks", type_="check")
    op.create_check_constraint(
        "ck_knowledge_chunks_category",
        "knowledge_chunks",
        "category IN ('faq','approved_claim','restricted_claim','brand_guideline')",
    )
