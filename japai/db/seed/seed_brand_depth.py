"""Top up per-brand knowledge chunks and add brand-specific compliance rules.

WHY: Phase 1 seeded 6 chunks per brand (2 faq, 2 approved_claim, 1
restricted_claim, 1 brand_guideline). That is thin for two reasons:
  - compliance step 3 verifies extracted claims against `approved_claim` chunks,
    so a small approved set produces false "unsupported claim" flags;
  - the content agent has little brand-specific material to ground copy in.
This brings every brand to 13 chunks. All three brands are topped up, not just
the two newer ones — after the Phase 7 reset all three were equally thin, and
uneven depth would make a multi-brand comparison meaningless.

COMPLIANCE RULES: Phase 3 seeded 6 global rules (brand_id IS NULL). This adds
rules scoped to a single brand's actual risk profile. compliance.py already ORs
brand-specific and global rules together, so these apply automatically.

HONESTY NOTE: these are plausible internal marketing-review standards written
for a demo, not real JA Assure policy and not citations of specific statutes.
Rule codes are internal (DS-/JT-/JD- prefixes) precisely so they are not mistaken
for regulatory references. Where a real regulation might apply, the wording is
kept general and conservative rather than inventing a citation.

Idempotent: reruns skip anything already present.

Usage:
    docker compose exec api python -m db.seed.seed_brand_depth
"""
from dotenv import load_dotenv

load_dotenv()

from apps.api.core.db import SessionLocal
from apps.api.models import Brand, ComplianceRule, KnowledgeChunk

# --- knowledge chunk top-ups: (category, title, content) ------------------
EXTRA_CHUNKS: dict[str, list[tuple[str, str, str]]] = {
    "jade": [
        ("faq", "What happens if stock is lost in transit?",
         "Losses in transit are assessed against the declared transit limits in the policy "
         "schedule, including the route and the security arrangements in place at the time."),
        ("faq", "Are items on display covered outside business hours?",
         "Cover for items left on display outside business hours depends on the safe and "
         "security warranties agreed in the schedule; many policies require stock to be "
         "secured in a locked safe overnight."),
        ("approved_claim", "Approved claim framing — valuation basis",
         "You may state that Jade 'settles claims based on the valuation basis set out in the "
         "policy schedule', provided you do not promise a specific settlement figure."),
        ("approved_claim", "Approved claim framing — specialist underwriting",
         "You may state that Jade 'underwrites jewellers block risks specifically for the "
         "Singapore trade', as this reflects the actual underwriting focus."),
        ("restricted_claim", "Restricted claim — security conditions",
         "Do not imply that cover applies regardless of how stock is stored or secured. Safe "
         "and alarm warranties are conditions of cover, not optional recommendations."),
        ("restricted_claim", "Restricted claim — sentimental or stated value",
         "Do not imply that items are covered for a sentimental or customer-stated value. "
         "Settlement follows the valuation basis at the time of loss."),
        ("brand_guideline", "Audience and register",
         "Write to trade owners and managers, not consumers. Assume the reader understands "
         "their own trade; explain insurance mechanics, not jewellery."),
    ],
    "jaguar-transit": [
        ("faq", "Does cover continue during warehouse storage between legs?",
         "Incidental storage between transit legs is typically covered up to a stated number of "
         "days in the policy schedule; storage beyond that limit usually needs separate cover."),
        ("faq", "What is required to make a transit claim?",
         "Claims generally require the transport documents, a packing list, evidence of the "
         "declared value, and notice of loss or damage to the carrier within the contractual "
         "time limit."),
        ("approved_claim", "Approved claim framing — multi-modal routing",
         "You may state that Jaguar Transit 'covers consignments across air, sea and land legs "
         "under a single policy', provided you reference the declared route in the schedule."),
        ("approved_claim", "Approved claim framing — declared value basis",
         "You may state that Jaguar Transit 'settles transit losses against the declared value "
         "of the consignment', provided the declaration requirement is stated."),
        ("restricted_claim", "Restricted claim — universal coverage",
         "Do not imply cover applies to any cargo, any route, or any mode without declaration. "
         "Commodity, route, and value limits are core to how transit cover is priced."),
        ("restricted_claim", "Restricted claim — delay and consequential loss",
         "Do not imply that delay, loss of market, or consequential financial loss is covered. "
         "Standard transit cover addresses physical loss or damage."),
        ("brand_guideline", "Operational specificity",
         "Reference concrete operational realities — handover points, documentation, transit "
         "legs. Avoid abstract reassurance language that a logistics manager would dismiss."),
    ],
    "doctorshield": [
        ("faq", "Does cover continue after I stop practising?",
         "Claims arising from past treatment can surface years later. Run-off cover addresses "
         "this period and is arranged separately from the active practising policy."),
        ("faq", "Is cover affected by which procedures I perform?",
         "Yes. Cover is underwritten against a declared specialty and scope of practice; "
         "materially changing the procedures you perform should be declared to the insurer."),
        ("approved_claim", "Approved claim framing — legal cost cover",
         "You may state that DoctorShield 'covers legal defence costs for claims arising from "
         "clinical practice', provided the policy terms and declared specialty are referenced."),
        ("approved_claim", "Approved claim framing — regulatory representation",
         "You may state that DoctorShield 'provides representation in disciplinary and "
         "regulatory proceedings', provided you do not describe the likely outcome."),
        ("restricted_claim", "Restricted claim — clinical competence",
         "Do not imply that holding cover reflects a practitioner's clinical competence, safety "
         "record, or standard of care. The two are unrelated and conflating them is misleading."),
        ("restricted_claim", "Restricted claim — universal specialty cover",
         "Do not imply cover extends to every specialty, procedure, or territory. Scope depends "
         "on the declared specialty and the territorial limits in the schedule."),
        ("brand_guideline", "Peer register, never fear",
         "Write doctor-to-doctor. Do not use fear of litigation, licence loss, or career damage "
         "as a persuasion device; describe the practical support the cover provides instead."),
    ],
}

