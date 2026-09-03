#!/usr/bin/env python3
"""Re-derive the published claim-rule precision/recall from the committed counts.

Never prints a figure that is not computed from docs/claim-calibration.json in this process.
Compares the shipped rule arm against the v0 vocabulary-regex arm (the naive baseline any
competent team ships in an afternoon). Exit 1 if the docs no longer match the counts.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAL = REPO / "docs" / "claim-calibration.json"
DOC = REPO / "docs" / "CLAIM-RULE-CALIBRATION-2026-09-03.md"
PAGE = REPO / "site" / "methodology.html"


def weighted(cells: dict, split: str) -> tuple[float, float]:
    tp = fp = fn = 0.0
    for key, c in cells.items():
        if not key.startswith(split + "|"):
            continue
        w = c["pop"] / c["n"]
        tp += w * c["tp"]
        fp += w * c["fp"]
        fn += w * c["fn"]
    return tp / (tp + fp), tp / (tp + fn)


def bootstrap_ci(cells: dict, split: str, n: int = 2000, seed: int = 0):
    rng = random.Random(seed)
    keys = [k for k in cells if k.startswith(split + "|")]
    ps, rs = [], []
    for _ in range(n):
        tp = fp = fn = 0.0
        for k in keys:
            c = cells[k]
            labels = (["tp"] * c["tp"] + ["fp"] * c["fp"] +
                      ["fn"] * c["fn"] + ["tn"] * c["tn"])
            if not labels:
                continue
            draw = [rng.choice(labels) for _ in range(c["n"])]
            w = c["pop"] / c["n"]
            tp += w * draw.count("tp")
            fp += w * draw.count("fp")
            fn += w * draw.count("fn")
        if tp + fp:
            ps.append(tp / (tp + fp))
        if tp + fn:
            rs.append(tp / (tp + fn))
    ps.sort()
    rs.sort()
    return (ps[int(0.025 * len(ps))], ps[int(0.975 * len(ps)) - 1],
            rs[int(0.025 * len(rs))], rs[int(0.975 * len(rs)) - 1])


def unweighted(cells: dict, split: str):
    fired = right = wrong = miss = 0
    for key, c in cells.items():
        if not key.startswith(split + "|"):
            continue
        fired += c["tp"] + c["fp"]
        right += c["tp"]
        wrong += c["fp"]
        miss += c["fn"]
    return fired, right, wrong, miss


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-docs", action="store_true",
                    help="fail if docs/methodology no longer print the recomputed rounded figures")
    args = ap.parse_args()

    cal = json.loads(CAL.read_text(encoding="utf-8"))
    print(f"rule_fingerprint (committed): {cal['rule_fingerprint']}")
    print(f"labelled_lines: {cal['labelled_lines']}  sittings_scanned: {cal.get('sittings_scanned')}")
    print()
    print(f"{'arm':<10} {'P':>6} {'R':>6} {'F1':>6}  P95              R95")
    rows = {}
    for arm in ("shipped", "v0"):
        p, r = weighted(cal["cells"][arm], "holdout")
        lo_p, hi_p, lo_r, hi_r = bootstrap_ci(cal["cells"][arm], "holdout")
        f1 = 2 * p * r / (p + r) if (p + r) else 0.0
        rows[arm] = (p, r, f1)
        print(f"{arm:<10} {p:6.2f} {r:6.2f} {f1:6.2f}  "
              f"[{lo_p:.2f},{hi_p:.2f}]     [{lo_r:.2f},{hi_r:.2f}]")
        fired, right, wrong, miss = unweighted(cal["cells"][arm], "holdout")
        print(f"           unweighted holdout: fired={fired} right={right} wrong={wrong} miss={miss}")

    print()
    sp, sr, _ = rows["shipped"]
    vp, vr, _ = rows["v0"]
    print(f"lift vs v0 baseline: precision {sp/vp:.2f}x · recall {sr/vr:.2f}x")
    print("Target was held-out precision > 0.8. "
          f"{'REACHED' if sp > 0.8 else 'NOT REACHED'} (point estimate "
          f"{round(sp, 2)}).")

    if args.check_docs:
        surfaces = {
            "calibration write-up": DOC.read_text(encoding="utf-8"),
            "methodology page": PAGE.read_text(encoding="utf-8"),
            "claims.py docstring": (REPO / "agentgrinder" / "claims.py").read_text(encoding="utf-8"),
            "README": (REPO / "README.md").read_text(encoding="utf-8"),
        }
        need = {
            "0.63": round(sp, 2),
            "0.66": round(sr, 2),
            "0.32": round(vp, 2),
            "0.37": round(vr, 2),
        }
        bad = []
        for where, text in surfaces.items():
            for label, val in need.items():
                # the printed string must equal the recomputed rounded figure
                if label != f"{val:.2f}":
                    bad.append(f"internal: expected key {label} == {val:.2f}")
                if label not in text:
                    bad.append(f"{where} missing {label}")
            if cal["rule_fingerprint"] not in text and where in (
                    "calibration write-up", "methodology page"):
                bad.append(f"{where} missing fingerprint")
        if bad:
            print("DOC CHECK FAILED:")
            for b in bad:
                print(" ", b)
            return 1
        print("DOC CHECK: every surface prints the recomputed rounded figures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
