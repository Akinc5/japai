"""Lead agent.

SCOPE HONESTY — read this before believing anything the demo shows you.

This is NOT a lead-generation or prospecting system. Nothing here scrapes a
business directory, queries Google Places / Hunter, or enriches against a real
data provider. The prospect list below is a **hand-authored synthetic dataset**
of fictional businesses, written to be plausible for Jade's actual market so the
pipeline shape is demonstrable. Every row it writes is stamped
`leads.source='seed_data'` precisely so this can never be mistaken for real
sourced data later.

What IS real is the pipeline shape around it:
  source -> deterministic fit scoring -> LLM outreach drafting -> the SAME
  compliance pipeline content goes through -> the SAME human review queue.

Scoring is fully deterministic and LLM-free (same philosophy as the Opportunity
agent): every number that produces a score is persisted in `score_breakdown`
and written out as `lead_signals` rows, so the ranking is explainable.
Exactly one LLM call is spent per lead, and only on the outreach copy.
"""
import re
from uuid import UUID

from sqlalchemy.orm import Session

from apps.api.agents import compliance as compliance_agent
from apps.api.agents import content as content_agent
from apps.api.models import Brand, ContentVersion, Lead, LeadActivity, LeadSignal

PROMPT_VERSION = "lead-outreach-v1"

# --- Scoring weights -------------------------------------------------------
# Deliberately simple and transparent. Each component is normalised to 0..1,
# multiplied by its weight, summed, then capped. Weights sum to 100 so a
# perfect-fit lead scores exactly 100 with no capping sleight of hand.
W_CATEGORY = 40
W_SIZE = 30
W_LOCATION = 20
W_SIGNALS = 10
SCORE_CAP = 100
SCORE_FORMULA = (
    "category_match*40 + size_fit*30 + location_match*20 + signal_bonus*10, capped at 100"
)

# The ideal-headcount band differs per brand: a jeweller and a freight operator
# of the same size are completely different prospects. Big enough to hold real
# exposure, small enough not to be self-insured or already on a global tower.
SIZE_SWEET_SPOT_BY_BRAND_SLUG: dict[str, tuple[int, int]] = {
    "jade": (5, 50),            # independent jewellers / goldsmiths
    "jaguar-transit": (20, 200),  # freight forwarders and logistics operators
    "doctorshield": (2, 30),      # clinics and small specialist practices
}
DEFAULT_SIZE_SWEET_SPOT = (5, 50)
SIZE_TOLERANCE = 60  # staff beyond the band before size_fit decays to 0

# Home market. A lead outside it is still scoreable, just materially weaker.
TARGET_MARKET_TERMS = ["singapore", "sg"]

# Cheap qualifying signals. Each present signal contributes an equal share of
# signal_bonus. These are attributes of the business, not of the data source.
QUALIFYING_SIGNALS = [
    "physical_storefront",
    "high_value_inventory",
    "trade_show_exhibitor",
    "on_site_workshop",
    "multi_outlet",
]

STOPWORDS = {"and", "the", "for", "with", "in", "of", "to", "a"}


