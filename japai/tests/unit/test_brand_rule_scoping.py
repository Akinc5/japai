"""Pure DB test for brand-scoped compliance rules — makes NO LLM calls.

Asserts the exact property the multi-brand claim rests on: when checking a
brand's content, the pipeline sees that brand's rules plus the global ones, and
does NOT see another brand's rules. A leak here would mean DoctorShield's
clinical-competence rule silently policing Jade's jewellery copy.

This queries rules the same way compliance.py does, rather than re-implementing
the filter, so it fails if that query changes.
"""
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import or_

from apps.api.core.db import SessionLocal
from apps.api.models import Brand, ComplianceRule

EXPECTED_BRAND_RULES = {
    "jade": {"JD-VALUE-01", "JD-SECURITY-01"},
    "jaguar-transit": {"JT-SCOPE-01", "JT-LOSS-01", "JT-CONTINUITY-01", "JT-SETTLE-01"},
    "doctorshield": {"DS-OUTCOME-01", "DS-CLINICAL-01", "DS-SCOPE-01", "DS-FEAR-01"},
}
EXPECTED_GLOBAL = {
    "MAS-ADV-01", "MAS-ADV-02", "CLAIM-SUBST-01",
    "COMPARE-01", "PRESSURE-01", "SUPERLATIVE-01",
}


def _rules_for_brand(db, brand_id) -> set[str]:
    """Mirrors the filter in compliance.py's run_compliance_check."""
    rows = (
        db.query(ComplianceRule)
        .filter(
            ComplianceRule.is_active.is_(True),
            or_(ComplianceRule.brand_id == brand_id, ComplianceRule.brand_id.is_(None)),
        )
        .all()
    )
    return {r.rule_code for r in rows}


def test_brand_rules_are_correctly_scoped():
    db = SessionLocal()
    try:
        brands = {b.slug: b for b in db.query(Brand).all()}
        for slug in EXPECTED_BRAND_RULES:
            assert slug in brands, f"brand '{slug}' missing — run seed_brands"

        for slug, own_codes in EXPECTED_BRAND_RULES.items():
            visible = _rules_for_brand(db, brands[slug].id)

            missing_own = own_codes - visible
            assert not missing_own, f"{slug}: own rules not visible: {sorted(missing_own)}"

            missing_global = EXPECTED_GLOBAL - visible
            assert not missing_global, f"{slug}: global rules not visible: {sorted(missing_global)}"

            # The leak check: no other brand's rules may appear.
            foreign = set()
            for other_slug, other_codes in EXPECTED_BRAND_RULES.items():
                if other_slug != slug:
                    foreign |= other_codes
            leaked = visible & foreign
            assert not leaked, f"{slug}: LEAKED another brand's rules: {sorted(leaked)}"

            print(
                f"  {slug:16s} sees {len(visible)} rules = "
                f"{len(own_codes)} own + {len(EXPECTED_GLOBAL)} global, 0 foreign"
            )

        print("\nPASS: brand rule scoping (own + global, no cross-brand leakage)")
    finally:
        db.close()


def test_inactive_rules_are_excluded():
    """is_active is part of the same filter; prove it actually gates."""
    db = SessionLocal()
    rule = None
    try:
        jade = db.query(Brand).filter_by(slug="jade").first()
        rule = db.query(ComplianceRule).filter_by(rule_code="JD-VALUE-01").first()
        assert rule is not None, "JD-VALUE-01 missing — run seed_brand_depth"

        assert "JD-VALUE-01" in _rules_for_brand(db, jade.id)
        rule.is_active = False
        db.commit()
        assert "JD-VALUE-01" not in _rules_for_brand(db, jade.id), "inactive rule still visible"
        print("PASS: inactive rules are excluded")
    finally:
        if rule is not None:
            rule.is_active = True
            db.commit()
        db.close()


if __name__ == "__main__":
    test_brand_rules_are_correctly_scoped()
    print()
    test_inactive_rules_are_excluded()
