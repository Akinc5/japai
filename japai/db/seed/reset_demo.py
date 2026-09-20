"""Reset to a known-good demo state.

Wipes all *generated* data (opportunities, campaigns, content, compliance reviews,
feedback, lessons, leads, research observations) and reseeds the durable
reference data (organization, brands, brand knowledge chunks, compliance rules).

`ai_runs` is deliberately NOT wiped. It is observability/audit data, not demo
content: nothing in the API or dashboard reads it, so an empty table buys the
demo nothing, while clearing it destroys the only record of cumulative LLM
spend (which it did, twice, during the Phase 5/6 builds). Use --wipe-ai-runs
if you explicitly want a clean slate; the current count is printed first so the
number is reported before it is lost.

Brands and their seeded knowledge/compliance rules are preserved by re-running the
existing seed scripts, so this is safe to run repeatedly before a demo.

Usage:
    docker compose exec api python -m db.seed.reset_demo          # wipe + reseed
    docker compose exec api python -m db.seed.reset_demo --keep-research
    docker compose exec api python -m db.seed.reset_demo --wipe-ai-runs
"""
import sys

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import text

from apps.api.core.db import SessionLocal
from db.seed import seed_brands, seed_compliance_rules

# Order matters: children before parents (FKs are ON DELETE CASCADE in most cases,
# but explicit ordering keeps this readable and independent of cascade config).
GENERATED_TABLES = [
    "compliance_reviews",
    "feedback",
    "lessons",
    "publishing_jobs",
    "analytics",
    "performance_insights",
    # Lead agent output. Cleared before content_versions so the outreach FK is
    # gone by the time its target rows are deleted, rather than relying on the
    # ON DELETE SET NULL to tidy up behind us.
    "lead_activities",
    "lead_signals",
    "leads",
    "content_versions",
    "content_assets",
    "campaigns",
    "content_opportunities",
]


def wipe(keep_research: bool = False, wipe_ai_runs: bool = False) -> None:
    db = SessionLocal()
    try:
        for table in GENERATED_TABLES:
            count = db.execute(text(f"DELETE FROM {table}")).rowcount
            print(f"  cleared {table:24s} ({count} rows)")

        if wipe_ai_runs:
            n = db.execute(text("DELETE FROM ai_runs")).rowcount
            print(f"  cleared ai_runs                 ({n} rows)  [--wipe-ai-runs]")
        else:
            print("  keeping ai_runs (audit/observability data; --wipe-ai-runs to clear)")

        if keep_research:
            print("  keeping competitor_observation chunks (--keep-research)")
        else:
            n = db.execute(
                text("DELETE FROM knowledge_chunks WHERE category = 'competitor_observation'")
            ).rowcount
            print(f"  cleared research observations   ({n} rows)")

        db.commit()
    finally:
        db.close()


def report_ai_runs(about_to_wipe: bool = False) -> None:
    """Print cumulative LLM spend before touching anything, so the number is on
    the record even when --wipe-ai-runs is about to discard it."""
    db = SessionLocal()
    try:
        row = db.execute(
            text(
                "SELECT count(*), count(*) FILTER (WHERE status='failed'), "
                "min(created_at), max(created_at) FROM ai_runs"
            )
        ).first()
        total, failed, first, last = row
        print(f"LLM spend on record: {total} calls ({failed} failed)")
        if total:
            print(f"  first: {first}\n  last:  {last}")
        if about_to_wipe and total:
            print("  ^ about to be erased by --wipe-ai-runs; note it now.")
    finally:
        db.close()


def verify() -> None:
    db = SessionLocal()
    try:
        checks = {
            "brands": "SELECT count(*) FROM brands",
            "knowledge_chunks": "SELECT count(*) FROM knowledge_chunks",
            "compliance_rules": "SELECT count(*) FROM compliance_rules",
            "content_versions": "SELECT count(*) FROM content_versions",
            "opportunities": "SELECT count(*) FROM content_opportunities",
            "feedback": "SELECT count(*) FROM feedback",
            "leads": "SELECT count(*) FROM leads",
            "ai_runs (kept)": "SELECT count(*) FROM ai_runs",
        }
        print("\nPost-reset state:")
        for label, sql in checks.items():
            print(f"  {label:20s} {db.execute(text(sql)).scalar()}")
    finally:
        db.close()


def main() -> None:
    keep_research = "--keep-research" in sys.argv
    wipe_ai_runs = "--wipe-ai-runs" in sys.argv
    report_ai_runs(about_to_wipe=wipe_ai_runs)
    print("\nWiping generated data...")
    wipe(keep_research=keep_research, wipe_ai_runs=wipe_ai_runs)
    print("\nReseeding reference data...")
    seed_brands.run()
    seed_compliance_rules.run()
    verify()
    print("\nDemo reset complete. Next: POST /research/run?brand_id=<jade>")


if __name__ == "__main__":
    main()
