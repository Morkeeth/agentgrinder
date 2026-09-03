"""Verdict over a series of readings. Ported from MAGNET's reporter (itself from helicon).

Rules carried forward:
  - baseline when fewer than two MEASURED readings exist: a first reading is not a trend
  - helped / hurt only when two measured readings exist and the direction is known
  - unmeasured is NULL, never zero, and never counts
  - the comparison is this sitting against the sitting BEFORE it on the same project, by start
    time, so re-drawing an old sitting never compares it with a newer one
"""
from __future__ import annotations

from typing import Literal

Verdict = Literal["baseline", "helped", "hurt", "unchanged"]


def verdict(readings: list[dict], *, direction: str = "up", at: str | None = None) -> tuple[Verdict, float | None]:
    """Label the reading that started at `at` (default: the last) against the measured reading before it."""
    measured = [r for r in readings if r.get("value") is not None]
    if at is not None:
        measured = [r for r in measured if r["started"] <= at]
    if len(measured) < 2:
        return "baseline", None
    before, after = measured[-2]["value"], measured[-1]["value"]
    delta = round(after - before, 4)
    if delta == 0:
        return "unchanged", 0.0
    good = (direction == "up" and delta > 0) or (direction == "down" and delta < 0)
    return ("helped" if good else "hurt"), delta


def progress(readings: list[dict], run: dict, prediction: dict | None = None) -> dict:
    """The card's progress block for `run`, from the series it now belongs to."""
    label, delta = verdict(readings, at=run.get("started"))
    measured = [r for r in readings if r.get("value") is not None and r["started"] <= (run.get("started") or "")]
    prev = measured[-2] if len(measured) >= 2 else None
    return dict(
        verdict=label, delta=delta,
        value=(measured[-1]["value"] if measured else None),
        previous_value=(prev["value"] if prev else None),
        previous_started=(prev["started"] if prev else None),
        runs_on_project=len([r for r in readings if r["started"] <= (run.get("started") or "")]),
        prediction=(prediction or {}).get("text"),
    )


def progress_line(p: dict | None, project: str) -> str:
    """One sentence, in the card's voice. Every number in it is from the series."""
    if not p:
        return ""
    n = p.get("runs_on_project") or 0
    if p["verdict"] == "baseline":
        why = ("this is the first grind recorded on it" if n <= 1
               else "the previous grind had no headline to compare against")
        return f"baseline on {project}: {why}. Two measured grinds give a verdict."
    arrow = "up" if (p["delta"] or 0) > 0 else ("down" if (p["delta"] or 0) < 0 else "level")
    sign = "+" if (p["delta"] or 0) > 0 else ""
    when = (p.get("previous_started") or "")[:16].replace("T", " ")
    return (f"{p['verdict']} vs your last grind on {project}: verified per turn {arrow} "
            f"{sign}{p['delta']:.2f} ({p['previous_value']:.2f} -> {p['value']:.2f}), "
            f"previous {when}, {n} grinds on this project.")
