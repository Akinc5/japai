"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-11

"""
from typing import Sequence, Union

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _pk():
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )


def _timestamps():
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "organizations",
        _pk(),
        sa.Column("name", sa.Text(), nullable=False),
        *_timestamps(),
    )

    op.create_table(
        "brands",
        _pk(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("voice_description", sa.Text(), nullable=True),
        sa.Column("tone_guidelines", sa.Text(), nullable=True),
        sa.Column("target_audience", sa.Text(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("slug", name="uq_brands_slug"),
    )

    op.create_table(
        "products",
        _pk(),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.Text(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "knowledge_chunks",
        _pk(),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(768), nullable=True),
        sa.Column("source", sa.Text(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "category IN ('faq','approved_claim','restricted_claim','brand_guideline')",
            name="ck_knowledge_chunks_category",
        ),
    )
    op.create_index("ix_knowledge_chunks_brand_id", "knowledge_chunks", ["brand_id"])
    op.create_index("ix_knowledge_chunks_category", "knowledge_chunks", ["category"])

    op.create_table(
        "content_opportunities",
        _pk(),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("opportunity_type", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("priority_score", sa.Numeric(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="new"),
        *_timestamps(),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "status IN ('new','under_review','approved','rejected','converted_to_campaign')",
            name="ck_content_opportunities_status",
        ),
    )

    op.create_table(
        "campaigns",
        _pk(),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="draft"),
        sa.Column("target_audience", sa.Text(), nullable=True),
        sa.Column("budget", sa.Numeric(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["opportunity_id"], ["content_opportunities.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "status IN ('draft','active','paused','completed','archived')",
            name="ck_campaigns_status",
        ),
    )

    op.create_table(
        "content_assets",
        _pk(),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_type", sa.Text(), nullable=False),
        sa.Column("platform", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="draft"),
        sa.Column("created_by", sa.Text(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "asset_type IN ('social_post','email','blog_article','ad_copy','landing_page','other')",
            name="ck_content_assets_asset_type",
        ),
        sa.CheckConstraint(
            "status IN ('draft','in_review','approved','rejected','published','archived')",
            name="ck_content_assets_status",
        ),
    )

    op.create_table(
        "content_versions",
        _pk(),
        sa.Column("content_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("generated_by_agent", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="draft"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="false"),
        *_timestamps(),
        sa.ForeignKeyConstraint(["content_asset_id"], ["content_assets.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("content_asset_id", "version_number", name="uq_content_versions_asset_version"),
        sa.CheckConstraint(
            "status IN ('draft','submitted_for_review','approved','rejected')",
            name="ck_content_versions_status",
        ),
    )

    op.create_table(
        "compliance_rules",
        _pk(),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rule_code", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False, server_default="medium"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        *_timestamps(),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("rule_code", name="uq_compliance_rules_rule_code"),
        sa.CheckConstraint(
            "category IN ('regulatory','claims','disclosure','brand_safety','other')",
            name="ck_compliance_rules_category",
        ),
        sa.CheckConstraint(
            "severity IN ('low','medium','high','critical')",
            name="ck_compliance_rules_severity",
        ),
    )

    op.create_table(
        "compliance_reviews",
        _pk(),
        sa.Column("content_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("compliance_rule_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewer_type", sa.Text(), nullable=False, server_default="ai_agent"),
        sa.Column("reviewer_name", sa.Text(), nullable=True),
        sa.Column("outcome", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        *_timestamps(),
        sa.ForeignKeyConstraint(["content_version_id"], ["content_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["compliance_rule_id"], ["compliance_rules.id"], ondelete="SET NULL"),
        sa.CheckConstraint("reviewer_type IN ('ai_agent','human')", name="ck_compliance_reviews_reviewer_type"),
        sa.CheckConstraint(
            "outcome IN ('pass','fail','warning','needs_human_review')",
            name="ck_compliance_reviews_outcome",
        ),
    )

    op.create_table(
        "feedback",
        _pk(),
        sa.Column("content_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("feedback_text", sa.Text(), nullable=False),
        sa.Column("sentiment", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Text(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["content_asset_id"], ["content_assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "source IN ('human_review','compliance','performance','lead')",
            name="ck_feedback_source",
        ),
        sa.CheckConstraint("sentiment IN ('positive','negative','neutral')", name="ck_feedback_sentiment"),
    )

    op.create_table(
        "lessons",
        _pk(),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_feedback_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("lesson_text", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Numeric(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_feedback_id"], ["feedback.id"], ondelete="SET NULL"),
    )

    op.create_table(
        "leads",
        _pk(),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_name", sa.Text(), nullable=True),
        sa.Column("contact_name", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="new"),
        sa.Column("score", sa.Numeric(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "status IN ('new','contacted','qualified','unqualified','converted','lost')",
            name="ck_leads_status",
        ),
    )
    op.create_index("ix_leads_email", "leads", ["email"])

    op.create_table(
        "lead_signals",
        _pk(),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("signal_type", sa.Text(), nullable=False),
        sa.Column("signal_value", sa.Text(), nullable=True),
        sa.Column("weight", sa.Numeric(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        *_timestamps(),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "lead_activities",
        _pk(),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("activity_type", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("performed_by", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        *_timestamps(),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "activity_type IN ('email_sent','call','meeting','note','status_change')",
            name="ck_lead_activities_activity_type",
        ),
    )

    op.create_table(
        "publishing_jobs",
        _pk(),
        sa.Column("content_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_post_id", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["content_asset_id"], ["content_assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["content_version_id"], ["content_versions.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "status IN ('pending','scheduled','publishing','published','failed','cancelled')",
            name="ck_publishing_jobs_status",
        ),
    )

    op.create_table(
        "analytics",
        _pk(),
        sa.Column("content_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metric_name", sa.Text(), nullable=False),
        sa.Column("metric_value", sa.Numeric(), nullable=False),
        sa.Column("platform", sa.Text(), nullable=True),
        sa.Column("is_simulated", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        *_timestamps(),
        sa.ForeignKeyConstraint(["content_asset_id"], ["content_assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "performance_insights",
        _pk(),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("content_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("insight_text", sa.Text(), nullable=False),
        sa.Column("insight_type", sa.Text(), nullable=True),
        sa.Column("generated_by_agent", sa.Text(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["content_asset_id"], ["content_assets.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "ai_runs",
        _pk(),
        sa.Column("agent_name", sa.Text(), nullable=False),
        sa.Column("run_type", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("input_summary", sa.Text(), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("related_entity_type", sa.Text(), nullable=True),
        sa.Column("related_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.CheckConstraint("status IN ('pending','running','succeeded','failed')", name="ck_ai_runs_status"),
    )
    op.create_index("ix_ai_runs_agent_name", "ai_runs", ["agent_name"])


def downgrade() -> None:
    op.drop_table("ai_runs")
    op.drop_table("performance_insights")
    op.drop_table("analytics")
    op.drop_table("publishing_jobs")
    op.drop_table("lead_activities")
    op.drop_table("lead_signals")
    op.drop_table("leads")
    op.drop_table("lessons")
    op.drop_table("feedback")
    op.drop_table("compliance_reviews")
    op.drop_table("compliance_rules")
    op.drop_table("content_versions")
    op.drop_table("content_assets")
    op.drop_table("campaigns")
    op.drop_table("content_opportunities")
    op.drop_table("knowledge_chunks")
    op.drop_table("products")
    op.drop_table("brands")
    op.drop_table("organizations")
