"""Localization agent — cultural adaptation, not translation.

The distinction matters and is enforced in the prompt: the model is told
explicitly that a faithful translation is a FAILED result, and is given
market-specific guidance per language (what persuades, what register is normal,
what to avoid) rather than "render this in X".

Structure mirrors the Phase 5 multi-format pattern: one campaign, N content
assets, each a variant. A localized asset is a NEW ContentAsset carrying
`language` and `source_content_asset_id`, with its own version chain, its own
compliance review, and its own place in the review queue. English approval does
not carry over — every localized asset is checked independently, in its own
language.

Brand voice comes from the same Brand record the English path uses, so voice
consistency holds across languages rather than each language drifting.

BLOCKLIST HONESTY: the non-English blocklists below were written from the
author's own language knowledge, not reviewed by a native speaker or a
compliance officer. They are deliberately short and cover the same categories as
the approved English list (guaranteed payout / 100% covered / risk-free / no
exceptions) rather than attempting exhaustive coverage. Before any real use they
need native-speaker and compliance review — this is a demo-grade safety net, and
the README says so.
"""
from uuid import UUID

from sqlalchemy.orm import Session

from apps.api.agents import compliance as compliance_agent
from apps.api.agents import lessons as lessons_agent
from apps.api.agents import optimization as optimization_agent
from apps.api.core import llm_client
from apps.api.core.config import settings
from apps.api.models import Brand, ContentAsset, ContentVersion

PROMPT_VERSION = "localization-v1"

DEFAULT_LANGUAGE = "en"

# Per-language configuration. `market_guidance` is the part that makes this
# localization rather than translation — it describes the market, not the words.
LANGUAGES: dict[str, dict] = {
    "en": {
        "name": "English",
        "endonym": "English",
        "market": "Singapore (English-speaking business audience)",
        "market_guidance": "Baseline language. Content is authored directly in English.",
        "blocklist": [],  # English uses compliance_agent.FORBIDDEN_PHRASES
    },
    "zh-Hans": {
        "name": "Chinese (Simplified)",
        "endonym": "简体中文",
        "market": "Chinese-speaking business owners in Singapore",
        "market_guidance": (
            "Write for Chinese-speaking business owners in Singapore, many of them "
            "family-run operators. Use Simplified characters and Singapore usage, not "
            "Mainland-specific or Taiwan-specific phrasing. Business register: "
            "relationship and longevity carry weight — continuity of the family "
            "business, protecting what has been built, prudence as a virtue. Prefer "
            "concrete, measured statements over emotive appeals. Do not use hard-sell "
            "urgency, which reads as untrustworthy in this market. Numerals and "
            "policy terms may stay in English where that is the normal trade usage."
        ),
        "blocklist": [
            "保证赔付",      # guaranteed payout
            "保证获赔",      # guaranteed claim approval
            "百分百赔付",    # 100% payout
            "100%赔付",
            "100%保障",     # 100% covered/protected
            "零风险",        # zero risk
            "无风险",        # no risk
            "绝对安全",      # absolutely safe
            "无条件赔付",    # unconditional payout
            "全额赔付保证",  # guarantee of full payout
            "必定赔付",      # will definitely pay out
        ],
    },
    "ms": {
        "name": "Malay",
        "endonym": "Bahasa Melayu",
        "market": "Malay-speaking business owners in Singapore",
        "market_guidance": (
            "Write in Bahasa Melayu as used in Singapore, for Malay-speaking business "
            "owners and operators. Use Singapore/Malaysian Malay vocabulary — e.g. "
            "'pejabat' for office, 'kereta' for car — NOT Indonesian forms. Register "
            "should be respectful and community-minded; 'amanah' (trustworthiness) and "
            "responsibility to family and community are persuasive framings. Avoid "
            "aggressive sales pressure. Keep insurance terms that the trade uses in "
            "English where a forced Malay coinage would be less clear."
        ),
        "blocklist": [
            "dijamin bayaran",       # guaranteed payout
            "jaminan tuntutan",      # claim guarantee
            "pasti dibayar",         # certain to be paid
            "100% dilindungi",       # 100% covered
            "dilindungi sepenuhnya", # fully protected
            "tanpa risiko",          # without risk
            "bebas risiko",          # risk-free
            "tiada risiko",          # no risk
            "tiada pengecualian",    # no exceptions
            "perlindungan penuh",    # full protection
        ],
    },
    "id": {
        "name": "Bahasa Indonesia",
        "endonym": "Bahasa Indonesia",
        "market": "Indonesian business owners (regional expansion market)",
        "market_guidance": (
            "Write in Bahasa Indonesia for Indonesian business owners. This is a "
            "DIFFERENT language from Malay — use Indonesian vocabulary ('kantor' not "
            "'pejabat', 'mobil' not 'kereta') and Indonesian business register. "
            "Indonesian business audiences respond to practical, operational detail "
            "and clear process ('bagaimana prosesnya'), and insurance penetration is "
            "lower, so briefly establishing why this cover exists is more useful than "
            "assuming familiarity. Keep the tone warm but professional; avoid both "
            "hard-sell urgency and overly formal bureaucratic phrasing."
        ),
        "blocklist": [
            "dijamin dibayar",       # guaranteed paid
            "jaminan klaim",         # claim guarantee
            "pasti dibayar",         # certain to be paid
            "100% dijamin",          # 100% guaranteed
            "100% ditanggung",       # 100% covered
            "ditanggung sepenuhnya", # fully covered
            "tanpa risiko",          # without risk
            "bebas risiko",          # risk-free
            "tanpa pengecualian",    # no exceptions
            "perlindungan penuh",    # full protection
        ],
    },
}

