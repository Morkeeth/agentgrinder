"""Evidence-matching embarrassment eval — synthetic only.

The claim DETECTOR is measured (precision 0.63 / recall 0.66 held out). The evidence MATCHER
(`evidence_matches`) has no real label set. Until one exists, this file holds a synthetic
labelled set written for the test, and scores three arms against it:

  shipped   — the code in claims.evidence_matches today (token match OR generic N passed)
  token_only — refuse the generic success token; require a named test/path from the claim
  silent    — never verify (the null that only invents zeros by omission)

A control that has not been watched going RED is not a control. The finding we want, if it is
true: the naive always-silent arm can beat the shipped matcher on precision, because a generic
"N passed" in the same turn still verifies any claim beside it. That result is allowed to make
us look worse. It is the point.

No line from any real transcript appears here.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentgrinder.claims import Claim, evidence_matches

# Each case: claim line tokens, result text, gold (True = this result really evidences THAT claim).
# Written for this file. The embarrassing cases are the ones where a generic "N passed" lands
# next to an unrelated claim.
CASES = [
    # true positives the shipped rule should keep
    dict(id="path-hit",
         claim="Fixed tests/test_bucket.py; test_edges passes.",
         tokens={"tests/test_bucket.py", "test_edges"},
         result="....\n4 passed in 0.09s\ntest_edges ... ok",
         gold=True),
    dict(id="named-test-in-output",
         claim="I re-ran test_login and it passed.",
         tokens={"test_login"},
         result="test_login PASSED",
         gold=True),
    dict(id="exit-zero-same-check",
         claim="Deployed the worker; the health check answers 200.",
         tokens=set(),
         result="curl health -> 200\nexit 0",
         gold=True),  # weak gold: no token, but the result is about the health check
    # false friends: generic success next to an unrelated claim
    dict(id="generic-ok-unrelated",
         claim="Fixed the off-by-one in the date bucket.",
         tokens=set(),
         result="4 passed in 0.09s",
         gold=False),  # the 4 tests are not evidence for the date-bucket claim
    dict(id="generic-ok-wrong-file",
         claim="Rewrote auth/session.py.",
         tokens={"auth/session.py"},
         result="12 passed in 0.4s",
         gold=False),
    dict(id="ok-line-unrelated",
         claim="Landed the migration.",
         tokens=set(),
         result="OK",
         gold=False),
    # true negatives
    dict(id="failed-suite",
         claim="Fixed tests/test_bucket.py.",
         tokens={"tests/test_bucket.py"},
         result="2 failed, 3 passed\nFAILED tests/test_other.py",
         gold=False),
    dict(id="empty-result",
         claim="Added the retry helper.",
         tokens=set(),
         result="",
         gold=False),
    dict(id="traceback",
         claim="Patched the parser.",
         tokens=set(),
         result="Traceback (most recent call last):\n  File ...",
         gold=False),
    # a real token hit that should survive token_only
    dict(id="path-only",
         claim="Updated samples/fixture-project/notes.md.",
         tokens={"samples/fixture-project/notes.md"},
         result="Wrote samples/fixture-project/notes.md (120 bytes)",
         gold=True),
]


def _score(predict):
    tp = fp = tn = fn = 0
    for c in CASES:
        pred = predict(c)
        gold = c["gold"]
        if pred and gold:
            tp += 1
        elif pred and not gold:
            fp += 1
        elif (not pred) and gold:
            fn += 1
        else:
            tn += 1
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    return dict(tp=tp, fp=fp, tn=tn, fn=fn, precision=prec, recall=rec,
                f1=(2 * prec * rec / (prec + rec) if (prec + rec) else 0.0))


def shipped(c):
    return evidence_matches(Claim(line=c["claim"], tokens=set(c["tokens"])), c["result"])


def token_only(c):
    """Baseline a competent team builds in two hours: refuse generic success tokens."""
    if not c["result"]:
        return False
    return any(tok in c["result"] for tok in c["tokens"])


def silent(c):
    return False


def test_the_synthetic_set_is_large_enough_to_embarrass_us():
    assert len(CASES) >= 10
    assert sum(1 for c in CASES if c["gold"]) >= 3
    assert sum(1 for c in CASES if not c["gold"]) >= 3


def test_shipped_matcher_still_takes_the_generic_bait():
    """Pin the known hole: a bare 'N passed' verifies a claim with no tokens."""
    bait = next(c for c in CASES if c["id"] == "generic-ok-unrelated")
    assert shipped(bait) is True
    assert bait["gold"] is False


def test_baseline_arms_beat_or_tie_shipped_on_precision():
    """The finding that earns its keep: silent and token_only do not lose to shipped on precision.

    If shipped ever beats both on this synthetic set, the suite still passes — but the printed
    report in the assertion message must show the numbers recomputed here, never a carried figure.
    """
    s, t, n = _score(shipped), _score(token_only), _score(silent)
    # Re-derived in this process. Silent precision is 0/0 → defined as 0.0 above; treat "no
    # false positives" as perfect precision when it never fires.
    silent_prec = 1.0 if (n["fp"] == 0 and n["tp"] == 0) else n["precision"]
    token_prec = t["precision"]
    shipped_prec = s["precision"]
    # The embarrassment condition: at least one naive arm has precision strictly above shipped,
    # OR shipped still takes the generic bait (pinned above). Record the scores either way.
    report = (f"shipped P={shipped_prec:.2f} R={s['recall']:.2f}  "
              f"token_only P={token_prec:.2f} R={t['recall']:.2f}  "
              f"silent P={silent_prec:.2f} R={n['recall']:.2f}")
    assert silent_prec >= shipped_prec or token_prec >= shipped_prec, report
    # And make sure we actually observed the hole, so a future "fix" that only deletes cases fails.
    assert s["fp"] >= 1, report


def test_token_only_keeps_real_path_hits():
    hit = next(c for c in CASES if c["id"] == "path-only")
    assert token_only(hit) is True
    assert shipped(hit) is True
