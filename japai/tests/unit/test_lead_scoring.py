"""Pure-logic test for lead fit scoring — makes NO LLM calls and NO DB writes.

`score_lead` is a pure function of (profile dict, Brand), so this constructs an
in-memory Brand and never opens a session. Safe to run with the stack down.
"""
from dotenv import load_dotenv

load_dotenv()

from apps.api.agents.lead import (
    JADE_SEED_LEADS,
    QUALIFYING_SIGNALS,
    SCORE_CAP,
    W_CATEGORY,
    W_LOCATION,
    W_SIGNALS,
    W_SIZE,
    score_lead,
    score_location_match,
    score_size_fit,
)
from apps.api.models import Brand

JADE = Brand(
    name="Jade",
    slug="jade",
    target_audience="Independent jewellers, goldsmiths, and jewellery retailers in Singapore.",
)


def test_weights_sum_to_cap():
    total = W_CATEGORY + W_SIZE + W_LOCATION + W_SIGNALS
    assert total == SCORE_CAP, f"weights sum to {total}, expected {SCORE_CAP}"
    print(f"Weights OK: {W_CATEGORY}+{W_SIZE}+{W_LOCATION}+{W_SIGNALS} = {total}")


def test_breakdown_sums_to_score():
    """The number shown must be the sum of the parts shown — the Phase 5
    SUM_OK check, applied to leads."""
    for profile in JADE_SEED_LEADS:
        b = score_lead(profile, JADE)
        parts = sum(c["points"] for c in b["components"].values())
        assert abs(parts - b["raw_total"]) < 0.01, (
            f"{profile['company_name']}: parts {parts} != raw_total {b['raw_total']}"
        )
        assert b["score"] == min(round(b["raw_total"], 2), SCORE_CAP)
        assert b["score"] <= SCORE_CAP
        print(f"  SUM_OK {profile['company_name']:32s} {b['score']:6.2f}")
    print("Breakdown sums OK for all seed leads")


def test_size_fit_curve():
    assert score_size_fit(12)[0] == 1.0, "inside band -> 1.0"
    assert score_size_fit(5)[0] == 1.0, "lower edge inclusive"
    assert score_size_fit(50)[0] == 1.0, "upper edge inclusive"
    assert score_size_fit(None)[0] == 0.5, "unknown -> neutral, not zero"
    assert score_size_fit(180)[0] == 0.0, "far above band -> 0"
    assert 0.0 < score_size_fit(2)[0] < 1.0, "below band decays, not cliff"
    assert 0.0 < score_size_fit(80)[0] < 1.0, "just above band decays, not cliff"
    print("Size-fit curve OK (band, edges, unknown, decay)")


def test_location_discriminates():
    sg, _ = score_location_match("Orchard Road, Singapore")
    my, _ = score_location_match("Kuala Lumpur, Malaysia")
    assert sg == 1.0 and my == 0.0, f"expected 1.0/0.0, got {sg}/{my}"
    print("Location match OK (Singapore 1.0, Malaysia 0.0)")


def test_scoring_actually_discriminates():
    """A formula that rates everything ~equally is decoration. The seed set is
    built with deliberate weak fits, so the spread must be real."""
    scores = sorted((score_lead(p, JADE)["score"] for p in JADE_SEED_LEADS), reverse=True)
    spread = scores[0] - scores[-1]
    assert spread >= 20, f"scores too flat to be useful: spread {spread} ({scores})"
    print(f"Discrimination OK: top {scores[0]}, bottom {scores[-1]}, spread {spread:.2f}")


def test_signals_are_recognised():
    """Guards against a typo'd signal name silently scoring zero forever."""
    used = {s for p in JADE_SEED_LEADS for s in p["signals"]}
    unknown = used - set(QUALIFYING_SIGNALS)
    assert not unknown, f"seed data uses unrecognised signals: {sorted(unknown)}"
    print(f"Signals OK: {len(used)} distinct, all recognised")


def test_seed_data_is_labelled_synthetic():
    """Contact details must not be able to reach a real person or business."""
    for p in JADE_SEED_LEADS:
        assert ".example.com" in p["email"], f"{p['company_name']} has a non-example email"
    print(f"Contact safety OK: all {len(JADE_SEED_LEADS)} emails on example.com")


def run_all():
    test_weights_sum_to_cap()
    test_breakdown_sums_to_score()
    test_size_fit_curve()
    test_location_discriminates()
    test_scoring_actually_discriminates()
    test_signals_are_recognised()
    test_seed_data_is_labelled_synthetic()
    print("\nPASS: lead scoring")


if __name__ == "__main__":
    run_all()