# --- Seed dataset ----------------------------------------------------------
# FICTIONAL businesses. Names, contacts and staff counts are invented. Contact
# details use example.com and the reserved +65 9000 xxxx block so nothing here
# can reach a real person or business.
JADE_SEED_LEADS: list[dict] = [
    {
        "company_name": "Tanglin Fine Jewellers",
        "contact_name": "Operations Manager",
        "email": "enquiries@tanglinfine.example.com",
        "phone": "+65 9000 0101",
        "category": "independent jeweller",
        "location": "Orchard Road, Singapore",
        "employee_count": 12,
        "signals": ["physical_storefront", "high_value_inventory", "trade_show_exhibitor"],
    },
    {
        "company_name": "Goldsmith & Co Pte Ltd",
        "contact_name": "Workshop Principal",
        "email": "hello@goldsmithco.example.com",
        "phone": "+65 9000 0102",
        "category": "goldsmith and bespoke jewellery workshop",
        "location": "Chinatown, Singapore",
        "employee_count": 6,
        "signals": ["on_site_workshop", "high_value_inventory"],
    },
    {
        "company_name": "Straits Heritage Jewellery",
        "contact_name": "Retail Director",
        "email": "contact@straitsheritage.example.com",
        "phone": "+65 9000 0103",
        "category": "jewellery retailer",
        "location": "Katong, Singapore",
        "employee_count": 45,
        "signals": ["physical_storefront", "multi_outlet", "high_value_inventory"],
    },
    {
        "company_name": "Kampong Glam Gem Traders",
        "contact_name": "Managing Partner",
        "email": "trade@kgglamgems.example.com",
        "phone": "+65 9000 0104",
        "category": "gemstone dealer",
        "location": "Kampong Glam, Singapore",
        "employee_count": 4,
        "signals": ["trade_show_exhibitor", "high_value_inventory"],
    },
    {
        "company_name": "Novena Bridal Jewellery",
        "contact_name": "Store Owner",
        "email": "bridal@novenabridal.example.com",
        "phone": "+65 9000 0105",
        "category": "bridal jewellery retailer",
        "location": "Novena, Singapore",
        "employee_count": 8,
        "signals": ["physical_storefront"],
    },
    {
        "company_name": "Lion City Pawn & Gold",
        "contact_name": "Branch Manager",
        "email": "info@lioncitypawn.example.com",
        "phone": "+65 9000 0106",
        "category": "pawnbroker and gold dealer",
        "location": "Geylang, Singapore",
        "employee_count": 15,
        "signals": ["physical_storefront", "high_value_inventory", "multi_outlet"],
    },
    # Deliberately weaker fits, so the scoring visibly discriminates rather than
    # rubber-stamping everything at 90+.
    {
        "company_name": "Pacific Gem Wholesale",
        "contact_name": "Distribution Lead",
        "email": "sales@pacificgemwholesale.example.com",
        "phone": "+65 9000 0107",
        "category": "gemstone wholesaler and distributor",
        "location": "Jurong, Singapore",
        "employee_count": 180,
        "signals": ["high_value_inventory"],
    },
    {
        "company_name": "Emerald Court Jewellers",
        "contact_name": "General Manager",
        "email": "office@emeraldcourt.example.com",
        "phone": "+60 3 0000 0108",
        "category": "jewellery retailer",
        "location": "Kuala Lumpur, Malaysia",
        "employee_count": 20,
        "signals": ["physical_storefront"],
    },
]

# Same construction as JADE_SEED_LEADS: fictional businesses, example.com
# contacts, reserved phone ranges. Categories are chosen to match each brand's
# stated target_audience so category_match has real signal to work with, and
# each list carries deliberately weaker fits so the scoring still discriminates.
JAGUAR_TRANSIT_SEED_LEADS: list[dict] = [
    {
        "company_name": "Keppel Bay Freight Forwarding",
        "contact_name": "Operations Director",
        "email": "ops@keppelbayfreight.example.com",
        "phone": "+65 9000 0201",
        "category": "freight forwarder and logistics operator",
        "location": "Keppel, Singapore",
        "employee_count": 85,
        "signals": ["high_value_inventory", "multi_outlet"],
    },
    {
        "company_name": "Changi Air Cargo Services",
        "contact_name": "Cargo Manager",
        "email": "cargo@changiaircargo.example.com",
        "phone": "+65 9000 0202",
        "category": "air cargo handler and shipper",
        "location": "Changi, Singapore",
        "employee_count": 140,
        "signals": ["high_value_inventory", "multi_outlet"],
    },
    {
        "company_name": "Tuas Bonded Logistics",
        "contact_name": "Warehouse Principal",
        "email": "enquiries@tuasbonded.example.com",
        "phone": "+65 9000 0203",
        "category": "logistics operator and bonded warehousing",
        "location": "Tuas, Singapore",
        "employee_count": 60,
        "signals": ["high_value_inventory", "on_site_workshop"],
    },
    {
        "company_name": "Orchard Secure Couriers",
        "contact_name": "Managing Director",
        "email": "hello@orchardsecure.example.com",
        "phone": "+65 9000 0204",
        "category": "high-value courier and cargo shipper",
        "location": "Orchard, Singapore",
        "employee_count": 28,
        "signals": ["high_value_inventory"],
    },
    {
        "company_name": "Jurong Heavy Haulage",
        "contact_name": "Fleet Manager",
        "email": "fleet@jurongheavy.example.com",
        "phone": "+65 9000 0205",
        "category": "heavy haulage and industrial transport",
        "location": "Jurong, Singapore",
        "employee_count": 110,
        "signals": ["multi_outlet"],
    },
    # Weaker fits: one tiny operator, one outside the home market.
    {
        "company_name": "Little India Parcel Runners",
        "contact_name": "Owner",
        "email": "contact@liparcel.example.com",
        "phone": "+65 9000 0206",
        "category": "local parcel delivery",
        "location": "Little India, Singapore",
        "employee_count": 6,
        "signals": [],
    },
    {
        "company_name": "Port Klang Cargo Partners",
        "contact_name": "General Manager",
        "email": "office@portklangcargo.example.com",
        "phone": "+60 3 0000 0207",
        "category": "freight forwarder and cargo shipper",
        "location": "Port Klang, Malaysia",
        "employee_count": 95,
        "signals": ["high_value_inventory"],
    },
]

