"""Load the committed demo snapshot so a fresh clone opens populated.

WHY: the demo content (research, opportunities, compliance-checked content in
four languages, reviewer decisions, lessons, leads, simulated analytics and
insights) was produced by real LLM runs. Regenerating it on every clone would
make first run slow and quota-dependent. `db/fixtures/demo_snapshot.sql` is a
data-only dump of the demo database captured after those runs — real output,
not hand-written fixtures. Loading it makes NO LLM calls.

It REPLACES every table's contents (reference data included, since seeded
brand/chunk UUIDs are random and content rows reference the captured ones), so
it refuses to run over a database that already has content unless --force.
`ai_runs` is part of the snapshot: it is the real call history behind the
content, and it is what /observability displays.

Usage:
    docker compose exec api alembic upgrade head
    docker compose exec api python -m db.seed.load_demo_snapshot
    docker compose exec api python -m db.seed.load_demo_snapshot --force   # replace existing data

Regenerate the snapshot from a populated database:
    docker compose exec -T postgres pg_dump -U ja_assure -d ja_assure --data-only \
        --inserts --no-owner --no-privileges --exclude-table=alembic_version \
        > db/fixtures/demo_snapshot.sql
"""
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import text

from apps.api.core.db import engine

SNAPSHOT = Path(__file__).resolve().parents[1] / "fixtures" / "demo_snapshot.sql"
# The snapshot's columns match this migration; loading it into any other schema
# would fail part-way or silently drop meaning.
SCHEMA_REVISION = "0010"
# pg_dump 16.15+ wraps output in psql-only meta-commands; they are not SQL.
_PSQL_META = re.compile(r"^\\(un)?restrict \S+$")


def main() -> None:
    force = "--force" in sys.argv

    with engine.connect() as conn:
        try:
            revision = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        except Exception:
            revision = None
        if revision != SCHEMA_REVISION:
            sys.exit(
                f"Schema is at {revision!r}, snapshot needs {SCHEMA_REVISION!r}. "
                "Run: docker compose exec api alembic upgrade head"
            )
        existing = conn.execute(text("SELECT count(*) FROM content_assets")).scalar()
        tables = conn.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
            )
        ).scalars().all()

    if existing and not force:
        sys.exit(
            f"Database already has {existing} content assets. Refusing to replace it. "
            "Re-run with --force to wipe ALL data (ai_runs included) and load the snapshot."
        )

    sql = "\n".join(
        line for line in SNAPSHOT.read_text(encoding="utf-8").splitlines()
        if not _PSQL_META.match(line)
    )

    # Raw DBAPI cursor: the dump is many statements with literal colons in copy
    # text, which SQLAlchemy's text() would misread as bind parameters.
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        # content_assets references itself (localized -> source asset), so
        # insert order cannot satisfy every FK; disable FK triggers for the load.
        cur.execute("SET session_replication_role = replica")
        cur.execute("TRUNCATE " + ", ".join(f'public."{t}"' for t in tables) + " CASCADE")
        cur.execute(sql)
        cur.execute("SET session_replication_role = DEFAULT")
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()
        # The dump sets search_path='' on its session; don't hand that
        # connection back to anything else in this process.
        engine.dispose()

    with engine.connect() as conn:
        print("Demo snapshot loaded:")
        for label, sql_count in {
            "brands": "SELECT count(*) FROM brands",
            "compliance_rules": "SELECT count(*) FROM compliance_rules",
            "content_assets": "SELECT count(*) FROM content_assets",
            "submitted_for_review": "SELECT count(*) FROM content_versions WHERE status = 'submitted_for_review'",
            "opportunities": "SELECT count(*) FROM content_opportunities",
            "leads": "SELECT count(*) FROM leads",
            "analytics (simulated)": "SELECT count(*) FROM analytics",
            "ai_runs": "SELECT count(*) FROM ai_runs",
        }.items():
            print(f"  {label:22s} {conn.execute(text(sql_count)).scalar()}")


if __name__ == "__main__":
    main()
