#!/usr/bin/env python3
"""Recompute every published claim-rule figure from the committed counts.

The precision and recall on the site and in the README were first computed by a script that was
never committed. That is a number without a reproducible source, which is the one thing this
project refuses to ship. This file is that source, versioned.

It reads `docs/claim-calibration.json` and nothing else. No transcript, no label file, no machine
state. The counts in that file are the whole evidence base, so anyone can rerun this and get the
published figures back.

    python3 scripts/claim-calibration-report.py           # the table
    python3 scripts/claim-calibration-report.py --json     # the same numbers, machine readable

WHAT IT COMPUTES

Precision and recall are Horvitz-Thompson estimates. The corpus was stratified, and a labelled
line stands for every line in its cell, so each cell is weighted by pop/n. The intervals are 2.5
and 97.5 percentiles of a bootstrap that resamples labelled lines inside each cell with
replacement, holding n fixed.

WHY IT REPORTS PER HARNESS

The headline blends three harnesses by their share of one machine's corpus. Two of those shares
are lopsided: Claude Code carries 62.9 percent of the held-out population weight and Cursor
carries 34.9 percent, but Cursor is estimated from four predicted positives. A blended figure can
be honest and still hide a stratum that is not measured at all. The per-harness rows are here so
that stratum is visible rather than averaged away.

A draw where a harness produces no predicted positive has no precision. Those draws are dropped
and counted, and the count is printed, because silently dropping them narrows an interval.
"""
import argparse
import json
import os
import random
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = os.path.join(REPO, "docs", "claim-calibration.json")

# Fixed so the table is reproducible. It is a seed, not a measurement: rerun with any other seed
# and the point estimates are identical, the interval edges move by about 0.01.
SEED = 20260904
DRAWS = 2000
HARNESSES = ("claude", "codex", "cursor")

# THE FLOOR, and why there are two numbers in it.
#
# Precision is true positives over predicted positives. A stratum with four predicted positives
# has a precision whose bootstrap interval runs from 0.00 to 0.86, which is the whole useful
# range. Reporting a point estimate there publishes the absence of a measurement.
#
# A thin stratum only endangers the HEADLINE when it also carries weight. Codex is thin and
# carries 2.2 percent, so it moves the blend by almost nothing. Cursor is thin and carries 34.9
# percent, so a third of the published figure rests on four predicted positives. The first case is
# a footnote. The second case is a defect.
#
# So: every stratum under the count floor is named as unreportable, and the run FAILS only when
# such a stratum also sits above the weight floor.
FLOOR_PREDICTED_POSITIVES = 10
FLOOR_WEIGHT = 0.10


def _cells(cal, rule, split, harness=None):
    out = {}
    for key, cell in cal["cells"][rule].items():
        if not key.startswith(split + "|"):
            continue
        if harness is not None and not key.endswith("|" + harness):
            continue
        out[key] = cell
    return out


def _estimate(cells, draw):
    """One Horvitz-Thompson reading. `draw` turns a cell into its (tp, fp, fn) for this reading."""
    tp = fp = fn = 0.0
    for cell in cells.values():
        weight = cell["pop"] / cell["n"]
        cell_tp, cell_fp, cell_fn = draw(cell)
        tp += weight * cell_tp
        fp += weight * cell_fp
        fn += weight * cell_fn
    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    return precision, recall


def _as_labelled(cell):
    return cell["tp"], cell["fp"], cell["fn"]


def _resampler(rng):
    def draw(cell):
        bag = (["tp"] * cell["tp"] + ["fp"] * cell["fp"]
               + ["fn"] * cell["fn"] + ["tn"] * cell["tn"])
        drawn = [rng.choice(bag) for _ in range(len(bag))]
        return drawn.count("tp"), drawn.count("fp"), drawn.count("fn")
    return draw


def _percentile(sorted_values, fraction):
    return sorted_values[int(fraction * (len(sorted_values) - 1))]


def measure(cells, draws=DRAWS, seed=SEED):
    """Point estimates, intervals, raw counts and population for one set of cells."""
    precision, recall = _estimate(cells, _as_labelled)
    rng = random.Random(seed)
    precisions, recalls = [], []
    for _ in range(draws):
        draw = _resampler(rng)
        p, r = _estimate(cells, draw)
        if p is not None:
            precisions.append(p)
        if r is not None:
            recalls.append(r)
    precisions.sort()
    recalls.sort()
    result = {
        "precision": precision,
        "recall": recall,
        "tp": sum(c["tp"] for c in cells.values()),
        "fp": sum(c["fp"] for c in cells.values()),
        "fn": sum(c["fn"] for c in cells.values()),
        "tn": sum(c["tn"] for c in cells.values()),
        "labelled": sum(c["n"] for c in cells.values()),
        "population": sum(c["pop"] for c in cells.values()),
        "draws": draws,
        "precision_draws_defined": len(precisions),
        "recall_draws_defined": len(recalls),
    }
    if precisions:
        result["precision_lo"] = _percentile(precisions, 0.025)
        result["precision_hi"] = _percentile(precisions, 0.975)
    if recalls:
        result["recall_lo"] = _percentile(recalls, 0.025)
        result["recall_hi"] = _percentile(recalls, 0.975)
    return result


