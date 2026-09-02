"""Map a coding-agent session to an athletic 'run'. Every metric traces to the session log.

A 'run' JSON (see samples/) carries only counts read from a real session:
  athlete, title, harness, project, started (ISO), duration_s,
  turns_typed, tool_calls, files_touched, commits,
  rhythm  -> typed turns per time bucket (the 'route')
and, optionally, the five numbers of a run (fleet-ops/METRICS-AGENTIC-ENGINEERING-2026-09-02.md):
  claims, claims_verified        -> verified-claims share (v0 rule in ingest.py; Helicon witness later)
  corrections                    -> correction rate (Transcripto; not computed here yet)
  artifacts_produced, artifacts_promised -> produced ÷ promised (promised needs ZUP)
  reach                          -> 0/1: did the output cross to a person who is not the author

THE HEADLINE is verified-per-turn = (claims_verified + artifacts_produced) ÷ turns_typed.
Typed turns are a COST (the denominator), never the achievement. A card that headlines
"47 prompts" celebrates the person who talked the most (METR 2025: developers believed
they were 20% faster and measured 19% slower). Distance = verified output; prompts = cost.

We never invent a number. If a field is missing, the derived stat is None and the card
shows a dash, not a guess (Constitution rule 3). A dash carries a tooltip naming the
tool that owns that number (SOURCES below).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


def _fmt_dur(s: int | None) -> str:
    if not s:
        return "—"
    h, rem = divmod(int(s), 3600)
    m, sec = divmod(rem, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m {sec:02d}s"


def _fmt_pace(sec_per: float | None) -> str:
    if not sec_per:
        return "—"
    m, s = divmod(int(round(sec_per)), 60)
    return f"{m}:{s:02d} /prompt"


# Who owns each of the five numbers when this repo cannot compute it alone. The tooltip on a
# dash names the source, so a "—" is a pointer, never a shrug.
SOURCES = {
    "typed_turns": "Transcripto export-run (authorship.py, vendored: typed OR queued, drops isMeta/isSidechain/tool_result)",
    "verified_share": "Helicon witness (claim-witness log); local v0 = claims.py rule, which OVER-COUNTS (a ceiling)",
    "correction_rate": "Transcripto export-run (coach classifier, inverse class — not built yet)",
    "produced_over_promised": "produced = Edit/Write paths that exist at close (local v0); promised = ZUP artifact-detect",
    "reach": "git remotes + gh + the launch log — did the output cross to a person who is not the author",
}


def verified_per_turn(verified_claims: int | None, artifacts_produced: int | None,
                      turns_typed: int | None) -> float | None:
    """(verified claims + artifacts produced) ÷ typed turns.

    None if ANY input is missing or there are no typed turns: a missing numerator defaulted to
    0 would fabricate a low score, which is a fabrication like any other.
    """
    if verified_claims is None or artifacts_produced is None or not turns_typed:
        return None
    return (verified_claims + artifacts_produced) / turns_typed


def _ratio(num: int | None, den: int | None) -> float | None:
    if num is None or not den:
        return None
    return num / den


@dataclass
class Cell:
    """One of the five run numbers: the printed value, and where it comes from."""
    label: str
    value: str            # "—" when not computable here
    source: str           # tooltip: the tool that owns this number
    cost: bool = False    # typed turns is the denominator — labelled as cost on the card


@dataclass
class Activity:
    athlete: str
    title: str
    harness: str
    project: str
    date_str: str
    # headline stats (the three big numbers, Strava-style)
    distance: str          # prompts you typed
    moving_time: str       # session duration
    pace: str              # time per typed prompt
    # secondary
    effort: str            # tool calls (the grind / 'elevation')
    segments: str          # files touched
    commits: str
    prompts_per_hour: str
    focus_pb: bool         # a light 'personal best' flag when cadence is high
    rhythm: list[int]      # the route profile
    # THE HEADLINE — verified per turn — and the five numbers of a run
    headline: str = "—"                        # e.g. "0.21"
    headline_val: float | None = None
    headline_formula: str = ""                 # "(6 verified + 4 artifacts) ÷ 47 typed turns"
    five: list = field(default_factory=list)   # five Cell rows, in the metric spec's order

HEADLINE_TIP = ("verified per turn = (verified claims + artifacts produced) ÷ typed turns. "
                "Local v0: claims.py rule + Edit/Write paths on disk — it over-counts, read it as a "
                "ceiling until Helicon witness replaces it")


@dataclass
class Headline:
    """The card's one big number, and the five cells that sit under it. ONE definition,
    used by every surface (demo card, grind card, profile, terminal), so they cannot disagree."""
    text: str                  # "0.21" or "—"
    value: float | None
    formula: str               # "(6 verified + 4 artifacts) ÷ 47 typed turns" / "needs …"
    five: list                 # five Cell rows, in the metric spec's order


def five_cells(run: dict) -> list[Cell]:
    turns = run.get("turns_typed")
    claims = run.get("claims")
    verified = run.get("claims_verified")
    corrections = run.get("corrections")
    produced = run.get("artifacts_produced")
    promised = run.get("artifacts_promised")
    reach = run.get("reach")
    share = _ratio(verified, claims)   # None when no claims were made
    corr = _ratio(corrections, turns)

    def _n(v):
        return "—" if v is None else str(v)

    return [
        Cell("typed turns", _n(turns), SOURCES["typed_turns"], cost=True),
        Cell("verified claims",
             f"{verified}/{claims} · {share:.0%}" if share is not None else
             (f"{verified}/{claims}" if verified is not None and claims is not None else "—"),
             SOURCES["verified_share"]),
        Cell("correction rate", f"{corr:.0%}" if corr is not None else "—", SOURCES["correction_rate"]),
        Cell("produced ÷ promised", f"{_n(produced)} ÷ {_n(promised)}", SOURCES["produced_over_promised"]),
        Cell("reach", ("yes" if reach else "no") if reach is not None else "—", SOURCES["reach"]),
    ]


def headline_of(run: dict) -> Headline:
    """Verified per turn from a run dict, or a dash that says which part is missing."""
    turns = run.get("turns_typed")
    verified = run.get("claims_verified")
    produced = run.get("artifacts_produced")
    vpt = verified_per_turn(verified, produced, turns)
    if vpt is not None:
        text = f"{vpt:.2f}"
        formula = f"({verified} verified + {produced} artifacts) ÷ {turns} typed turns"
    else:
        text = "—"
        missing = [k for k, v in (("verified claims", verified), ("artifacts produced", produced),
                                  ("typed turns", turns)) if v is None]
        formula = "needs " + ", ".join(missing) if missing else "no typed turns"
    return Headline(text=text, value=vpt, formula=formula, five=five_cells(run))


def build_activity(run: dict) -> Activity:
    turns = run.get("turns_typed")
    dur = run.get("duration_s")
    tools = run.get("tool_calls")
    files = run.get("files_touched")
    commits = run.get("commits")
    rhythm = run.get("rhythm") or []

    pace_sec = (dur / turns) if (dur and turns) else None
    pph = (turns / (dur / 3600)) if (dur and turns) else None
    # 'personal best': a genuinely high, sustained cadence — traced, not decorative.
    focus_pb = bool(pph and pph >= 25 and turns and turns >= 30)

    started = run.get("started")
    try:
        date_str = datetime.fromisoformat(started).strftime("%a %d %b %Y · %H:%M") if started else "—"
    except ValueError:
        date_str = started or "—"

    hl = headline_of(run)

    return Activity(
        athlete=run.get("athlete", "athlete"),
        title=run.get("title", "Untitled session"),
        harness=run.get("harness", "coding agent"),
        project=run.get("project", "—"),
        date_str=date_str,
        distance=f"{turns} prompts" if turns is not None else "—",
        moving_time=_fmt_dur(dur),
        pace=_fmt_pace(pace_sec),
        effort=f"{tools} tool calls" if tools is not None else "—",
        segments=f"{files} files" if files is not None else "—",
        commits=str(commits) if commits is not None else "—",
        prompts_per_hour=f"{pph:.1f}/h" if pph else "—",
        focus_pb=focus_pb,
        rhythm=[int(x) for x in rhythm],
        headline=hl.text,
        headline_val=hl.value,
        headline_formula=hl.formula,
        five=hl.five,
    )
