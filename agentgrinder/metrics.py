"""Map a coding-agent session to an athletic 'run'. Every metric traces to the session log.

A 'run' JSON (see samples/) carries only counts read from a real session:
  athlete, title, harness, project, started (ISO), duration_s,
  turns_typed, tool_calls, files_touched, commits,
  rhythm  -> typed turns per time bucket (the 'route')

We never invent a number. If a field is missing, the derived stat is None and the card
shows a dash, not a guess (Constitution rule 3).
"""
from __future__ import annotations

from dataclasses import dataclass
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
    )