def report(cal=None, draws=DRAWS, seed=SEED):
    cal = cal or json.load(open(CAL))
    out = {"seed": seed, "draws": draws, "measured": cal["measured"],
           "rule_fingerprint": cal["rule_fingerprint"], "rules": {}}
    for rule in ("shipped", "v0"):
        rows = {"all": measure(_cells(cal, rule, "holdout"), draws, seed)}
        for harness in HARNESSES:
            rows[harness] = measure(_cells(cal, rule, "holdout", harness), draws, seed)
        out["rules"][rule] = rows
    for rule, rows in out["rules"].items():
        total = rows["all"]["population"]
        for harness in HARNESSES:
            rows[harness]["weight"] = rows[harness]["population"] / total
    return out


def _interval(row, key):
    lo, hi = row.get(key + "_lo"), row.get(key + "_hi")
    if lo is None:
        return "not defined"
    return "%.2f to %.2f" % (lo, hi)


def _print(out):
    for rule, title in (("shipped", "the rule shipping today, sentence level"),
                        ("v0", "v0, one vocabulary regex over the line")):
        print("\n%s  (held-out half, seed %d, %d draws)" % (title, out["seed"], out["draws"]))
        print("  %-9s %-6s %-16s %-6s %-16s %8s %10s %7s"
              % ("harness", "prec", "interval", "rec", "interval",
                 "labelled", "population", "weight"))
        for name in ("all",) + HARNESSES:
            row = out["rules"][rule][name]
            weight = "%.1f%%" % (100 * row["weight"]) if "weight" in row else "100.0%"
            print("  %-9s %-6.2f %-16s %-6.2f %-16s %8d %10d %7s"
                  % (name, row["precision"], _interval(row, "precision"),
                     row["recall"], _interval(row, "recall"),
                     row["labelled"], row["population"], weight))
        for name in ("all",) + HARNESSES:
            row = out["rules"][rule][name]
            dropped = row["draws"] - row["precision_draws_defined"]
            if dropped:
                print("    %s: %d of %d bootstrap draws produced no predicted positive, "
                      "so they carry no precision and were dropped."
                      % (name, dropped, row["draws"]))
        counts = out["rules"][rule]["cursor"]
        print("    cursor counts, as labelled: %d true positive, %d false positive, "
              "%d false negative, %d true negative, over %d lines standing for %d."
              % (counts["tp"], counts["fp"], counts["fn"], counts["tn"],
                 counts["labelled"], counts["population"]))


def audit(out):
    """Which strata are too thin to report, and which of those poison the headline.

    Returns (unreportable, fatal). `fatal` is what makes the run exit non-zero. A sentence in a
    document has to be re-read by somebody. A check goes red on its own.
    """
    unreportable, fatal = [], []
    for harness in HARNESSES:
        row = out["rules"]["shipped"][harness]
        predicted = row["tp"] + row["fp"]
        if predicted >= FLOOR_PREDICTED_POSITIVES:
            continue
        entry = {"harness": harness, "predicted_positives": predicted,
                 "floor": FLOOR_PREDICTED_POSITIVES, "weight": row["weight"],
                 "labelled": row["labelled"], "population": row["population"]}
        unreportable.append(entry)
        if row["weight"] >= FLOOR_WEIGHT:
            fatal.append(entry)
    return unreportable, fatal


def _print_audit(unreportable, fatal):
    print("\nthe floor: a stratum needs %d predicted positives before its precision is reportable,"
          % FLOOR_PREDICTED_POSITIVES)
    print("and a stratum under that floor carrying %.0f percent or more of the population weight"
          % (100 * FLOOR_WEIGHT))
    print("makes the headline unsafe.")
    if not unreportable:
        print("  every stratum is above the floor.")
    for entry in unreportable:
        verdict = "FAILS, it carries the headline" if entry in fatal else "noted, too small to move the headline"
        print("  %-8s %d predicted positives, %.1f percent of the weight, %d labelled lines "
              "standing for %d: %s"
              % (entry["harness"], entry["predicted_positives"], 100 * entry["weight"],
                 entry["labelled"], entry["population"], verdict))
    if fatal:
        print("\nFAIL: %s. The published precision cannot be called general while a stratum this "
              "size is unmeasured."
              % ", ".join("%s is under the floor at %d predicted positives while carrying %.1f "
                          "percent of the weight" % (e["harness"], e["predicted_positives"],
                                                     100 * e["weight"]) for e in fatal))
        print("     The fix is to state which population the headline describes. Note that the "
              "shipped card runs the claim rule on Claude Code transcripts only, so labelling more "
              "lines in a stratum the card does not score would sharpen a number nothing uses. "
              "Labelling becomes the fix if, and only if, that harness is wired into the rule; "
              "tests/test_claim_rule.py holds that seam and goes red on the day it happens.")
    else:
        print("\nPASS: no stratum under the floor carries enough weight to move the headline.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="print the numbers as JSON")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--draws", type=int, default=DRAWS)
    parser.add_argument("--no-check", action="store_true",
                        help="print the table and exit 0 even when a stratum is under the floor")
    args = parser.parse_args(argv)
    out = report(draws=args.draws, seed=args.seed)
    unreportable, fatal = audit(out)
    out["unreportable"] = unreportable
    out["fatal"] = fatal
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        _print(out)
        _print_audit(unreportable, fatal)
    return 1 if (fatal and not args.no_check) else 0


if __name__ == "__main__":
    sys.exit(main())
