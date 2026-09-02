"""The headline is verified-per-turn, prompts are a cost. Math + the v0 claim rule.

Written 2026-09-02 after the metric finding (fleet-ops/METRICS-AGENTIC-ENGINEERING-2026-09-02.md):
a card that headlines "47 prompts" celebrates the METR failure. These tests pin the flip.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentgrinder.claims import ClaimTracker, claims_in, evidence_matches
from agentgrinder.ingest import parse_session
from agentgrinder.metrics import build_activity, verified_per_turn
from agentgrinder.render import render_card


def test_headline_math():
    assert verified_per_turn(6, 4, 47) == (6 + 4) / 47
    assert abs(verified_per_turn(6, 4, 47) - 0.2127659) < 1e-6


def test_headline_never_fabricated_from_missing_parts():
    # a missing numerator defaulted to 0 would print a low score nobody measured
    assert verified_per_turn(None, 4, 47) is None
    assert verified_per_turn(6, None, 47) is None
    assert verified_per_turn(6, 4, None) is None
    assert verified_per_turn(6, 4, 0) is None


def test_activity_headline_and_five_row():
    run = {"turns_typed": 47, "duration_s": 8400, "claims": 9, "claims_verified": 6,
           "artifacts_produced": 4, "artifacts_promised": None, "corrections": None, "reach": None}
    a = build_activity(run)
    assert a.headline == "0.21"
    assert a.headline_formula == "(6 verified + 4 artifacts) ÷ 47 typed turns"
    labels = [c.label for c in a.five]
    assert labels == ["typed turns", "verified claims", "correction rate", "produced ÷ promised", "reach"]
    typed, share, corr, prod, reach = a.five
    assert typed.value == "47" and typed.cost is True          # prompts are the cost
    assert share.value == "6/9 · 67%"
    assert corr.value == "—" and "Transcripto" in corr.source   # the dash names its owner
    assert prod.value == "4 ÷ —" and "ZUP" in prod.source
    assert reach.value == "—" and "gh" in reach.source
    # the Strava-shaped numbers survive, under cost
    assert a.distance == "47 prompts"


def test_activity_with_no_five_numbers_prints_dashes():
    a = build_activity({"turns_typed": 12, "duration_s": 600})
    assert a.headline == "—"
    assert "verified claims" in a.headline_formula
    assert [c.value for c in a.five] == ["12", "—", "—", "— ÷ —", "—"]


def test_card_headlines_verified_per_turn_not_prompts():
    run = json.load(open(os.path.join(os.path.dirname(__file__), "..", "samples", "sample_run.json")))
    html = render_card(build_activity(run))
    assert '<div class="n">0.21</div>' in html
    assert "verified per turn" in html
    # prompts are still on the card, but grouped as cost, never as Distance
    assert ">Distance<" not in html
    assert "Cost — what the run spent" in html
    assert "47 prompts" in html
    # every dash carries a tooltip naming a source
    assert 'title="Transcripto export-run' in html and "ZUP" in html and "Helicon witness" in html


# ---- the v0 claim rule ----------------------------------------------------------------

def test_claim_lines_and_tokens():
    cl = claims_in("Ran the suite.\ntests/test_x.py passes — test_alpha green\nno claim here\n")
    assert len(cl) == 1
    assert "test_alpha" in cl[0].tokens and "tests/test_x.py" in cl[0].tokens


def test_evidence_generic_token_rejected_when_result_also_fails():
    c = claims_in("all tests pass, done")[0]
    assert evidence_matches(c, "3 passed in 0.1s")
    assert not evidence_matches(c, "2 passed, 1 failed")
    assert not evidence_matches(c, "some listing with nothing")


def test_tracker_window_is_the_human_turn_either_side():
    t = ClaimTracker()
    t.typed_turn()
    t.tool_result("4 passed in 0.2s")           # evidence BEFORE the claim (the common shape)
    t.assistant_text("tests pass, fixed.")
    t.typed_turn()                              # new human turn: the next claim cannot borrow that evidence
    t.assistant_text("deployed and works")
    t.close()
    assert (t.claims, t.verified) == (2, 1)


def _rec(typ, content, **kw):
    o = {"type": typ, "timestamp": kw.pop("ts", "2026-09-02T10:00:00Z"), "message": {"role": typ, "content": content}}
    o.update(kw)
    return o


def test_parse_session_counts_claims_and_produced(tmp_path):
    made = tmp_path / "out.md"; made.write_text("x")
    lines = [
        _rec("user", "please fix it", ts="2026-09-02T10:00:00Z", cwd=str(tmp_path), promptSource="typed"),
        _rec("assistant", [{"type": "tool_use", "name": "Write", "input": {"file_path": str(made)}},
                           {"type": "tool_use", "name": "Write", "input": {"file_path": str(tmp_path / "never.md")}}],
             ts="2026-09-02T10:00:10Z"),
        _rec("user", [{"type": "tool_result", "content": "5 passed in 0.3s"}], ts="2026-09-02T10:00:20Z"),
        _rec("assistant", [{"type": "text", "text": "Suite passes. Also the deploy is done."}], ts="2026-09-02T10:00:30Z"),
        _rec("user", "thanks, now the other thing", ts="2026-09-02T10:05:00Z", promptSource="typed"),
        _rec("assistant", [{"type": "text", "text": "Fixed it."}], ts="2026-09-02T10:05:10Z"),
    ]
    p = tmp_path / "s.jsonl"
    p.write_text("\n".join(json.dumps(x) for x in lines) + "\n")
    r = parse_session(str(p))
    assert r["turns_typed"] == 2
    # one claim per LINE ("passes ... done" is one line); 'Fixed it.' has no evidence in its turn
    assert (r["claims"], r["claims_verified"]) == (2, 1)
    assert r["artifacts_produced"] == 1                    # never.md was not written to disk
    assert r["artifacts_promised"] is None and r["corrections"] is None and r["reach"] is None
    a = build_activity(r)
    assert a.headline == f"{(1 + 1) / 2:.2f}"