DOCTORSHIELD_SEED_LEADS: list[dict] = [
    {
        "company_name": "Novena Specialist Practice",
        "contact_name": "Practice Manager",
        "email": "admin@novenaspecialist.example.com",
        "phone": "+65 9000 0301",
        "category": "specialist doctors and medical practice",
        "location": "Novena, Singapore",
        "employee_count": 12,
        "signals": ["physical_storefront", "multi_outlet"],
    },
    {
        "company_name": "Bukit Timah Family Clinic",
        "contact_name": "Clinic Director",
        "email": "reception@btfamilyclinic.example.com",
        "phone": "+65 9000 0302",
        "category": "general practitioners and allied healthcare",
        "location": "Bukit Timah, Singapore",
        "employee_count": 8,
        "signals": ["physical_storefront"],
    },
    {
        "company_name": "Raffles Place Dermatology",
        "contact_name": "Lead Consultant",
        "email": "enquiries@rpdermatology.example.com",
        "phone": "+65 9000 0303",
        "category": "specialist dermatology practitioners",
        "location": "Raffles Place, Singapore",
        "employee_count": 6,
        "signals": ["physical_storefront", "high_value_inventory"],
    },
    {
        "company_name": "East Coast Orthopaedic Partners",
        "contact_name": "Managing Partner",
        "email": "partners@ecortho.example.com",
        "phone": "+65 9000 0304",
        "category": "specialist surgeons and healthcare practitioners",
        "location": "East Coast, Singapore",
        "employee_count": 18,
        "signals": ["physical_storefront", "multi_outlet"],
    },
    {
        "company_name": "Tampines Allied Health Centre",
        "contact_name": "Centre Manager",
        "email": "info@tampinesallied.example.com",
        "phone": "+65 9000 0305",
        "category": "allied healthcare practitioners",
        "location": "Tampines, Singapore",
        "employee_count": 22,
        "signals": ["physical_storefront"],
    },
    # Weaker fits: a large hospital group (likely already covered corporately)
    # and a non-clinical wellness business.
    {
        "company_name": "Sentosa Wellness Spa",
        "contact_name": "Operations Lead",
        "email": "hello@sentosawellness.example.com",
        "phone": "+65 9000 0306",
        "category": "wellness and spa services",
        "location": "Sentosa, Singapore",
        "employee_count": 25,
        "signals": ["physical_storefront"],
    },
    {
        "company_name": "Pan-Asia Hospital Group",
        "contact_name": "Head of Risk",
        "email": "risk@panasiahospital.example.com",
        "phone": "+65 9000 0307",
        "category": "hospital group and medical practitioners",
        "location": "Central, Singapore",
        "employee_count": 900,
        "signals": ["multi_outlet"],
    },
]

