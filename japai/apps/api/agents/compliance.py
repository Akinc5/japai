import re

from sqlalchemy import or_
from sqlalchemy.orm import Session

from apps.api.core import llm_client
from apps.api.core.config import settings
from apps.api.models import ComplianceReview, ComplianceRule, ContentVersion, KnowledgeChunk

# --- Step 1: deterministic blocklist ---------------------------------------

FORBIDDEN_PHRASES = [
    "guaranteed",
    "guaranteed approval",
    "guaranteed payout",
    "100% covered",
    "risk-free",
    "zero risk",
    "no risk",
    "no exceptions",
    "fully protected",
    "always covered",
    "never denied",
    "claims always approved",
    "instant payout",
    "no questions asked",
    "loss-proof",
    "cannot be rejected",
]


def _scan_blocklist(body: str, language: str = "en") -> list[dict]:
    """Scan against the blocklist for the content's OWN language.

    An English-only scan is worthless against Chinese or Indonesian copy — the
    forbidden phrase simply will not appear as an English substring. The
    per-language lists live in localization.py alongside the rest of each
    language's configuration.

    Imported lazily because localization.py imports this module for the English
    list, and a module-level import would be circular.
    """
    from apps.api.agents.localization import blocklist_for_language

    lower = body.lower()
    phrases = blocklist_for_language(language)
    return [
        {
            "term": phrase,
            "reason": f"Contains blocklisted phrase '{phrase}'"
            + ("" if language == "en" else f" ({language})"),
            "policy_ref": None,
        }
        for phrase in phrases
        # Chinese has no word boundaries and is not case-sensitive; lowering is a
        # no-op there and substring matching is the correct approach for all three.
        if phrase.lower() in lower
    ]


# --- Step 2: claim extraction -----------------------------------------------

EXTRACTION_PROMPT_VERSION = "compliance-extract-v1"
CLAIM_EXTRACTION_SCHEMA = {"type": "array", "items": {"type": "string"}}


def _extract_claims(db: Session, content_version: ContentVersion, language: str = "en") -> list[str]:
    # Claims are always extracted IN ENGLISH, whatever language the copy is in.
    # Step 3 matches them by keyword overlap against the brand's approved_claim
    # chunks, which are English, and its _keywords() regex is [a-zA-Z]{4,} —
    # ASCII-only. Chinese copy would yield zero keywords, score 0.0 overlap, and
    # flag every single claim as unsupported. Extracting to English keeps
    # verification meaningful across all four languages without duplicating the
    # knowledge base per language.
    language_note = (
        ""
        if language == "en"
        else (
            f"\n\nThe copy below is in {language}. Extract the claims but express each one "
            "IN ENGLISH, so they can be checked against an English knowledge base. "
            "Translate the claim's meaning faithfully; do not soften or omit any claim."
        )
    )
    prompt = (
        "Extract every distinct factual or coverage claim made in this marketing copy as a "
        "JSON array of short standalone strings. A claim is a specific, checkable statement "
        "about what is covered, how the product behaves, or what the company does — not general "
        "brand voice or calls to action. If there are no such claims, return an empty array."
        f"{language_note}\n\n"
        f"Copy:\n{content_version.body}"
    )
    try:
        claims = llm_client.generate_json(
            prompt,
            db,
            schema=CLAIM_EXTRACTION_SCHEMA,
            model=settings.GEMINI_MODEL,
            agent_name="compliance_agent",
            prompt_version=EXTRACTION_PROMPT_VERSION,
            related_entity_type="content_version",
            related_entity_id=content_version.id,
        )
    except (llm_client.LLMResponseError, llm_client.LLMUnavailableError):
        # Fallback to sentence extraction when LLM RPM quota is cooling down
        sentences = re.split(r"[.!?\n]+", content_version.body)
        claims = [s.strip() for s in sentences if len(s.strip()) > 25][:5]
    if not isinstance(claims, list):
        return []
    return [c for c in claims if isinstance(c, str) and c.strip()]



# --- Step 3: claim verification (heuristic, no embeddings yet) -------------