# --- brand-specific compliance rules --------------------------------------
# (rule_code, category, severity, description)
BRAND_RULES: dict[str, list[tuple[str, str, str, str]]] = {
    "doctorshield": [
        ("DS-OUTCOME-01", "claims", "high",
         "Must not state or imply a guaranteed legal outcome — that a claim will be "
         "successfully defended, dismissed, or settled favourably. Indemnity covers defence "
         "costs and damages subject to policy terms; it cannot promise how a case resolves."),
        ("DS-CLINICAL-01", "claims", "high",
         "Must not make comparative or absolute statements about a practitioner's clinical "
         "competence, safety record, or standard of care, and must not imply that holding "
         "cover is evidence of clinical quality."),
        ("DS-SCOPE-01", "disclosure", "high",
         "Must not imply cover applies across all specialties, procedures, or territories. "
         "Any statement of scope must acknowledge that cover follows the declared specialty "
         "and territorial limits."),
        ("DS-FEAR-01", "brand_safety", "medium",
         "Must not use fear-based framing about litigation, loss of licence, or career damage "
         "as a persuasion device. Messaging should describe practical support, not consequences."),
    ],
    "jaguar-transit": [
        ("JT-SCOPE-01", "disclosure", "high",
         "Must not imply blanket 'anywhere, anytime' or 'any cargo' coverage. Transit cover is "
         "bounded by declared route, mode, commodity and value, and any scope statement must "
         "not omit that."),
        ("JT-LOSS-01", "claims", "high",
         "Must not overstate transit-loss coverage by implying that all loss, damage, shortage "
         "or delay is covered regardless of cause. Standard exclusions such as inherent vice "
         "and insufficient packing apply."),
        ("JT-CONTINUITY-01", "claims", "medium",
         "Must not imply uninterrupted cover across multi-modal legs without reference to the "
         "transit clause and any incidental storage limits."),
        ("JT-SETTLE-01", "brand_safety", "low",
         "Must not promise specific claims settlement timeframes for transit losses, which "
         "depend on carrier documentation and survey findings."),
    ],
    "jade": [
        ("JD-VALUE-01", "claims", "medium",
         "Must not imply items are settled at a customer-stated or sentimental value. "
         "Settlement follows the valuation basis at the time of loss."),
        ("JD-SECURITY-01", "disclosure", "medium",
         "Must not imply cover applies regardless of storage or security arrangements. Safe, "
         "alarm and overnight-storage warranties are conditions of cover."),
    ],
}


def run() -> dict:
    db = SessionLocal()
    added_chunks = 0
    added_rules = 0
    try:
        for slug, chunks in EXTRA_CHUNKS.items():
            brand = db.query(Brand).filter_by(slug=slug).first()
            if brand is None:
                print(f"  ! brand '{slug}' missing — run seed_brands first; skipping")
                continue
            for category, title, content in chunks:
                exists = (
                    db.query(KnowledgeChunk)
                    .filter(
                        KnowledgeChunk.brand_id == brand.id,
                        KnowledgeChunk.title == title,
                    )
                    .first()
                )
                if exists is not None:
                    continue
                db.add(
                    KnowledgeChunk(
                        brand_id=brand.id,
                        category=category,
                        title=title,
                        content=content,
                        source="seed_brand_depth",
                    )
                )
                added_chunks += 1

        for slug, rules in BRAND_RULES.items():
            brand = db.query(Brand).filter_by(slug=slug).first()
            if brand is None:
                continue
            for rule_code, category, severity, description in rules:
                # rule_code is UNIQUE across the table, so this is the natural key.
                exists = db.query(ComplianceRule).filter_by(rule_code=rule_code).first()
                if exists is not None:
                    continue
                db.add(
                    ComplianceRule(
                        brand_id=brand.id,
                        rule_code=rule_code,
                        category=category,
                        severity=severity,
                        description=description,
                        is_active=True,
                    )
                )
                added_rules += 1

        db.commit()
        print(f"Added {added_chunks} knowledge chunk(s) and {added_rules} brand-specific rule(s).")
        return {"chunks": added_chunks, "rules": added_rules}
    finally:
        db.close()


if __name__ == "__main__":
    run()