SEED_LEADS_BY_BRAND_SLUG: dict[str, list[dict]] = {
    "jade": JADE_SEED_LEADS,
    "jaguar-transit": JAGUAR_TRANSIT_SEED_LEADS,
    "doctorshield": DOCTORSHIELD_SEED_LEADS,
}


def _normalise(word: str) -> str:
    """Crude singular/plural fold, deliberately not a real stemmer.

    Without this, a business described as "independent jeweller" matches a target
    market of "independent jewellers" at only 0.5 — the plural 's' alone halves a
    correct match. Folding a trailing 's' fixes the common case while staying
    inspectable; it is not trying to be linguistically complete.
    """
    return word[:-1] if len(word) > 3 and word.endswith("s") else word


def _tokens(text: str) -> set[str]:
    return {
        _normalise(w)
        for w in re.findall(r"[a-z]{3,}", (text or "").lower())
        if w not in STOPWORDS
    }


def score_category_match(category: str, brand: Brand) -> tuple[float, dict]:
    """Keyword overlap between the lead's category and the brand's stated target
    audience. Pure function of its inputs — no DB, no LLM."""
    lead_tokens = _tokens(category)
    target_tokens = _tokens(brand.target_audience or "")
    overlap = sorted(lead_tokens & target_tokens)
    fraction = len(overlap) / len(lead_tokens) if lead_tokens else 0.0
    return fraction, {
        "matched_terms": overlap,
        "lead_terms": sorted(lead_tokens),
        "fraction": round(fraction, 4),
    }


def score_size_fit(
    employee_count: int | None, band: tuple[int, int] = DEFAULT_SIZE_SWEET_SPOT
) -> tuple[float, dict]:
    """1.0 inside the sweet spot, decaying linearly outside it to 0 at the
    tolerance edge. Unknown headcount scores a neutral 0.5 rather than 0, so a
    missing field doesn't masquerade as a bad fit."""
    low, high = band
    if employee_count is None:
        return 0.5, {"employee_count": None, "band": [low, high], "note": "unknown -> neutral 0.5"}
    if low <= employee_count <= high:
        fit = 1.0
    elif employee_count < low:
        fit = max(0.0, employee_count / low)
    else:
        overshoot = employee_count - high
        fit = max(0.0, 1.0 - overshoot / SIZE_TOLERANCE)
    return fit, {"employee_count": employee_count, "band": [low, high], "fit": round(fit, 4)}


def score_location_match(location: str) -> tuple[float, dict]:
    lowered = (location or "").lower()
    hit = next((term for term in TARGET_MARKET_TERMS if term in lowered), None)
    return (1.0 if hit else 0.0), {"location": location, "matched_term": hit}


def score_signal_bonus(signals: list[str]) -> tuple[float, dict]:
    recognised = [s for s in signals if s in QUALIFYING_SIGNALS]
    fraction = len(recognised) / len(QUALIFYING_SIGNALS)
    return fraction, {
        "present": recognised,
        "possible": QUALIFYING_SIGNALS,
        "fraction": round(fraction, 4),
    }


def score_lead(profile: dict, brand: Brand) -> dict:
    """Deterministic fit score. Returns the full breakdown, not just the number,
    so the UI and the DB can show the arithmetic."""
    category_match, category_detail = score_category_match(profile["category"], brand)
    band = SIZE_SWEET_SPOT_BY_BRAND_SLUG.get(brand.slug, DEFAULT_SIZE_SWEET_SPOT)
    size_fit, size_detail = score_size_fit(profile.get("employee_count"), band)
    location_match, location_detail = score_location_match(profile.get("location", ""))
    signal_bonus, signal_detail = score_signal_bonus(profile.get("signals", []))

    components = {
        "category_match": {
            "value": round(category_match, 4),
            "weight": W_CATEGORY,
            "points": round(category_match * W_CATEGORY, 2),
            "detail": category_detail,
        },
        "size_fit": {
            "value": round(size_fit, 4),
            "weight": W_SIZE,
            "points": round(size_fit * W_SIZE, 2),
            "detail": size_detail,
        },
        "location_match": {
            "value": round(location_match, 4),
            "weight": W_LOCATION,
            "points": round(location_match * W_LOCATION, 2),
            "detail": location_detail,
        },
        "signal_bonus": {
            "value": round(signal_bonus, 4),
            "weight": W_SIGNALS,
            "points": round(signal_bonus * W_SIGNALS, 2),
            "detail": signal_detail,
        },
    }
    raw_total = sum(c["points"] for c in components.values())
    final = min(round(raw_total, 2), SCORE_CAP)

    return {
        "formula": SCORE_FORMULA,
        "components": components,
        "raw_total": round(raw_total, 2),
        "capped_at": SCORE_CAP,
        "score": final,
    }