STOPWORDS = {"the", "and", "for", "with", "about", "your", "from", "that", "this", "will", "have"}
SUPPORT_THRESHOLD = 0.3
RESTRICTED_THRESHOLD = 0.4


def _keywords(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    return {w for w in words if w not in STOPWORDS}


def _overlap_ratio(claim_kw: set[str], chunk_kw: set[str]) -> float:
    if not claim_kw:
        return 0.0
    return len(claim_kw & chunk_kw) / len(claim_kw)


def _verify_claims(db: Session, brand_id, claims: list[str]) -> list[dict]:
    if not claims:
        return []

    approved = (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.brand_id == brand_id, KnowledgeChunk.category == "approved_claim")
        .all()
    )
    restricted = (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.brand_id == brand_id, KnowledgeChunk.category == "restricted_claim")
        .all()
    )
    approved_kw = [_keywords(c.content) for c in approved]
    restricted_kw = [_keywords(c.content) for c in restricted]

    issues = []
    for claim in claims:
        claim_kw = _keywords(claim)
        if not claim_kw:
            continue
        best_restricted = max((_overlap_ratio(claim_kw, kw) for kw in restricted_kw), default=0.0)
        best_approved = max((_overlap_ratio(claim_kw, kw) for kw in approved_kw), default=0.0)

        if best_restricted >= RESTRICTED_THRESHOLD:
            issues.append(
                {
                    "term": claim,
                    "reason": "Restricted claim overlap: closely matches a claim this brand is not "
                    "permitted to make.",
                    "policy_ref": None,
                }
            )
        elif best_approved < SUPPORT_THRESHOLD:
            issues.append(
                {
                    "term": claim,
                    "reason": "Unsupported claim: no matching approved_claim knowledge chunk found "
                    "for this brand.",
                    "policy_ref": None,
                }
            )
    return issues


# --- Step 4: LLM compliance review ------------------------------------------

REVIEW_PROMPT_VERSION = "compliance-review-v1"
COMPLIANCE_REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "risk_level": {"type": "string", "enum": ["pass", "review", "block"]},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "term": {"type": "string"},
                    "reason": {"type": "string"},
                    "policy_ref": {"type": "string", "nullable": True},
                },
                "required": ["term", "reason"],
            },
        },
        "suggested_revision": {"type": "string", "nullable": True},
    },
    "required": ["risk_level", "issues"],
}

_VALID_RISK_LEVELS = {"pass", "review", "block"}


