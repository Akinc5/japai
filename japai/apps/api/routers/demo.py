"""Live judge demo — an orchestration layer over already-verified agents.

This router reimplements NOTHING. Generation goes through content.py,
localization through localization.py, and compliance through
compliance.run_compliance_check unchanged. What it adds is the safety envelope a
judge-operated surface needs: a quota guard, an input guard, a rate limit, and
an honest fallback to real recorded runs when live mode is unavailable.

Step breakdown is DERIVED from the real ComplianceReview, not simulated:
  - step 1 is recomputed with the same pure, free _scan_blocklist function;
  - steps 3 and 4 are separated by whether an issue carries a policy_ref
    (step 4, the LLM review cites rules) or is an "Unsupported claim:" finding
    (step 3, the deterministic verifier).
Nothing here invents a verdict the pipeline did not actually produce.
"""
import json
from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api.agents import compliance as compliance_agent
from apps.api.agents import content as content_agent
from apps.api.agents import localization as localization_agent
from apps.api.agents.compliance import RISK_LEVEL_BY_OUTCOME
from apps.api.core import demo_guards
from apps.api.core.db import get_db
from apps.api.models import Brand, ComplianceReview, ContentAsset, ContentVersion

router = APIRouter(prefix="/demo", tags=["demo"])

FIXTURES_PATH = Path(__file__).resolve().parents[3] / "db" / "fixtures" / "demo_examples.json"

SUPPORTED_LANGUAGES = list(localization_agent.LANGUAGES.keys())


class DemoRunRequest(BaseModel):
    brand_id: UUID
    language: str = Field(default="en")
    claim_or_topic: str = Field(default="")
    # "generate" (default): write new copy about the topic, then check it.
    # "check_only": run compliance against the judge's LITERAL text.
    #
    # check_only exists because of an empirically observed property: the content
    # agent is itself compliance-aware and usually refuses to reproduce
    # forbidden phrases, so generated copy trips Step 1 only sometimes. Observed
    # across ~7 runs with blatant prompts: mostly 'review', occasionally a real
    # Step 1 block when the model did emit a forbidden phrase. That variance is
    # fine for a demo but bad for a guaranteed talking point, so check_only
    # makes the deterministic blocklist reliably demonstrable. It costs ZERO LLM
    # calls when it blocks and reuses run_compliance_check unchanged.
    #
    # Literal, not str: an unrecognised mode used to fall through to "generate"
    # and spend real quota. On a judge-operated endpoint an unknown mode should
    # be a free 422, not a silent live run.
    mode: Literal["generate", "check_only"] = Field(default="generate")


def _session_key(request: Request) -> str:
    """Prefer an explicit session header so multiple tabs on one machine are
    treated as one session; fall back to client host."""
    return request.headers.get("x-demo-session") or (
        request.client.host if request.client else "unknown"
    )