def _fit_reason(breakdown: dict, brand_name: str) -> str:
    """One human sentence naming the strongest scoring components. Feeds the
    outreach prompt so the copy references why this business was picked."""
    ranked = sorted(
        breakdown["components"].items(), key=lambda kv: kv[1]["points"], reverse=True
    )
    parts = []
    for name, comp in ranked[:2]:
        if comp["points"] <= 0:
            continue
        if name == "category_match":
            terms = comp["detail"]["matched_terms"]
            parts.append(
                f"their trade matches {brand_name}'s target market ({', '.join(terms)})"
                if terms
                else "their trade is adjacent to the target market"
            )
        elif name == "size_fit":
            parts.append(f"they are an independently-sized operator ({comp['detail']['employee_count']} staff)")
        elif name == "location_match":
            parts.append("they operate in the home market")
        elif name == "signal_bonus":
            parts.append("they show " + ", ".join(comp["detail"]["present"]).replace("_", " "))
    return "; ".join(parts) or "limited qualifying signals on file"


def _build_outreach_context(profile: dict, breakdown: dict, brand_name: str) -> str:
    """Lead-specific personalisation appended to the content agent's own brand
    system prompt, so outreach inherits voice, approved claims, restricted
    claims and the lessons loop instead of re-deriving them.

    The brand name is passed in rather than hardcoded: this block is injected
    into whichever brand's prompt is generating, so a literal 'Jade' here would
    tell the model to write about Jade in a DoctorShield email.
    """
    return "\n".join(
        [
            "You are writing a first-touch outreach email to a prospective "
            "business client, not a social post.",
            f"Prospect: {profile['company_name']}",
            f"Trade / category: {profile['category']}",
            f"Location: {profile['location']}",
            f"Approximate size: {profile['employee_count']} staff",
            f"Why they were shortlisted: {_fit_reason(breakdown, brand_name)}",
            "",
            "Requirements: keep it under 150 words. Open by referencing their "
            f"specific trade, not a generic greeting. State plainly what {brand_name} "
            "covers and why it is relevant to a business like theirs. Close with "
            "a low-pressure next step (an offer to share details or arrange a "
            "short call). Do not promise cover, pricing, or acceptance. Do not "
            "invent anything about this business beyond the facts given above.",
        ]
    )


def _upsert_lead(db: Session, brand: Brand, profile: dict, source: str) -> Lead:
    """Idempotent on (brand_id, company_name) so re-running the agent re-scores
    the existing rows instead of duplicating the prospect list."""
    lead = (
        db.query(Lead)
        .filter(Lead.brand_id == brand.id, Lead.company_name == profile["company_name"])
        .first()
    )
    if lead is None:
        lead = Lead(brand_id=brand.id, company_name=profile["company_name"])
        db.add(lead)

    lead.contact_name = profile.get("contact_name")
    lead.email = profile.get("email")
    lead.phone = profile.get("phone")
    lead.category = profile.get("category")
    lead.location = profile.get("location")
    lead.employee_count = profile.get("employee_count")
    lead.source = source
    return lead


