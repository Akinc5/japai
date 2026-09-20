"""lead agent: category, transparent fit scoring, outreach linkage

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-13

All changes are additive/nullable. The `leads` table has never been written to,
so there is no backfill and no data-loss risk.

`contact_info JSONB` is deliberately NOT added: the table already carries flat
contact_name / email / phone columns, which cover placeholder contact data.

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fit-scoring inputs. location/employee_count are real scoring signals, not
    # decoration — see lead.py's SCORE_FORMULA.
    op.add_column("leads", sa.Column("category", sa.Text(), nullable=True))
    op.add_column("leads", sa.Column("location", sa.Text(), nullable=True))
    op.add_column("leads", sa.Column("employee_count", sa.Integer(), nullable=True))

    # Mirrors content_opportunities.score_breakdown: every number that produced
    # the score is persisted so the result is explainable, not a black box.
    op.add_column("leads", sa.Column("score_breakdown", postgresql.JSONB(), nullable=True))

    # Outreach drafts are stored as content_versions so they reuse the existing
    # compliance + review machinery. This is the lead -> draft link.
    op.add_column(
        "leads",
        sa.Column("outreach_content_version_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "leads_outreach_content_version_id_fkey",
        "leads",
        "content_versions",
        ["outreach_content_version_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # The existing CHECK allows only email_sent/call/meeting/note/status_change.
    # 'outreach_drafted' records that a draft was generated but NOT sent.
    op.drop_constraint("ck_lead_activities_activity_type", "lead_activities", type_="check")
    op.create_check_constraint(
        "ck_lead_activities_activity_type",
        "lead_activities",
        "activity_type IN ('email_sent','call','meeting','note','status_change',"
        "'outreach_drafted')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_lead_activities_activity_type", "lead_activities", type_="check")
    op.create_check_constraint(
        "ck_lead_activities_activity_type",
        "lead_activities",
        "activity_type IN ('email_sent','call','meeting','note','status_change')",
    )

    op.drop_constraint("leads_outreach_content_version_id_fkey", "leads", type_="foreignkey")
    op.drop_column("leads", "outreach_content_version_id")
    op.drop_column("leads", "score_breakdown")
    op.drop_column("leads", "employee_count")
    op.drop_column("leads", "location")
    op.drop_column("leads", "category")
