"""The evidence side has two rules, and one of them carries almost all of the verified count.

The card's honesty number has two halves. The denominator, what counts as a claim, was measured on
3 September: precision 0.63, recall 0.66. The numerator, whether a claim was matched to the RIGHT
evidence, has no label set and both `claims.py` and the card tooltip say so.

`scripts/evidence-branch-report.py` does not close that gap, because closing it needs labelling.
It measures the size of it: which ARM of `evidence_matches` fires. That is a property of the code
path rather than a judgement, so it is readable straight off the corpus.

The measurement is only worth anything if the script's `branch_of` and the shipped
`evidence_matches` agree about whether a claim is verified at all. `branch_of` deliberately does
not call `evidence_matches`, because it has to see inside it. This file is what holds the two
together, so the reported split cannot drift away from the rule it is splitting.
"""
import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "evidence_branch_report", os.path.join(REPO, "scripts", "evidence-branch-report.py"))
ebr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ebr)

from agentgrinder.claims import claims_in, evidence_matches  # noqa: E402

# Every line here was written for this file. No transcript text appears in this repository.
CLAIM_LINES = [
    "Fixed tests/test_bucket.py and test_edges passes.",
    "Added the retry helper and the suite is green at 42 tests.",
    "Deployed the worker; the health check answers 200.",
    "I re-ran the suite after the rename and 128 tests passed.",
]
RESULT_SETS = [
    ["tests/test_bucket.py ..... 5 passed"],   # names the file the claim named
    ["42 passed in 1.2s"],                     # a passing token and nothing else
    ["Traceback (most recent call last)"],     # a passing token would be contradicted
    ["exit 0"],
    ["OK"],
    ["3 failed, 2 passed"],                    # contradicted
    [""],
    ["nothing relevant here"],
    ["test_edges PASSED", "exit 0"],           # token in one result, generic in another
    ["exit 0", "tests/test_bucket.py touched"],  # generic first, token second
]


def _claim(text):
    found = claims_in(text)
    assert found, f"the rule no longer reads this fixture as a claim: {text}"
    return found[0]


def test_the_split_agrees_with_the_rule_it_is_splitting():
    """A report that disagreed with the shipped rule would be measuring a different product."""
    for line in CLAIM_LINES:
        for results in RESULT_SETS:
            claim = _claim(line)
            reported = ebr.branch_of(claim, results) is not None
            shipped = any(evidence_matches(claim, r) for r in results)
            assert reported == shipped, (line, results, reported, shipped)


def test_all_three_outcomes_are_reachable():
    """A classifier nobody has seen return each of its values is not a classifier yet."""
    seen = set()
    for line in CLAIM_LINES:
        for results in RESULT_SETS:
            seen.add(ebr.branch_of(_claim(line), results))
    assert seen == {"token", "generic", None}, seen


def test_the_stronger_arm_wins_whichever_result_carries_it():
    """A claim is GENERIC-ONLY only when no result in the turn named it.

    Order matters here and it is easy to get wrong: `evidence_matches` returns on the first result
    that matches at all, so a naive port would report `generic` whenever the passing token happened
    to come first. The split has to look at the whole turn before deciding.
    """
    claim = _claim("Fixed tests/test_bucket.py and test_edges passes.")
    assert ebr.branch_of(claim, ["exit 0", "tests/test_bucket.py touched"]) == "token"
    assert ebr.branch_of(claim, ["tests/test_bucket.py touched", "exit 0"]) == "token"
    assert ebr.branch_of(claim, ["exit 0"]) == "generic"


def test_a_contradicted_result_does_not_verify():
    claim = _claim("Added the retry helper and the suite is green at 42 tests.")
    assert ebr.branch_of(claim, ["3 failed, 2 passed"]) is None
    assert ebr.branch_of(claim, ["Traceback (most recent call last)"]) is None


def test_a_claim_naming_nothing_can_only_ever_reach_the_weak_arm():
    """This is the ceiling the report prints, asserted rather than described.

    A claim line that names no test and no file has an empty token set, so the strong arm has
    nothing to match on and the only route to `verified` is the generic one. That is why the share
    is large: it is mostly a property of how people write claims, not of the matcher.
    """
    claim = _claim("Deployed the worker; the health check answers 200.")
    assert not claim.tokens
    assert ebr.branch_of(claim, ["tests/test_bucket.py ..... 5 passed"]) == "generic"
    assert ebr.branch_of(claim, ["nothing relevant here"]) is None


def test_the_report_runs_and_reports_nothing_rather_than_zero_on_an_empty_machine(monkeypatch,
                                                                                 capsys):
    monkeypatch.setattr(ebr.glob, "glob", lambda *a, **k: [])
    rc = ebr.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "nothing to split" in out
    assert "0.0%" not in out, "an empty corpus is being shown a percentage"
