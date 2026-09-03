"""Flex — compare your real runs across agents (Claude, Cursor, fleet)."""
from __future__ import annotations

import glob
import os

from . import history
from .ingest import _codex_count, codex_session_files, latest_cursor_session, latest_codex_session, latest_session, parse_cursor_session, parse_codex_session

HARNESS_ORDER = ("Claude Code", "Cursor", "Fleet", "Codex")


def _claude_stats() -> dict:
    hist = history.load()
    if not hist:
        return dict(harness="Claude Code", grinds=0, prompts=0, moving_s=0, commits=0)
    return dict(
        harness="Claude Code",
        grinds=len(hist),
        prompts=sum(h["typed"] for h in hist),
        moving_s=sum(h["moving_s"] for h in hist),
        tools=sum(h["tools"] for h in hist),
        edits=sum(h["edits"] for h in hist),
    )


def _cursor_stats(scan: int = 80) -> dict:
    files = sorted(
        glob.glob(os.path.expanduser("~/.cursor/projects/*/agent-transcripts/*/*.jsonl")),
        key=os.path.getmtime,
        reverse=True,
    )[:scan]
    grinds = prompts = moving_s = 0
    for f in files:
        try:
            run = parse_cursor_session(f)
        except (OSError, ValueError):
            continue
        grinds += 1
        prompts += run.get("turns_typed") or 0
        moving_s += run.get("duration_s") or 0
    return dict(
        harness="Cursor",
        grinds=grinds,
        prompts=prompts,
        moving_s=moving_s,
        tools=0,
        commits=0,
    )


def _codex_stats(scan: int = 5) -> dict:
    files = codex_session_files()[:scan]   # both trees; see ingest.CODEX_GLOBS
    grinds = prompts = tools = 0
    for f in files:
        hit = _codex_count(f)
        if not hit:
            continue
        t, tc = hit
        grinds += 1
        prompts += t
        tools += tc
    return dict(
        harness="Codex",
        grinds=grinds,
        prompts=prompts,
        moving_s=0,
        tools=tools,
        commits=0,
    )


def local_flex() -> list[dict]:
    """Per-harness totals on this machine."""
    rows = [_claude_stats(), _cursor_stats(), _codex_stats()]
    return [r for r in rows if r["grinds"] > 0]


def latest_any() -> tuple[str, str] | None:
    """(harness_id, session_path) for the freshest grind across agents."""
    c = latest_session()
    cu = latest_cursor_session()
    cx = latest_codex_session()
    candidates: list[tuple[str, str, float]] = []
    if c:
        candidates.append(("claude", c, os.path.getmtime(c)))
    if cu:
        candidates.append(("cursor", cu, os.path.getmtime(cu)))
    if cx:
        candidates.append(("codex", cx, os.path.getmtime(cx)))
    if not candidates:
        return None
    harness, path, _ = max(candidates, key=lambda x: x[2])
    return harness, path


def format_flex(rows: list[dict] | None = None) -> str:
    rows = rows if rows is not None else local_flex()
    if not rows:
        return "No grinds found — run agentgrinder grind after a Claude or Cursor session."
    lines = ["\n  flex · your real runs across agents\n"]
    for r in rows:
        h = r["harness"]
        g = r["grinds"]
        p = r["prompts"]
        mins = r["moving_s"] // 60
        lines.append(f"  {h:<14}  {g:>4} grinds  {p:>6} prompts  {mins:>5}m moving")
    lines.append("\n  post any grind:  agentgrinder grind --push\n")
    try:
        from .meme import ghost_ratio
        tag, gl = ghost_ratio(sum(r["grinds"] for r in rows), 0)
        lines.insert(-1, f"  ghost flex · {tag}: {gl}\n")
    except Exception:
        pass
    return "\n".join(lines)


def flex_from_runs(runs: list[dict]) -> list[dict]:
    """Group published runs (web/DB) by harness string."""
    by: dict[str, dict] = {}
    for r in runs:
        raw = (r.get("harness") or "unknown").strip()
        key = raw if raw else "unknown"
        if key not in by:
            by[key] = dict(harness=key, grinds=0, prompts=0, moving_s=0, commits=0)
        b = by[key]
        b["grinds"] += 1
        b["prompts"] += r.get("prompts") or r.get("turns_typed") or 0
        b["moving_s"] += r.get("duration_s") or 0
        b["commits"] += r.get("commits") or 0
    return sorted(by.values(), key=lambda x: -x["grinds"])
