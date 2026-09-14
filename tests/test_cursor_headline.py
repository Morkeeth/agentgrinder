"""Cursor cards get an honest artifacts÷turns headline when claim evidence is absent."""
from agentgrinder.metrics import headline_of


def test_cursor_harness_headline_is_artifacts_per_turn_not_verified():
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
    assert hl.metric_id == "artifacts_per_turn"
    assert hl.label == "artifacts per turn"
    assert "9 artifacts ÷ 6 typed turns" == hl.formula
    assert "verified" not in hl.label
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
    assert hl.label == "verified per turn"
