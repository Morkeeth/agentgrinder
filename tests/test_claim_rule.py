"""The claim rule, pinned by fixtures and by its own published error rate.

Three things are held here, and the third is the point:

1. the rule behaves as the rubric says, on SYNTHETIC lines written for this file;
2. the precision and recall printed in the docs are the numbers that fall out of the counts
   committed beside them, so a figure cannot drift away from its evidence;
3. the rule's own text is digested, and the digest is stored with those numbers. Edit the rule and
   this suite goes red until the calibration is redone. A measured claim about an instrument stops
   being true the moment somebody edits the instrument.

No line from any real transcript appears in this repository. The label set is local to the machine
it was drawn on.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentgrinder.claims import claims_in, is_claim_line, rule_fingerprint

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = os.path.join(REPO, "docs", "claim-calibration.json")
DOC = os.path.join(REPO, "docs", "CLAIM-RULE-CALIBRATION-2026-09-03.md")
PAGE = os.path.join(REPO, "site", "methodology.html")

# ---- 1. the rubric, as fixtures. Every line below was written for this test. ----------------

CLAIMS = [
    "Fixed the off-by-one in the date bucket, and the failing case passes now.",   # repaired state
    "Added the retry helper to the queue worker and the suite is green at 42 tests.",  # action done
    "Deployed the worker to staging; the health check answers 200.",               # action done
    "I re-ran the suite after the rename and 128 tests passed.",                   # check outcome
    "- Lint: passed",                                                             # check outcome
    "Pushed to the release branch at 1a2b3c4.",                                   # action done
]

NOT_CLAIMS = [
    "## What is done",                                    # a heading carrying a completion word
    "| status | done |",                                  # a table row
    "Two things I fixed tonight:",                        # a label that introduces a list
    "Should I mark the migration as done?",               # a question
    "Next I will run the migration and check that it passes.",   # a plan
    "If the suite passes, we ship it tomorrow.",          # a condition
    "Make sure the build is green before you tag it.",    # advice
    "> the suite passed on their machine",                # quoted, and someone else's run
    "The retry helper works by doubling the delay after each failure.",  # how a thing behaves
]


def test_every_rubric_claim_is_read_as_one():
    missed = [s for s in CLAIMS if not is_claim_line(s)]
    assert missed == [], f"the rule no longer reads these as claims: {missed}"


def test_no_rubric_non_claim_is_read_as_a_claim():
    wrong = [s for s in NOT_CLAIMS if is_claim_line(s)]
    assert wrong == [], f"the rule now reads these as claims: {wrong}"


def test_claims_in_keeps_the_line_and_its_tokens():
    cl = claims_in("Fixed tests/test_bucket.py; test_edges passes.\njust thinking out loud\n")
    assert len(cl) == 1
    assert "tests/test_bucket.py" in cl[0].tokens and "test_edges" in cl[0].tokens


# ---- 2. the published figures are recomputed from the committed counts ----------------------

def _weighted(cells, split):
    """Horvitz-Thompson precision and recall: every labelled line stands for its whole cell."""
    tp = fp = fn = 0.0
    for key, c in cells.items():
        if not key.startswith(split + "|"):
            continue
        w = c["pop"] / c["n"]
        tp += w * c["tp"]
        fp += w * c["fp"]
        fn += w * c["fn"]
    return tp / (tp + fp), tp / (tp + fn)


def test_the_docs_print_the_precision_the_counts_produce():
    cal = json.load(open(CAL))
    p_new, r_new = _weighted(cal["cells"]["shipped"], "holdout")
    p_old, r_old = _weighted(cal["cells"]["v0"], "holdout")
    assert round(p_new, 2) == 0.63 and round(r_new, 2) == 0.66
    assert round(p_old, 2) == 0.32 and round(r_old, 2) == 0.37
    doc, page = open(DOC).read(), open(PAGE).read()
    for text, where in ((doc, "the calibration write-up"), (page, "the methodology page")):
        for n in ("0.63", "0.66", "0.32", "0.37"):
            assert n in text, f"{where} no longer prints {n}"


def test_the_held_out_half_is_the_one_reported():
    cal = json.load(open(CAL))
    held = {k: c for k, c in cal["cells"]["shipped"].items() if k.startswith("holdout|")}
    assert sum(c["n"] for c in held.values()) == 198
    assert cal["labelled_lines"] == 396
    # the tuning half exists and is not the number on the page
    p_train, _ = _weighted(cal["cells"]["shipped"], "train")
    assert round(p_train, 2) > round(_weighted(cal["cells"]["shipped"], "holdout")[0], 2)


# ---- 3. the rule cannot move without the numbers moving -------------------------------------

def test_the_rule_matches_the_calibration_it_publishes():
    cal = json.load(open(CAL))
    assert cal["rule_fingerprint"] == rule_fingerprint(), (
        "the claim rule changed since it was calibrated. Re-run the calibration on the labelled "
        "set, update docs/claim-calibration.json and the two pages that print its numbers, then "
        "store the new fingerprint. A published precision belongs to one exact rule.")


def test_the_docs_carry_the_same_fingerprint():
    fp = json.load(open(CAL))["rule_fingerprint"]
    assert re.fullmatch(r"[0-9a-f]{16}", fp)
    assert fp in open(DOC).read() and fp in open(PAGE).read()
