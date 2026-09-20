"""Proves brand-specific compliance rules actually fire — and only for their brand.

tests/unit/test_brand_rule_scoping.py proves the *query* is scoped correctly with
no LLM calls. This goes one step further and proves the rules reach the model and
change its verdict, which is the part a scoping test cannot show.

The fixture deliberately contains NO blocklisted phrase, so step 1 cannot
short-circuit it — the verdict has to come from steps 2-4 with the brand's rules
in the prompt.

Costs ~2 LLM calls per brand run. Fixtures are origin='test_fixture' and are
excluded from the review queue, metrics and lessons.
"""
from dotenv import load_dotenv

load_dotenv()

from apps.api.agents import compliance as compliance_agent
from apps.api.agents import content as content_agent
from apps.api.core.db import SessionLocal
from apps.api.models import Brand, ContentAsset, ContentVersion

# Violates DS-OUTCOME-01 (implying a guaranteed legal outcome) and
# DS-CLINICAL-01 (cover as evidence of clinical quality). Contains none of the
# 16 blocklisted phrases, so step 1 passes it through to the LLM review.
DS_VIOLATION = (
    "With DoctorShield behind you, a malpractice claim will be defended "
    "successfully and dismissed before it ever reaches a hearing. Doctors who "
    "carry our cover are demonstrably safer practitioners than those who do not."
)


def _fixture_version(db, brand, body: str) -> ContentVersion:
    campaign = content_agent.get_or_create_ad_hoc_campaign(db, brand)
    asset = ContentAsset(
        campaign_id=campaign.id,
        brand_id=brand.id,
        asset_type="social_post",
        platform="linkedin",
        title="brand rule regression fixture",
        status="draft",
        origin="test_fixture",
    )
    db.add(asset)
    db.flush()
    version = ContentVersion(
        content_asset_id=asset.id,
        version_number=1,
        body=body,
        status="draft",
        is_current=True,
    )
    db.add(version)
    db.flush()
    return version


def _run(db, slug: str, body: str):
    brand = db.query(Brand).filter_by(slug=slug).first()
    assert brand is not None, f"brand '{slug}' missing"
    version = _fixture_version(db, brand, body)
    review = compliance_agent.run_compliance_check(db, version)
    refs = {
        (i.get("policy_ref") or "")
        for i in (review.detected_issues or [])
        if i.get("policy_ref")
    }
    return review, refs


def test_doctorshield_rule_fires_for_doctorshield():
    db = SessionLocal()
    try:
        review, refs = _run(db, "doctorshield", DS_VIOLATION)
        print(f"  DoctorShield verdict: {review.outcome}")
        print(f"  policy_refs cited: {sorted(refs) or '(none)'}")

        assert review.outcome in ("fail", "needs_human_review"), (
            f"violating copy was not flagged at all (outcome={review.outcome})"
        )
        ds_refs = {r for r in refs if r.startswith("DS-")}
        assert ds_refs, (
            "no DoctorShield-specific rule was cited. The copy violates "
            f"DS-OUTCOME-01/DS-CLINICAL-01 but refs were: {sorted(refs)}"
        )
        print(f"PASS: DoctorShield rules fired -> {sorted(ds_refs)}")
        return ds_refs
    finally:
        db.close()


def test_doctorshield_rules_do_not_fire_for_jade():
    """Same copy, checked as Jade. Jade should never cite a DS- rule, because
    those rules are not in Jade's rule set at all."""
    db = SessionLocal()
    try:
        review, refs = _run(db, "jade", DS_VIOLATION)
        print(f"  Jade verdict: {review.outcome}")
        print(f"  policy_refs cited: {sorted(refs) or '(none)'}")

        leaked = {r for r in refs if r.startswith("DS-") or r.startswith("JT-")}
        assert not leaked, f"Jade content cited another brand's rules: {sorted(leaked)}"
        print("PASS: no DoctorShield/Jaguar rules cited on Jade content")
    finally:
        db.close()


if __name__ == "__main__":
    test_doctorshield_rule_fires_for_doctorshield()
    print()
    test_doctorshield_rules_do_not_fire_for_jade()
    print("\nPASS: brand-specific rules fire for their brand and not for others")
