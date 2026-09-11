"""Cursor cards get an honest artifacts÷turns headline when claim evidence is absent."""
from agentgrinder.metrics import headline_of


def test_cursor_harness_headline_uses_artifacts_not_fake_verified_zero():
    run = {
        "turns_typed": 6,
        "claims": 4,
        "claims_verified": None,
        "artifacts_produced": 9,
        "capabilities": {"timed_trace": False, "claim_evidence": False, "authorship": True},
        "reach": None,
        "corrections": None,
        "artifacts_promised": None,
    }
    hl = headline_of(run)
    assert hl.text == "1.50"
    assert hl.value == 1.5
    assert "claims evidence not in this harness" in hl.formula
    assert "9 artifacts" in hl.formula
    assert hl.five[1].value == "—/4"
    assert "tool stdout" in hl.five[1].source


def test_missing_artifacts_still_dashes_even_on_cursor():
    run = {
        "turns_typed": 6,
        "claims_verified": None,
        "artifacts_produced": None,
        "capabilities": {"claim_evidence": False},
    }
    hl = headline_of(run)
    assert hl.text == "—"
    assert hl.value is None
