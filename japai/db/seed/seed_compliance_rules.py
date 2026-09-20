from dotenv import load_dotenv

load_dotenv()

from apps.api.core.db import SessionLocal
from apps.api.models import ComplianceRule

RULES = [
    {
        "rule_code": "MAS-ADV-01",
        "category": "regulatory",
        "severity": "high",
        "description": (
            "Must not state or imply guaranteed claim approval, payout amount, or payout "
            "timeline — all claims are subject to policy terms, exclusions, and assessment."
        ),
    },
    {
        "rule_code": "MAS-ADV-02",
        "category": "disclosure",
        "severity": "medium",
        "description": (
            "Any statement about coverage scope must not omit that cover is subject to the "
            "policy schedule, exclusions, and underwriting terms."
        ),
    },
    {
        "rule_code": "CLAIM-SUBST-01",
        "category": "claims",
        "severity": "high",
        "description": (
            "Factual claims about what is covered must be substantiated by an approved brand "
            "knowledge source; unsupported coverage claims are not permitted."
        ),
    },
    {
        "rule_code": "COMPARE-01",
        "category": "brand_safety",
        "severity": "medium",
        "description": (
            "Do not make direct comparisons to named competitor insurers or disparage other "
            "insurers' products."
        ),
    },
    {
        "rule_code": "PRESSURE-01",
        "category": "brand_safety",
        "severity": "low",
        "description": (
            "Avoid high-pressure sales language (e.g. 'act now', 'limited time') that could "
            "induce a hasty decision on a regulated financial product."
        ),
    },
    {
        "rule_code": "SUPERLATIVE-01",
        "category": "claims",
        "severity": "medium",
        "description": (
            "Avoid unsubstantiated superlatives ('the best', 'the only', '#1') without an "
            "objective, verifiable basis."
        ),
    },
]


def run() -> None:
    db = SessionLocal()
    try:
        for rule_data in RULES:
            rule = db.query(ComplianceRule).filter_by(rule_code=rule_data["rule_code"]).first()
            if rule is None:
                db.add(ComplianceRule(brand_id=None, **rule_data))
                print(f"Created compliance rule: {rule_data['rule_code']}")
            else:
                print(f"Compliance rule already exists, skipping: {rule_data['rule_code']}")
        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