def _llm_review(
    db: Session,
    content_version: ContentVersion,
    flagged_claims: list[dict],
    rules: list[ComplianceRule],
    language: str = "en",
) -> dict:
    rules_text = (
        "\n".join(f"- [{r.rule_code}] ({r.severity}) {r.description}" for r in rules)
        or "(no compliance rules on file)"
    )
    flagged_text = "\n".join(f"- {c['term']}: {c['reason']}" for c in flagged_claims) or "(none)"

    # The rules and the reviewer's reasoning stay in English (that is how the
    # rules are written and how issues are read by the team), but the copy being
    # judged is not. Saying so explicitly stops the model treating non-English
    # copy as an anomaly, and keeps issue text readable for an English reviewer.
    language_note = (
        ""
        if language == "en"
        else (
            f"\n\nIMPORTANT: the copy below is written in {language}. Judge it as it "
            "would be read by a native speaker of that language, including implied "
            "meaning and idiom — a guarantee implied idiomatically is still a "
            "guarantee. Write your issue REASONS in English so the compliance team "
            "can read them, but quote the offending phrase in its original "
            f"language. The suggested_revision must be written in {language}, "
            "because it is replacement copy that has to be usable as-is."
        )
    )
    prompt = (
        "You are a compliance reviewer for a Singapore insurance marketing team. Review the "
        f"marketing copy below and return a risk_level.{language_note}\n\n"
        f"Marketing copy:\n{content_version.body}\n\n"
        f"Compliance rules to check against:\n{rules_text}\n\n"
        f"Pre-flagged unsupported/restricted claims (from an earlier automated check):\n{flagged_text}\n\n"
        "Use risk_level='block' for clear violations of the rules above (e.g. implied guaranteed "
        "outcomes, misleading absolute claims). Use 'review' for borderline issues, unsupported "
        "claims, or pressure tactics that a human should check before publishing. Use 'pass' only "
        "if there are no real concerns. List every real issue you find in issues, citing the "
        "matching rule_code as policy_ref where one applies, otherwise null. Only include a "
        "suggested_revision if risk_level is 'review' or 'block'."
    )
    try:
        result = llm_client.generate_json(
            prompt,
            db,
            schema=COMPLIANCE_REVIEW_SCHEMA,
            model=settings.GEMINI_MODEL,
            agent_name="compliance_agent",
            prompt_version=REVIEW_PROMPT_VERSION,
            related_entity_type="content_version",
            related_entity_id=content_version.id,
        )
    except (llm_client.LLMResponseError, llm_client.LLMUnavailableError):
        # Fallback to deterministic verification when LLM rate limit is reached
        result = {
            "risk_level": "review" if flagged_claims else "pass",
            "issues": [
                {
                    "term": f.get("term", ""),
                    "reason": f.get("reason", ""),
                    "policy_ref": "CLAIM-SUBST-01" if "unsupported" in str(f.get("reason", "")).lower() else "DISCL-REQ-01",
                }
                for f in flagged_claims
            ],
            "suggested_revision": None,
        }

    if not isinstance(result, dict) or result.get("risk_level") not in _VALID_RISK_LEVELS:
        result = {
            "risk_level": "review" if flagged_claims else "pass",
            "issues": [
                {
                    "term": f.get("term", "unsupported_claim"),
                    "reason": f.get("reason", "Flagged during claim verification against approved knowledge chunks."),
                    "policy_ref": "CLAIM-SUBST-01",
                }
                for f in flagged_claims
            ],
            "suggested_revision": None,
        }
    result.setdefault("issues", [])
    result.setdefault("suggested_revision", None)
    return result



# --- Orchestration -----------------------------------------------------------

OUTCOME_BY_RISK_LEVEL = {"pass": "pass", "review": "needs_human_review", "block": "fail"}
RISK_LEVEL_BY_OUTCOME = {"pass": "pass", "needs_human_review": "review", "fail": "block", "warning": "review"}


def run_compliance_check(db: Session, content_version: ContentVersion) -> ComplianceReview:
    language = getattr(content_version.content_asset, "language", "en") or "en"
    blocklist_issues = _scan_blocklist(content_version.body, language)

    if blocklist_issues:
        risk_level = "block"
        reviewer_type = "deterministic"
        detected_issues = blocklist_issues
        suggested_revision = None
        notes = f"{len(blocklist_issues)} blocklisted phrase(s) found."
    else:
        brand_id = content_version.content_asset.brand_id
        claims = _extract_claims(db, content_version, language)
        flagged_claims = _verify_claims(db, brand_id, claims)
        rules = (
            db.query(ComplianceRule)
            .filter(
                ComplianceRule.is_active.is_(True),
                or_(ComplianceRule.brand_id == brand_id, ComplianceRule.brand_id.is_(None)),
            )
            .all()
        )
        review_result = _llm_review(db, content_version, flagged_claims, rules, language)

        risk_level = review_result["risk_level"]
        reviewer_type = "llm"
        detected_issues = flagged_claims + review_result["issues"]
        suggested_revision = review_result["suggested_revision"]
        notes = f"Pipeline verdict: {risk_level} ({len(detected_issues)} issue(s))."

    content_version.status = "rejected" if risk_level == "block" else "submitted_for_review"
    if suggested_revision:
        metadata = dict(content_version.version_metadata or {})
        metadata["suggested_revision"] = suggested_revision
        content_version.version_metadata = metadata

    review = ComplianceReview(
        content_version_id=content_version.id,
        compliance_rule_id=None,
        reviewer_type=reviewer_type,
        reviewer_name="compliance_pipeline_v2",
        outcome=OUTCOME_BY_RISK_LEVEL[risk_level],
        detected_issues=detected_issues,
        notes=notes,
    )
    db.add(review)
    db.add(content_version)
    db.commit()
    db.refresh(review)
    return review
