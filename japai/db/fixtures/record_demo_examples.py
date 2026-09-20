"""Record REAL demo runs into db/fixtures/demo_examples.json.

Every example in that file is captured verbatim from the live pipeline by this
script. Nothing is hand-written or edited afterwards — that is the whole point:
the fallback shown to a judge when quota is exhausted must be a real recorded
run, not a plausible-looking mock.

Each recorded example carries `recorded_at` and `recorded_by` so its provenance
is visible in the API response and the UI.

Costs real LLM calls (roughly 3-4 per scenario). Re-run only when the pipeline
changes enough that the recordings become misleading.

Usage:
    docker compose exec api python -m db.fixtures.record_demo_examples
    docker compose exec api python -m db.fixtures.record_demo_examples --opportunity-only
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import json as _json
import urllib.error
import urllib.request

from apps.api.core.db import SessionLocal
from apps.api.models import Brand, ContentOpportunity

# Calls the running API over HTTP with the stdlib rather than fastapi's
# TestClient, which would pull in httpx and force an image rebuild for a
# one-off recording script.
API_BASE = "http://localhost:8000"

OUT_PATH = Path(__file__).resolve().parent / "demo_examples.json"

SCENARIOS = [
    {
        "id": "clean_pass_en",
        "title": "Clean claim, English",
        "description": "A well-grounded claim that survives the full pipeline.",
        "brand_slug": "jade",
        "language": "en",
        "claim_or_topic": "our policy covers jewellery stock while it is in transit",
    },
    {
        "id": "blocked_absolutes_en",
        "title": "Absolute guarantees, English",
        "description": "Multiple absolute guarantees — caught with a real policy citation.",
        "brand_slug": "jade",
        "language": "en",
        "claim_or_topic": "we guarantee every claim is approved and your stock is 100% covered with zero risk",
    },
    {
        "id": "blocked_check_only_en",
        "title": "Forbidden phrases, checked as written",
        "description": (
            "Check-only mode: compliance judges the text exactly as supplied. The "
            "deterministic blocklist blocks it outright and steps 2-4 are skipped, "
            "so this verdict costs ZERO model calls."
        ),
        "brand_slug": "jade",
        "language": "en",
        "mode": "check_only",
        "claim_or_topic": (
            "Our jewellers block policy is guaranteed to pay every claim, no "
            "exceptions. Your stock is 100% covered and completely risk-free."
        ),
    },
    {
        "id": "localized_zh",
        "title": "Cultural adaptation, Chinese (Simplified)",
        "description": "Generated in English, adapted for Chinese-speaking Singapore owners, then compliance-checked in Chinese.",
        "brand_slug": "jade",
        "language": "zh-Hans",
        "claim_or_topic": "protecting jewellery inventory held in store overnight",
    },
]


def _post(path: str, body: dict, headers: dict) -> tuple[int, dict]:
    data = _json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}{path}", data=data, method="POST",
        headers={"Content-Type": "application/json", **headers},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return resp.status, _json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, {"detail": exc.read().decode("utf-8")[:300]}


def record_run_scenarios(db) -> list[dict]:
    recorded = []
    for spec in SCENARIOS:
        brand = db.query(Brand).filter_by(slug=spec["brand_slug"]).first()
        if brand is None:
            print(f"  ! brand '{spec['brand_slug']}' missing; skipping {spec['id']}")
            continue

        print(f"  recording {spec['id']} ...", flush=True)
        status, payload = _post(
            "/demo/run",
            {
                "brand_id": str(brand.id),
                "language": spec["language"],
                "claim_or_topic": spec["claim_or_topic"],
                "mode": spec.get("mode", "generate"),
            },
            {"x-demo-session": f"fixture-recorder-{spec['id']}"},
        )
        if status != 200:
            print(f"    FAILED http {status}: {str(payload)[:200]}")
            continue
        if payload.get("mode") != "live":
            print(f"    SKIPPED — endpoint returned mode={payload.get('mode')} (not a live run)")
            continue

        # Strip the volatile envelope: quota/rate-limit snapshots are true only
        # at capture time and would be misleading to replay later.
        payload.pop("quota", None)
        payload.pop("rate_limit", None)

        verdict = (payload.get("result") or {}).get("risk_level")
        print(f"    -> verdict={verdict}, refs={(payload.get('result') or {}).get('policy_refs')}")

        recorded.append(
            {
                "id": spec["id"],
                "title": spec["title"],
                "description": spec["description"],
                "kind": "demo_run",
                "language": spec["language"],
                "brand_name": brand.name,
                "claim_or_topic": spec["claim_or_topic"],
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "recorded_by": "record_demo_examples.py",
                "is_real_capture": True,
                **payload,
            }
        )
    return recorded


def record_opportunity_walkthrough(db) -> dict | None:
    """Captured from opportunities ALREADY in the database — costs zero LLM
    calls. The scoring breakdown is the interesting part and it is fully
    deterministic, so replaying it is exactly as truthful as regenerating it."""
    opp = (
        db.query(ContentOpportunity)
        .filter(ContentOpportunity.score_breakdown.isnot(None))
        .order_by(ContentOpportunity.priority_score.desc())
        .first()
    )
    if opp is None:
        print("  ! no scored opportunities in the DB; skipping opportunity walkthrough")
        return None

    brand = db.get(Brand, opp.brand_id)
    print(f"  recording opportunity walkthrough: {opp.title[:50]} (score {opp.priority_score})")
    return {
        "id": "opportunity_walkthrough",
        "title": "Opportunity scoring walkthrough",
        "description": (
            "How a content opportunity is scored. Fully deterministic and LLM-free — "
            "every number below is the actual input to the score."
        ),
        "kind": "opportunity",
        "language": "en",
        "brand_name": brand.name if brand else None,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "recorded_by": "record_demo_examples.py",
        "is_real_capture": True,
        "opportunity": {
            "title": opp.title,
            "rationale": opp.description,
            "opportunity_type": opp.opportunity_type,
            "score": float(opp.priority_score) if opp.priority_score is not None else None,
            "score_breakdown": opp.score_breakdown,
            "suggested_angle": opp.suggested_angle,
            "suggested_formats": opp.suggested_formats or [],
            "source_chunk_ids": opp.source_chunk_ids or [],
        },
    }


def main() -> None:
    opportunity_only = "--opportunity-only" in sys.argv
    db = SessionLocal()
    try:
        existing = []
        if OUT_PATH.exists():
            try:
                existing = json.loads(OUT_PATH.read_text(encoding="utf-8")).get("examples", [])
            except json.JSONDecodeError:
                existing = []

        examples: list[dict] = []
        if not opportunity_only:
            print("Recording live demo runs (costs real LLM calls)...")
            examples.extend(record_run_scenarios(db))
        else:
            # Keep previously recorded demo runs when only refreshing the
            # opportunity walkthrough.
            examples.extend([e for e in existing if e.get("kind") == "demo_run"])

        print("Recording opportunity walkthrough (0 LLM calls)...")
        walkthrough = record_opportunity_walkthrough(db)
        if walkthrough:
            examples.append(walkthrough)

        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "note": (
                "Every example here is a REAL captured run from the live pipeline, "
                "saved verbatim by db/fixtures/record_demo_examples.py. None of it is "
                "fabricated or hand-edited."
            ),
            "count": len(examples),
            "examples": examples,
        }
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"\nWrote {len(examples)} example(s) to {OUT_PATH}")
        for e in examples:
            verdict = (e.get("result") or {}).get("risk_level") or e.get("kind")
            print(f"  - {e['id']:26s} {e['language']:8s} {verdict}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
