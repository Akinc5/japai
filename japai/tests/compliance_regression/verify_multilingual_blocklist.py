"""Proves the blocklist is language-aware — costs ZERO LLM calls.

The failure this guards against is specific and severe: before this phase,
step 1 scanned only the 16 English phrases. A Chinese asset saying 保证赔付
("guaranteed payout") contains no English substring, so it sailed through step 1
and the whole deterministic safety net was silently inert for localized content.

Each fixture below is a forbidden-equivalent phrase in its own language,
constructed the same way Phase 3's English fixtures were. Every one must block
under its own language, and the cross-language checks confirm the lists are
actually being selected by language rather than all concatenated together.
"""
from dotenv import load_dotenv

load_dotenv()

from apps.api.agents import compliance as compliance_agent
from apps.api.agents import content as content_agent
from apps.api.agents import localization as localization_agent
from apps.api.core.db import SessionLocal
from apps.api.models import Brand, ContentAsset, ContentVersion

# (language, body, the term that must be caught)
FIXTURES = [
    ("zh-Hans", "投保捷德珠宝保险，我们保证赔付每一宗索赔，零风险。", "保证赔付"),
    ("zh-Hans", "您的库存将获得100%保障，绝对安全。", "100%保障"),
    ("ms", "Dengan Jade, tuntutan anda pasti dibayar dan perniagaan anda bebas risiko.", "pasti dibayar"),
    ("ms", "Stok anda dilindungi sepenuhnya, tiada pengecualian.", "dilindungi sepenuhnya"),
    ("id", "Bersama Jade, klaim Anda dijamin dibayar tanpa pengecualian.", "dijamin dibayar"),
    ("id", "Inventaris Anda 100% ditanggung dan bebas risiko.", "100% ditanggung"),
    ("en", "Your stock is guaranteed payout with no exceptions.", "guaranteed payout"),
]


def test_each_language_blocklist_catches_its_own():
    """Pure function test — no DB, no LLM."""
    failures = []
    for language, body, expected in FIXTURES:
        issues = compliance_agent._scan_blocklist(body, language)
        terms = {i["term"] for i in issues}
        if expected not in terms:
            failures.append(f"{language}: '{expected}' NOT caught (got {sorted(terms)})")
        else:
            print(f"  [OK] {language:8s} caught '{expected}'")
    assert not failures, "blocklist misses:\n  " + "\n  ".join(failures)
    print("PASS: every language's blocklist catches its own forbidden phrase")


def test_english_scan_is_blind_to_other_languages():
    """The regression this phase exists to prevent: scanning non-English copy
    with the English list must find nothing, proving language selection is what
    makes the catch (and that the old behaviour really was inert)."""
    for language, body, expected in FIXTURES:
        if language == "en":
            continue
        english_only = compliance_agent._scan_blocklist(body, "en")
        assert not english_only, (
            f"unexpected: English list matched {language} copy: {english_only}"
        )
    print("PASS: English list alone finds nothing in zh-Hans/ms/id copy (as expected)")


def test_language_lists_are_not_merged():
    """Malay and Indonesian share some vocabulary, but a term unique to one must
    not be caught under the other — otherwise the lists are being concatenated
    rather than selected."""
    ms_only = "Stok anda dilindungi sepenuhnya."      # ms phrasing
    id_only = "Inventaris Anda ditanggung sepenuhnya."  # id phrasing

    assert compliance_agent._scan_blocklist(ms_only, "ms"), "ms term not caught under ms"
    assert not compliance_agent._scan_blocklist(ms_only, "id"), "ms-only term leaked into id list"
    assert compliance_agent._scan_blocklist(id_only, "id"), "id term not caught under id"
    assert not compliance_agent._scan_blocklist(id_only, "ms"), "id-only term leaked into ms list"
    print("PASS: Malay and Indonesian lists are selected separately, not merged")


def test_unknown_language_does_not_fall_back_to_english():
    """A language we have no list for must return [] rather than silently
    applying the English list to text it cannot match."""
    assert localization_agent.blocklist_for_language("ta") == []
    print("PASS: unknown language yields an empty list, not a false-confidence English scan")


def test_end_to_end_block_through_real_pipeline():
    """Runs a Chinese fixture through the actual run_compliance_check, proving
    the language reaches step 1 from content_assets.language. The blocklist hit
    short-circuits steps 2-4, so this still costs ZERO LLM calls."""
    db = SessionLocal()
    try:
        brand = db.query(Brand).filter_by(slug="jade").first()
        assert brand is not None, "Jade missing — run seed_brands"
        campaign = content_agent.get_or_create_ad_hoc_campaign(db, brand)

        asset = ContentAsset(
            campaign_id=campaign.id,
            brand_id=brand.id,
            asset_type="social_post",
            platform="linkedin",
            title="multilingual blocklist fixture",
            status="draft",
            origin="test_fixture",
            language="zh-Hans",
        )
        db.add(asset)
        db.flush()

        version = ContentVersion(
            content_asset_id=asset.id,
            version_number=1,
            body="投保捷德珠宝保险，我们保证赔付每一宗索赔，零风险。",
            status="draft",
            is_current=True,
        )
        db.add(version)
        db.flush()

        review = compliance_agent.run_compliance_check(db, version)
        terms = {i["term"] for i in (review.detected_issues or [])}

        assert review.outcome == "fail", f"expected fail, got {review.outcome}"
        assert version.status == "rejected", f"expected rejected, got {version.status}"
        assert "保证赔付" in terms, f"expected 保证赔付 in {sorted(terms)}"
        assert "零风险" in terms, f"expected 零风险 in {sorted(terms)}"
        print(f"  pipeline verdict: {review.outcome}, status {version.status}")
        print(f"  terms caught: {sorted(terms)}")
        print("PASS: language reaches step 1 through the real pipeline (0 LLM calls)")
    finally:
        db.close()


if __name__ == "__main__":
    test_each_language_blocklist_catches_its_own()
    print()
    test_english_scan_is_blind_to_other_languages()
    test_language_lists_are_not_merged()
    test_unknown_language_does_not_fall_back_to_english()
    print()
    test_end_to_end_block_through_real_pipeline()
    print("\nPASS: multilingual blocklist")