def _load_fixtures() -> list[dict]:
    if not FIXTURES_PATH.exists():
        return []
    try:
        with FIXTURES_PATH.open(encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("examples", [])
    except (json.JSONDecodeError, OSError):
        return []


def _pick_fixture(language: str | None = None, prefer_verdict: str | None = None) -> dict | None:
    examples = _load_fixtures()
    if not examples:
        return None
    if language:
        matches = [e for e in examples if e.get("language") == language]
        if matches:
            examples = matches
    if prefer_verdict:
        matches = [e for e in examples if e.get("result", {}).get("risk_level") == prefer_verdict]
        if matches:
            examples = matches
    return examples[0]


def _step(key: str, label: str, status: str, detail: str, **extra) -> dict:
    return {"key": key, "label": label, "status": status, "detail": detail, **extra}


def _build_steps(
    body: str,
    language: str,
    review: ComplianceReview | None,
    localized_from: str | None,
    user_input: str = "",
) -> list[dict]:
    """Reconstruct the pipeline stages from what actually happened."""
    steps: list[dict] = []

    steps.append(
        _step("input_guard", "Input accepted", "pass", "Passed length, topic and injection checks.")
    )

    # Informational, free, and worth showing: the content agent is itself
    # compliance-aware and will refuse to write a forbidden phrase, so step 1
    # rarely fires on generated copy. Scanning the judge's OWN words makes the
    # deterministic scan visible, and makes the point that the guard would have
    # caught it had the generator complied.
    input_hits = compliance_agent._scan_blocklist(user_input, "en") if user_input else []
    if input_hits:
        steps.append(
            _step(
                "input_scan",
                "Your wording vs. the forbidden-phrase list",
                "warn",
                "Your input itself contains phrasing that is blocked outright in "
                "insurance marketing. The content agent is compliance-aware and will "
                "not reproduce it — but if it had, Step 1 below would have blocked it.",
                terms=[h["term"] for h in input_hits],
            )
        )

    gen_detail = f"Generated with the content agent, grounded in approved brand knowledge."
    if localized_from:
        gen_detail = (
            "Generated in English, then culturally adapted (not translated) into "
            f"{localization_agent.LANGUAGES.get(language, {}).get('name', language)}."
        )
    steps.append(_step("generation", "Content generated", "pass", gen_detail))

    if review is None:
        steps.append(_step("compliance", "Compliance", "error", "No compliance review recorded."))
        return steps

    issues = review.detected_issues or []

    # Step 1 — recomputed with the same free, deterministic function.
    blocklist_hits = compliance_agent._scan_blocklist(body, language)
    if blocklist_hits:
        steps.append(
            _step(
                "blocklist",
                "Step 1 · Forbidden-phrase scan",
                "fail",
                f"{len(blocklist_hits)} blocklisted phrase(s) found — blocked immediately.",
                terms=[h["term"] for h in blocklist_hits],
                language=language,
            )
        )
        steps.append(
            _step(
                "short_circuit",
                "Steps 2-4 skipped",
                "skipped",
                "A blocklist hit blocks outright, so no LLM calls were spent on "
                "content that was already doomed.",
            )
        )
        return steps

    terms_checked = len(localization_agent.blocklist_for_language(language))
    steps.append(
        _step(
            "blocklist",
            "Step 1 · Forbidden-phrase scan",
            "pass",
            f"No blocklisted phrases found ({terms_checked} {language} terms checked).",
            language=language,
        )
    )

    unsupported = [i for i in issues if not i.get("policy_ref")]
    cited = [i for i in issues if i.get("policy_ref")]

    steps.append(
        _step(
            "claims",
            "Step 2-3 · Claim extraction & verification",
            "warn" if unsupported else "pass",
            f"{len(unsupported)} claim(s) could not be matched to approved brand knowledge."
            if unsupported
            else "All extracted claims matched approved brand knowledge.",
            issues=unsupported,
        )
    )

    risk = RISK_LEVEL_BY_OUTCOME.get(review.outcome, "review")
    status = {"pass": "pass", "review": "warn", "block": "fail"}.get(risk, "warn")
    steps.append(
        _step(
            "review",
            "Step 4 · Compliance review",
            status,
            f"Verdict: {risk}. {len(cited)} issue(s) cited a specific policy rule.",
            issues=cited,
            policy_refs=sorted({i["policy_ref"] for i in cited if i.get("policy_ref")}),
        )
    )
    return steps


def _result_payload(version: ContentVersion, review: ComplianceReview | None) -> dict:
    metadata = version.version_metadata or {}
    issues = (review.detected_issues or []) if review else []
    return {
        "content_version_id": str(version.id),
        "body": version.body,
        "status": version.status,
        "outcome": review.outcome if review else None,
        "risk_level": RISK_LEVEL_BY_OUTCOME.get(review.outcome, "review") if review else None,
        "detected_issues": issues,
        "policy_refs": sorted({i["policy_ref"] for i in issues if i.get("policy_ref")}),
        "suggested_revision": metadata.get("suggested_revision"),
        "reviewer_type": review.reviewer_type if review else None,
    }


def _run_check_only(db: Session, brand: Brand, payload: DemoRunRequest, session_key: str) -> dict:
    """Compliance against the judge's literal text — no generation step.

    Stored with origin='manual' so it is excluded from the rejection-rate
    metric, the review queue and the lessons loop (all of which whitelist
    origin='agent'), exactly like test fixtures are.
    """
    campaign = content_agent.get_or_create_ad_hoc_campaign(db, brand)
    asset = ContentAsset(
        campaign_id=campaign.id,
        brand_id=brand.id,
        asset_type="social_post",
        platform="linkedin",
        title=f"[demo check] {payload.claim_or_topic[:80]}",
        status="draft",
        created_by="judge_demo",
        origin="manual",
        language=payload.language,
    )
    db.add(asset)
    db.flush()

    version = ContentVersion(
        content_asset_id=asset.id,
        version_number=1,
        body=payload.claim_or_topic.strip(),
        version_metadata={"demo_mode": "check_only", "language": payload.language},
        generated_by_agent="judge_demo",
        status="draft",
        is_current=True,
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    compliance_agent.run_compliance_check(db, version)
    db.refresh(version)

    review = (
        db.query(ComplianceReview)
        .filter(ComplianceReview.content_version_id == version.id)
        .order_by(ComplianceReview.reviewed_at.desc())
        .first()
    )

    steps = [
        _step("input_guard", "Input accepted", "pass", "Passed length, topic and injection checks."),
        _step(
            "generation",
            "Generation skipped",
            "skipped",
            "Check-only mode: your text is judged exactly as written, with no "
            "generation step in between.",
        ),
    ]
    # Reuse the same step derivation, minus the two stages this mode replaces
    # (input_guard and generation are already represented above).
    steps.extend(
        s
        for s in _build_steps(version.body, payload.language, review, None, user_input="")
        if s["key"] not in ("input_guard", "generation")
    )

    return {
        "mode": "live",
        "demo_mode": "check_only",
        "live_available": True,
        "recorded": False,
        "brand": {"id": str(brand.id), "name": brand.name, "slug": brand.slug},
        "language": payload.language,
        "language_name": localization_agent.LANGUAGES.get(payload.language, {}).get("name"),
        "claim_or_topic": payload.claim_or_topic.strip(),
        "english_source": None,
        "compliance_ran_on": "your text exactly as written",
        "steps": steps,
        "result": _result_payload(version, review),
        "quota": demo_guards.quota_status(db),
        "rate_limit": demo_guards.check_rate_limit(session_key),
    }


@router.get("/quota-status")
def get_quota_status(db: Session = Depends(get_db)):
    status = demo_guards.quota_status(db)
    status["fallback_examples_available"] = len(_load_fixtures())
    return status


@router.get("/fallback-examples")
def fallback_examples():
    """Pre-recorded REAL runs. Every payload here was produced by the live
    pipeline and saved verbatim — see db/fixtures/demo_examples.json."""
    examples = _load_fixtures()
    return {
        "count": len(examples),
        "recorded": True,
        "note": (
            "These are real captured runs, not fabricated samples. Each was produced "
            "by POST /demo/run against the live pipeline and saved verbatim."
        ),
        "examples": examples,
    }


@router.get("/suggestions")
def suggestions():
    """Starter prompts for judges who would rather click than type. Two are
    expected to pass, two to be caught — one bluntly, one subtly."""
    return {
        "suggestions": [
            {
                "label": "Stock in transit (clean)",
                "text": "our policy covers jewellery stock while it is in transit",
                "expectation": "likely pass / review",
            },
            {
                "label": "Overnight security (clean)",
                "text": "protecting jewellery inventory held in store overnight",
                "expectation": "likely pass / review",
            },
            # Outcome here is genuinely variable, and the expectation text says
            # so rather than promising one path. The generator is itself
            # compliance-aware, so sometimes it sanitises the phrase (caught
            # later at Step 4) and sometimes it emits one (blocked at Step 1).
            # Both are real results; neither is scripted.
            {
                "label": "Guaranteed payout (blunt)",
                "text": "our insurance guarantees a payout on every claim with no exceptions",
                "expectation": (
                    "your wording is flagged against the forbidden-phrase list; the copy "
                    "is then blocked either at Step 1 or Step 4 depending on whether the "
                    "generator sanitised it"
                ),
            },
            {
                "label": "Unsupported comparison (subtle)",
                "text": "our coverage settles claims faster than any other insurer in Singapore",
                "expectation": "caught later as an unsubstantiated comparative claim",
            },
        ]
    }


@router.post("/run")
def run_demo(payload: DemoRunRequest, request: Request, db: Session = Depends(get_db)):
    session_key = _session_key(request)

    # --- rate limit (cheapest check first) ---
    rate = demo_guards.check_rate_limit(session_key)
    if not rate["allowed"]:
        return {
            "mode": "rate_limited",
            "message": (
                f"That's {rate['limit']} runs in {rate['window_seconds']} seconds — "
                f"give it {rate['retry_after_seconds']}s and try again."
            ),
            "retry_after_seconds": rate["retry_after_seconds"],
            "rate_limit": rate,
        }

    # --- input guard (free, and must run before any model call) ---
    guard = demo_guards.check_input(payload.claim_or_topic)
    if not guard.ok:
        return {
            "mode": "rejected",
            "input_guard": guard.as_dict(),
            "message": guard.message,
        }

    if payload.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language. Supported: {SUPPORTED_LANGUAGES}",
        )

    brand = db.get(Brand, payload.brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    # --- quota guard, re-evaluated on EVERY request ---
    quota = demo_guards.quota_status(db)
    if not quota["live_available"]:
        example = _pick_fixture(language=payload.language)
        return {
            "mode": "recorded",
            "live_available": False,
            "quota": quota,
            "message": (
                "Live demo temporarily paused to protect the remaining daily quota — "
                "showing a real recorded run instead."
            ),
            "example": example,
            "recorded": True,
        }

    demo_guards.record_run(session_key)

    if payload.mode == "check_only":
        return _run_check_only(db, brand, payload, session_key)

    # --- real pipeline, unchanged agents ---
    version = content_agent.generate_content(
        db,
        brand_id=brand.id,
        platform="linkedin",
        topic=payload.claim_or_topic.strip(),
    )
    localized_from = None

    if payload.language == localization_agent.DEFAULT_LANGUAGE:
        compliance_agent.run_compliance_check(db, version)
        db.refresh(version)
        final_version = version
    else:
        # Phase 9 path: localize_content_version runs the FULL compliance
        # pipeline against the localized copy in its own language.
        english_body = version.body
        final_version = localization_agent.localize_content_version(
            db, version.id, payload.language
        )
        localized_from = english_body

    review = (
        db.query(ComplianceReview)
        .filter(ComplianceReview.content_version_id == final_version.id)
        .order_by(ComplianceReview.reviewed_at.desc())
        .first()
    )

    return {
        "mode": "live",
        "live_available": True,
        "recorded": False,
        "brand": {"id": str(brand.id), "name": brand.name, "slug": brand.slug},
        "language": payload.language,
        "language_name": localization_agent.LANGUAGES.get(payload.language, {}).get("name"),
        "claim_or_topic": payload.claim_or_topic.strip(),
        "english_source": localized_from,
        "compliance_ran_on": (
            "the localized copy, in its own language"
            if localized_from
            else "the generated English copy"
        ),
        "steps": _build_steps(
            final_version.body,
            payload.language,
            review,
            localized_from,
            user_input=payload.claim_or_topic.strip(),
        ),
        "result": _result_payload(final_version, review),
        "quota": demo_guards.quota_status(db),
        "rate_limit": demo_guards.check_rate_limit(session_key),
    }
