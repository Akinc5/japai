"""Guards for the live judge demo. All THREE are deterministic and cost ZERO LLM calls.

They exist because this is the one surface a judge operates directly, live and
unsupervised, possibly adversarially:

  1. quota guard      — never start a live run that could die on quota mid-demo
  2. input guard      — never send junk, abuse, or prompt injection to the model
  3. rate limiter     — one overeager session can't drain the day's budget

The quota guard is re-evaluated on EVERY request, not cached at startup: the
count moves with every call the rest of the system makes, so a value read at
boot would be stale within seconds.
"""
import re
import time
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from apps.api.core.config import settings
from apps.api.models import AiRun

# --- 1. Quota guard --------------------------------------------------------


def calls_today(db: Session) -> int:
    """LLM calls recorded since midnight UTC. Counts every agent, not just the
    demo, because they all draw on the same upstream quota."""
    since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return db.query(func.count(AiRun.id)).filter(AiRun.created_at >= since).scalar() or 0


def quota_status(db: Session) -> dict:
    """Whether live mode is currently available, plus the numbers behind it so
    the UI can be honest rather than just saying 'unavailable'."""
    used = calls_today(db)
    ceiling = settings.DEMO_DAILY_CALL_CEILING
    margin = settings.DEMO_CALL_MARGIN
    threshold = max(ceiling - margin, 0)

    # A demo run costs roughly: 1 generation (+1 if localized) + ~2 compliance.
    est_cost_per_run = 4
    remaining = max(threshold - used, 0)

    return {
        "live_available": used < threshold,
        "calls_used_today": used,
        "ceiling": ceiling,
        "margin": margin,
        "threshold": threshold,
        "calls_remaining": remaining,
        "estimated_runs_remaining": remaining // est_cost_per_run,
        "note": (
            "Ceiling is a self-imposed operational budget, not a documented "
            "provider limit. Configure with DEMO_DAILY_CALL_CEILING."
        ),
    }


# --- 2. Input guard --------------------------------------------------------

MIN_INPUT_CHARS = 8
MAX_INPUT_CHARS = 300

# Prompt-injection shapes. Deliberately short and pattern-based: this is a guard
# rail, not a content classifier, and it must stay free and instant. Anything
# subtle enough to slip past here still faces the real 4-step compliance
# pipeline, which is the actual safety mechanism.
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+|any\s+)?previous",
    r"ignore\s+(the\s+)?above",
    r"disregard\s+(all\s+|any\s+)?(previous|prior|the above)",
    r"forget\s+(all\s+|everything\s+|your\s+)?(previous|prior|instructions)",
    r"you\s+are\s+now\s+(a|an)\b",
    r"act\s+as\s+(a|an)\b",
    r"pretend\s+(to\s+be|you\s+are)",
    r"system\s*prompt",
    r"reveal\s+(your|the)\s+(prompt|instructions|system)",
    r"print\s+(your|the)\s+(prompt|instructions)",
    r"</?\s*(system|assistant|user)\s*>",
    r"\bDAN\b\s+mode",
    r"jailbreak",
    r"developer\s+mode",
    r"override\s+(your|the)\s+(rules|instructions|guidelines)",
]

# Topic anchor: at least one of these should appear for the input to be
# plausibly about insurance marketing. Kept broad on purpose — a false reject is
# worse for a judge than letting a marginal topic through to compliance.
TOPIC_TERMS = [
    "insur", "cover", "coverage", "policy", "policies", "claim", "premium",
    "risk", "protect", "liability", "indemnity", "underwrit", "deductible",
    "excess", "peril", "loss", "theft", "damage", "transit", "cargo", "freight",
    "shipment", "jewel", "goldsmith", "stock", "inventory", "malpractice",
    "clinic", "practitioner", "doctor", "patient", "medical", "negligence",
    "broker", "renewal", "quote", "compensat", "reimburse", "warranty",
    "exclusion", "endorsement", "benefit", "safeguard", "secure", "security",
]

ABUSE_TERMS = [
    "fuck", "shit", "bitch", "bastard", "cunt", "asshole",
    "kill yourself", "kys", "retard", "nigger", "faggot",
]

FRIENDLY_REJECTION = (
    "Try a marketing claim related to insurance coverage, risk, or policy "
    "benefits — for example “our policy covers stock in transit” or “protect "
    "your inventory against theft”."
)


class InputGuardResult:
    def __init__(self, ok: bool, reason_code: str | None = None, message: str | None = None):
        self.ok = ok
        self.reason_code = reason_code
        self.message = message

    def as_dict(self) -> dict:
        return {"ok": self.ok, "reason_code": self.reason_code, "message": self.message}


def check_input(raw: str | None) -> InputGuardResult:
    """Cheap, deterministic sanity check on judge-supplied text.

    Never echoes the offending input back and never names which pattern matched
    — an adversarial user should not be able to use the error messages to map
    the filter.
    """
    text = (raw or "").strip()

    if not text:
        return InputGuardResult(False, "empty", "Please enter a marketing claim or topic.")

    if len(text) < MIN_INPUT_CHARS:
        return InputGuardResult(
            False, "too_short", f"That's a bit short — {FRIENDLY_REJECTION}"
        )

    if len(text) > MAX_INPUT_CHARS:
        return InputGuardResult(
            False,
            "too_long",
            f"Please keep it under {MAX_INPUT_CHARS} characters so the demo stays quick.",
        )

    lowered = text.lower()

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            # Deliberately vague: same message as off-topic, so probing the
            # filter tells an adversarial user nothing.
            return InputGuardResult(False, "rejected", FRIENDLY_REJECTION)

    if any(term in lowered for term in ABUSE_TERMS):
        return InputGuardResult(False, "rejected", FRIENDLY_REJECTION)

    if not any(term in lowered for term in TOPIC_TERMS):
        return InputGuardResult(False, "off_topic", FRIENDLY_REJECTION)

    return InputGuardResult(True)


# --- 3. Per-session rate limiter -------------------------------------------
# In-memory on purpose: this phase is meant to be pure orchestration over the
# existing schema, and a DB-backed limiter would mean a new table. The tradeoff
# is that the window resets when the API restarts, which is acceptable for a
# single-process demo and is stated in the README rather than hidden.

_RUNS: dict[str, list[float]] = {}


def check_rate_limit(session_key: str) -> dict:
    now = time.time()
    window = settings.DEMO_RATE_LIMIT_WINDOW_SECONDS
    limit = settings.DEMO_RATE_LIMIT_RUNS

    recent = [t for t in _RUNS.get(session_key, []) if now - t < window]
    _RUNS[session_key] = recent

    if len(recent) >= limit:
        retry_after = int(window - (now - recent[0])) + 1
        return {
            "allowed": False,
            "retry_after_seconds": max(retry_after, 1),
            "limit": limit,
            "window_seconds": window,
        }
    return {
        "allowed": True,
        "remaining": limit - len(recent),
        "limit": limit,
        "window_seconds": window,
    }


def record_run(session_key: str) -> None:
    """Called only after a run is actually admitted, so rejected requests (guard
    failures, rate limits) don't count against the caller's allowance."""
    _RUNS.setdefault(session_key, []).append(time.time())


def reset_rate_limits() -> None:
    """Test hook."""
    _RUNS.clear()