LOCALIZABLE_LANGUAGES = [code for code in LANGUAGES if code != DEFAULT_LANGUAGE]


def blocklist_for_language(language: str) -> list[str]:
    """English falls back to the approved 16-phrase list; other languages use
    their own. Returns [] for an unknown language rather than silently applying
    the English list to text it cannot match."""
    if language == DEFAULT_LANGUAGE:
        return compliance_agent.FORBIDDEN_PHRASES
    return LANGUAGES.get(language, {}).get("blocklist", [])


def _build_localization_prompt(brand: Brand, spec: dict, source_body: str) -> str:
    return "\n".join(
        [
            f"Adapt the marketing copy below for {spec['market']}, in {spec['name']} "
            f"({spec['endonym']}).",
            "",
            "THIS IS NOT A TRANSLATION TASK. A faithful sentence-by-sentence "
            "translation is a FAILED result. You are re-expressing the same "
            "underlying offer for a different market: change the framing, the "
            "emphasis, the examples and the order of ideas wherever the target "
            "market would find a different angle more persuasive. Keep the "
            "substance of what is being offered identical — do not introduce any "
            "coverage, benefit, or guarantee that is not in the source.",
            "",
            f"Market guidance: {spec['market_guidance']}",
            "",
            f"Brand voice (must hold across languages): {brand.voice_description or 'N/A'}",
            f"Tone guidelines: {brand.tone_guidelines or 'N/A'}",
            "",
            "Compliance constraints carry over in full: never state or imply "
            "guaranteed payouts, guaranteed claim approval, total or unconditional "
            "protection, or absence of risk — in any language.",
            "",
            f"Output ONLY the adapted copy in {spec['name']}. No preamble, no "
            "translation notes, no English gloss.",
            "",
            "--- SOURCE COPY (English) ---",
            source_body,
        ]
    )


def localize_content_version(
    db: Session, content_version_id: UUID, language: str
) -> ContentVersion:
    """Create a localized sibling asset + version, then run the FULL compliance
    pipeline against it in its own language.

    One LLM call for the adaptation; compliance then costs its own calls, exactly
    as it does for English.
    """
    if language not in LANGUAGES:
        raise ValueError(
            f"Unsupported language '{language}'. Supported: {sorted(LANGUAGES)}"
        )
    if language == DEFAULT_LANGUAGE:
        raise ValueError(
            "Source content is already English; pick a target language other than 'en'."
        )

    source_version = db.get(ContentVersion, content_version_id)
    if source_version is None:
        raise ValueError(f"Content version {content_version_id} not found")

    source_asset = source_version.content_asset
    if source_asset.language != DEFAULT_LANGUAGE:
        raise ValueError(
            f"Can only localize from English source content "
            f"(this asset is '{source_asset.language}')."
        )

    brand = db.get(Brand, source_asset.brand_id)
    if brand is None:
        raise ValueError(f"Brand {source_asset.brand_id} not found")

    # Idempotency: one localized asset per (source asset, language).
    existing = (
        db.query(ContentAsset)
        .filter(
            ContentAsset.source_content_asset_id == source_asset.id,
            ContentAsset.language == language,
        )
        .first()
    )
    if existing is not None:
        current = (
            db.query(ContentVersion)
            .filter(
                ContentVersion.content_asset_id == existing.id,
                ContentVersion.is_current.is_(True),
            )
            .first()
        )
        if current is not None:
            return current

    spec = LANGUAGES[language]
    prompt = _build_localization_prompt(brand, spec, source_version.body)

    localized_asset = ContentAsset(
        campaign_id=source_asset.campaign_id,
        brand_id=source_asset.brand_id,
        asset_type=source_asset.asset_type,
        platform=source_asset.platform,
        title=f"[{language}] {source_asset.title or ''}"[:200],
        status="draft",
        created_by="localization_agent",
        origin=source_asset.origin,
        language=language,
        source_content_asset_id=source_asset.id,
    )
    db.add(localized_asset)
    db.flush()

    body = llm_client.generate(
        prompt,
        db,
        system=(
            f"You are a marketing localization specialist for {spec['market']}. "
            f"You adapt insurance marketing for local markets. You never produce "
            f"literal translations, and you never invent coverage."
        ),
        model=settings.GEMINI_MODEL,
        agent_name="localization_agent",
        prompt_version=PROMPT_VERSION,
        related_entity_type="content_asset",
        related_entity_id=localized_asset.id,
    )

    source_meta = source_version.version_metadata or {}
    version = ContentVersion(
        content_asset_id=localized_asset.id,
        version_number=1,
        body=body,
        version_metadata={
            "prompt_version": PROMPT_VERSION,
            "model_used": settings.GEMINI_MODEL,
            "language": language,
            "language_name": spec["name"],
            "localized_from_version_id": str(source_version.id),
            "localized_from_asset_id": str(source_asset.id),
            "market": spec["market"],
            "system_prompt": prompt,
            # Provenance carries over from the English source: the localized copy
            # rests on the same approved knowledge chunks.
            "sources": source_meta.get("sources", []),
            "topic": source_meta.get("topic"),
            "platform": source_asset.platform,
        },
        generated_by_agent="localization_agent",
        status="draft",
        is_current=True,
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    # Independent compliance, in the target language. An English pass grants the
    # localized version nothing.
    compliance_agent.run_compliance_check(db, version)
    db.refresh(version)
    return version


def localize_to_all(
    db: Session, content_version_id: UUID, languages: list[str] | None = None
) -> list[ContentVersion]:
    targets = languages or LOCALIZABLE_LANGUAGES
    return [localize_content_version(db, content_version_id, lang) for lang in targets]