def _write_signals(db: Session, lead: Lead, breakdown: dict) -> None:
    """Mirror each scoring component into `lead_signals`. Replaces prior rows so
    a re-score doesn't accumulate stale signals."""
    db.query(LeadSignal).filter(LeadSignal.lead_id == lead.id).delete()
    for name, comp in breakdown["components"].items():
        db.add(
            LeadSignal(
                lead_id=lead.id,
                signal_type=name,
                signal_value=str(comp["value"]),
                weight=comp["points"],
            )
        )


def source_and_score_leads(db: Session, brand_id: UUID, source: str = "seed_data") -> list[Lead]:
    """Sourcing + deterministic scoring. Makes ZERO LLM calls, so this is safe to
    run repeatedly while iterating on the formula."""
    brand = db.get(Brand, brand_id)
    if brand is None:
        raise ValueError(f"Brand {brand_id} not found")

    profiles = SEED_LEADS_BY_BRAND_SLUG.get(brand.slug)
    if not profiles:
        raise ValueError(
            f"No seed prospect dataset defined for brand '{brand.slug}'. "
            f"Available: {sorted(SEED_LEADS_BY_BRAND_SLUG)}"
        )

    leads: list[Lead] = []
    for profile in profiles:
        breakdown = score_lead(profile, brand)
        lead = _upsert_lead(db, brand, profile, source)
        lead.score = breakdown["score"]
        lead.score_breakdown = breakdown
        db.flush()
        _write_signals(db, lead, breakdown)
        leads.append(lead)

    db.commit()
    for lead in leads:
        db.refresh(lead)
    return sorted(leads, key=lambda x: float(x.score or 0), reverse=True)


def draft_outreach_for_lead(db: Session, lead: Lead) -> ContentVersion:
    """One LLM call. The draft is stored as a ContentVersion (asset_type='email')
    so it flows through the existing compliance pipeline and the existing review
    queue rather than a parallel approval path."""
    brand = db.get(Brand, lead.brand_id)
    if brand is None:
        raise ValueError(f"Lead {lead.id} has no brand")

    breakdown = lead.score_breakdown or score_lead(
        {
            "category": lead.category,
            "location": lead.location,
            "employee_count": lead.employee_count,
            "signals": [],
        },
        brand,
    )
    profile = {
        "company_name": lead.company_name,
        "category": lead.category,
        "location": lead.location,
        "employee_count": lead.employee_count,
    }

    version = content_agent.generate_content(
        db,
        brand_id=brand.id,
        platform="email",
        topic=f"outreach to {lead.company_name}",
        content_format="outreach_email",
        extra_context=_build_outreach_context(profile, breakdown, brand.name),
    )

    # Insurance marketing rules apply to outreach exactly as they do to content.
    compliance_agent.run_compliance_check(db, version)
    db.refresh(version)

    lead.outreach_content_version_id = version.id
    db.add(
        LeadActivity(
            lead_id=lead.id,
            activity_type="outreach_drafted",
            description=(
                f"Outreach draft generated (content_version {version.id}); "
                f"compliance outcome: {version.status}. Not sent."
            ),
            performed_by="lead_agent",
        )
    )
    db.commit()
    db.refresh(lead)
    return version


def generate_leads(
    db: Session,
    brand_id: UUID,
    draft_outreach: bool = True,
    max_outreach: int = 3,
    source: str = "seed_data",
) -> dict:
    """Full pass: source -> score -> draft outreach for the top N.

    `max_outreach` caps LLM spend: one call per drafted lead, highest-scoring
    first, because that is the order a human would actually work the list.
    """
    leads = source_and_score_leads(db, brand_id, source=source)

    drafted = []
    if draft_outreach:
        for lead in leads[:max_outreach]:
            version = draft_outreach_for_lead(db, lead)
            drafted.append(
                {
                    "lead_id": str(lead.id),
                    "company_name": lead.company_name,
                    "content_version_id": str(version.id),
                    "status": version.status,
                }
            )

    return {
        "brand_id": str(brand_id),
        "source": source,
        "leads_sourced": len(leads),
        "outreach_drafted": len(drafted),
        "drafts": drafted,
    }
