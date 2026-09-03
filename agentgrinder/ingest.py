"""Native ingest: a real Claude Code session (.jsonl) -> a run dict. No external deps.

The authorship signal is not decided here: every `type: "user"` record goes through
`authorship.is_human_turn`, the one gate the whole package shares (Transcripto's measured rule,
vendored). Tool results and injected context are `type: "user"` too and are not the operator's
turns. Every number below is read from the log.
"""
from __future__ import annotations

import glob
import json
import os
from datetime import datetime

from .authorship import is_human_turn
from .claims import ClaimTracker, is_tool_result, result_text

_EDIT_TOOLS = {"Edit", "Write", "NotebookEdit"}


def _ts(o: dict):
    t = o.get("timestamp")
    if not t:
        return None
    try:
        return datetime.fromisoformat(t.replace("Z", "+00:00"))
    except ValueError:
        return None


def _tool_uses(msg: dict):
    """Yield (tool_name, input_dict) for each tool_use block in an assistant message."""
    content = msg.get("content")
    if isinstance(content, list):
        for b in content:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                yield b.get("name", ""), (b.get("input") or {})


CLAUDE_GLOB = "~/.claude/projects/*/*.jsonl"
CURSOR_GLOB = "~/.cursor/projects/*/agent-transcripts/*/*.jsonl"


def latest_session() -> str | None:
    files = glob.glob(os.path.expanduser(CLAUDE_GLOB))
    return max(files, key=os.path.getmtime) if files else None


def searched_paths() -> tuple:
    """Every transcript location the tool reads, in the order it reads them.

    An error that says "nothing found" without saying where it looked is untestable by the person
    reading it. Every not-found message prints this list.
    """
    return (CLAUDE_GLOB, CURSOR_GLOB) + CODEX_GLOBS


def parse_session(path: str, athlete: str = "you") -> dict:
    typed_ts, all_ts = [], []
    tool_calls = 0
    files: set[str] = set()
    route: list[str] = []  # ordered top-level regions touched (the code 'GPS' path)
    commits = 0
    project = None
    first_prompt = None
    tracker = ClaimTracker()       # v0 verified-claims rule, see claims.py
    written: set[str] = set()      # Edit/Write paths; 'produced' = the ones that exist at close

    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = _ts(o)
            if ts:
                all_ts.append(ts)
            if not project:
                project = o.get("cwd") or None
            typ = o.get("type")
            msg = o.get("message") if isinstance(o.get("message"), dict) else {}

            if is_human_turn(o):
                tracker.typed_turn()
                if ts:
                    typed_ts.append(ts)
                if first_prompt is None:
                    c = msg.get("content")
                    if isinstance(c, str):
                        first_prompt = c.strip()
                    elif isinstance(c, list):
                        for b in c:
                            if isinstance(b, dict) and b.get("type") == "text":
                                first_prompt = (b.get("text") or "").strip()
                                break
            elif is_tool_result(o):
                tracker.tool_result(result_text(o))
            elif typ == "assistant":
                c = msg.get("content")
                if isinstance(c, list):
                    tracker.assistant_text("\n".join(
                        b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"))
                elif isinstance(c, str):
                    tracker.assistant_text(c)
                for name, inp in _tool_uses(msg):
                    tool_calls += 1
                    if name in _EDIT_TOOLS and inp.get("file_path"):
                        fp = inp["file_path"]; files.add(fp); written.add(fp)
                        # region = first meaningful path segment (privacy: names stay local; only indices are pushed)
                        parts = [p for p in fp.replace(str(project or ""), "").split("/") if p and not p.startswith(".")]
                        route.append(parts[0] if parts else "root")
                    elif name == "Bash":
                        cmd = (inp.get("command") or "")
                        if "git commit" in cmd:
                            commits += 1

    tracker.close()
    if not typed_ts:
        raise ValueError(f"no typed human turns found in {path}")
    # v0 'artifacts produced': Edit/Write paths that exist on disk at PARSE time (not at the
    # session's close — a later delete or rename reads as not produced). 'promised' is ZUP's.
    artifacts_produced = sum(1 for fp in written if os.path.exists(fp))

    # moving time (Strava-style): sum gaps between events, but a gap over IDLE_CAP means you stepped away
    IDLE_CAP = 1200  # 20 min
    ev = sorted(t for t in all_ts if t >= min(typed_ts))
    span = 0
    for a, b in zip(ev, ev[1:]):
        span += min((b - a).total_seconds(), IDLE_CAP)
    # rhythm: typed turns bucketed across the session span (the 'route')
    buckets = 24
    rhythm = [0] * buckets
    if span > 0:
        t0 = min(typed_ts)
        for t in typed_ts:
            idx = min(buckets - 1, int((t - t0).total_seconds() / span * buckets))
            rhythm[idx] += 1
    else:
        rhythm = [len(typed_ts)]

    cwd = project.rstrip("/") if project else ""
    proj_name = os.path.basename(cwd) if cwd else "session"
    # real characteristic: does the project carry a rules/context file? (Karpathy: rules cut errors ~41%->11%)
    rules = None; rules_lines = 0; has_plan = False
    if cwd:
        for pc in ("spec.md", "PLAN.md", "plan.md", "docs/spec.md", "docs/PLAN.md"):
            if os.path.exists(os.path.join(cwd, pc)):
                has_plan = True
                break
        for cand in ("CLAUDE.md", "AGENTS.md", ".cursor/rules", ".cursorrules"):
            p = os.path.join(cwd, cand)
            if os.path.exists(p):
                rules = cand
                try: rules_lines = sum(1 for _ in open(p, encoding="utf-8", errors="ignore"))
                except OSError: rules_lines = 0
                break
    title = (first_prompt[:60] + "…") if first_prompt and len(first_prompt) > 60 else (first_prompt or f"{proj_name} session")

    return {
        "athlete": athlete,
        "title": title,
        "harness": "Claude Code",
        "project": proj_name,
        "started": min(typed_ts).isoformat(),
        "duration_s": int(span),
        "turns_typed": len(typed_ts),
        "tool_calls": tool_calls,
        "files_touched": len(files),
        "commits": commits,
        "rhythm": rhythm,
        # the five numbers (fleet-ops/METRICS-AGENTIC-ENGINEERING-2026-09-02.md); None = not this repo's to compute
        "claims": tracker.claims,
        "claims_verified": tracker.verified,     # v0 rule, claims.py
        "corrections": None,                     # Transcripto (coach inverse class) — not built
        "artifacts_produced": artifacts_produced,
        "artifacts_promised": None,              # ZUP artifact-detect
        "reach": None,                           # git remotes + gh + launch log
        "has_rules": bool(rules), "rules_file": rules, "rules_lines": rules_lines, "has_plan": has_plan,
        "rig": detect_rig(),
        "route": _route_indices(route),          # numbers only -- safe to publish
        "route_legend": _dedupe(route),          # region names — LOCAL only, never pushed
    }


# ---- Cursor origin -----------------------------------------------------------
# Cursor stores one session per dir: ~/.cursor/projects/*/agent-transcripts/<uuid>/<uuid>.jsonl
# A TYPED human turn is role:user whose text carries a <user_query>...</user_query> wrapper
# (Cursor's own honest authorship signal; injected/tool records do not carry it).
import re as _re

def _cursor_text(msg: dict) -> str:
    c = msg.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    return ""

def _cursor_tool_blocks(msg: dict) -> int:
    c = msg.get("content")
    return sum(1 for b in c if isinstance(b, dict) and b.get("type") not in (None, "text")) if isinstance(c, list) else 0

def latest_cursor_session() -> str | None:
    files = glob.glob(os.path.expanduser(CURSOR_GLOB))
    return max(files, key=os.path.getmtime) if files else None

def parse_cursor_session(path: str, athlete: str = "you") -> dict:
    typed = 0
    tool_calls = 0
    stamps = []
    first_prompt = None
    ts_re = _re.compile(r"<timestamp>(.*?)</timestamp>")
    uq_re = _re.compile(r"<user_query>(.*?)</user_query>", _re.S)
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            role = o.get("role")
            msg = o.get("message") if isinstance(o.get("message"), dict) else {}
            text = _cursor_text(msg)
            if role == "user" and "<user_query>" in text:
                typed += 1
                m = ts_re.search(text)
                if m:
                    stamps.append(m.group(1))
                if first_prompt is None:
                    q = uq_re.search(text)
                    first_prompt = (q.group(1).strip() if q else text.strip())
            elif role == "assistant":
                tool_calls += _cursor_tool_blocks(msg)

    if not typed:
        raise ValueError(f"no typed <user_query> turns in {path}")

    # duration from first/last embedded timestamp (best-effort), else None
    dur = None
    def _pt(s):
        s = _re.sub(r"\s*\(UTC[^)]*\)", "", s).strip()
        for fmt in ("%A, %b %d, %Y, %I:%M %p", "%A, %B %d, %Y, %I:%M %p"):
            try: return datetime.strptime(s, fmt)
            except ValueError: pass
        return None
    pts = [p for p in (_pt(s) for s in stamps) if p]
    if len(pts) >= 2:
        dur = int((max(pts) - min(pts)).total_seconds())

    # rhythm: bucket typed turns by position (24 buckets) — shape without needing per-turn time
    buckets = min(24, max(1, typed))
    rhythm = [0] * buckets
    for i in range(typed):
        rhythm[min(buckets - 1, i * buckets // typed)] += 1

    proj = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(path)))).replace("Users-morkeeth-", "")
    title = (first_prompt[:60] + "…") if first_prompt and len(first_prompt) > 60 else (first_prompt or f"{proj} session")
    return {
        "athlete": athlete, "title": title, "harness": "Cursor", "project": proj,
        "started": (min(pts).isoformat() if pts else None),
        "duration_s": dur, "turns_typed": typed, "tool_calls": tool_calls,
        "files_touched": None, "commits": None, "rhythm": rhythm,
    }


# ---- Codex origin ------------------------------------------------------------
# rollout-*.jsonl — event_msg user_message = human turn.
#
# WHERE CODEX ACTUALLY WRITES. Until 3 Sep 2026 this globbed `~/.codex/archived_sessions/*.jsonl`
# only, flat and non-recursive. Codex CLI writes live sessions to
# `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` and archives a fraction of them. Measured on the
# author's own machine that day: the shipped glob saw 16 files, the real tree held 64. A person
# who has just started with Codex has no archived sessions at all, so every Codex command
# returned "nothing to read" while their transcripts sat on disk.
_INJECT_MARKERS = ("<recommended_plugins>", "<environment_context>", "<turn_aborted>")

CODEX_GLOBS = (
    "~/.codex/sessions/**/*.jsonl",      # where live sessions land, nested by date
    "~/.codex/archived_sessions/*.jsonl",  # where some of them are moved later
)


def codex_session_files() -> list[str]:
    """Every Codex rollout on this machine, both trees, newest first, no duplicates."""
    seen: dict[str, float] = {}
    for pat in CODEX_GLOBS:
        for f in glob.glob(os.path.expanduser(pat), recursive=True):
            if f in seen or not os.path.isfile(f):
                continue
            try:
                seen[f] = os.path.getmtime(f)
            except OSError:
                continue
    return sorted(seen, key=lambda f: seen[f], reverse=True)


def latest_codex_session() -> str | None:
    files = codex_session_files()
    return files[0] if files else None


def _codex_count(path: str) -> tuple[int, int] | None:
    """Fast typed/tool estimate without full JSON parse of megabyte lines."""
    typed = tools = 0
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if '"type":"user_message"' in line and "<recommended_plugins>" not in line:
                    typed += 1
                if '"role":"assistant"' in line and '"type":"' in line:
                    tools += line.count('"type":"') - line.count('"type":"message"')
    except OSError:
        return None
    return (typed, max(tools, 0)) if typed else None


def parse_codex_session(path: str, athlete: str = "you") -> dict:
    hit = _codex_count(path)
    if not hit:
        raise ValueError(f"no human user_message turns in {path}")
    typed, tool_calls = hit
    cwd = None
    try:
        with open(path, encoding="utf-8") as fh:
            head = fh.readline()
        o = json.loads(head)
        if o.get("type") == "session_meta":
            cwd = (o.get("payload") or {}).get("cwd")
    except (OSError, ValueError, json.JSONDecodeError):
        pass

    buckets = min(24, max(1, typed))
    rhythm = [0] * buckets
    for i in range(typed):
        rhythm[min(buckets - 1, i * buckets // typed)] += 1

    proj = os.path.basename(cwd) if cwd else os.path.basename(path).replace(".jsonl", "")[:32]
    title = f"{proj} session"
    return {
        "athlete": athlete,
        "title": title,
        "harness": "Codex",
        "project": proj,
        "started": None,
        "duration_s": None,
        "turns_typed": typed,
        "tool_calls": tool_calls,
        "files_touched": None,
        "commits": None,
        "rhythm": rhythm,
    }


def _dedupe(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen: seen.add(x); out.append(x)
    return out

def _route_indices(route):
    """Map the ordered region names to small integers — the publishable, name-free path."""
    order = {r: i for i, r in enumerate(_dedupe(route))}
    return [order[r] for r in route]


# ---- coach: light cross-session history (local only, privacy-safe) -----------
def _quick_stats(path: str):
    """Cheap parse of one Claude session: (date, typed_count, duration_s). No content read into memory."""
    typed_ts, all_ts = [], []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line: continue
                try: o = json.loads(line)
                except json.JSONDecodeError: continue
                t = _ts(o)
                if t: all_ts.append(t)
                if is_human_turn(o) and t:
                    typed_ts.append(t)
    except OSError:
        return None
    if not typed_ts: return None
    return (min(typed_ts).date(), len(typed_ts), (max(all_ts)-min(typed_ts)).total_seconds() if all_ts else 0)

def scan_history(limit: int = 150):
    files = sorted(glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")),
                   key=os.path.getmtime, reverse=True)[:limit]
    out = []
    for f in files:
        st = _quick_stats(f)
        if st: out.append(st)
    return out  # recent sessions: (date, typed, duration_s)

def best_recent_session(n: int = 12) -> str | None:
    """Pick the most substantial (most typed turns) among the n most-recently-modified sessions."""
    files = sorted(glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")), key=os.path.getmtime, reverse=True)[:n]
    best, best_typed = None, -1
    for f in files:
        st = _quick_stats(f)
        if st and st[1] > best_typed:
            best, best_typed = f, st[1]
    return best

def coach_lines(this_run: dict) -> list[str]:
    """Sober performance insight from local history. No streaks, no gamification. Numbers only."""
    hist = scan_history()  # (date, typed, duration_s)
    if len(hist) < 2:
        return []
    durs = sorted((h[2] for h in hist), reverse=True)
    prompts = sorted((h[1] for h in hist), reverse=True)
    # median cadence (prompts/hour) across history
    cads = [h[1] / (h[2] / 3600) for h in hist if h[2] > 300]
    med_cad = sorted(cads)[len(cads) // 2] if cads else 0
    d = this_run.get("duration_s") or 0
    tp = this_run.get("turns_typed") or 0
    tc = this_run.get("tool_calls") or 0
    commits = this_run.get("commits") or 0
    regions = len(set(this_run.get("route") or []))
    rig = this_run.get("rig") or {}
    graded, described = [], []
    # VERIFIED self-comparison: a true rank of active time
    if d and durs:
        rank = 1 + sum(1 for x in durs if x > d)
        if rank <= 3: graded.append(f"one of your longest focus sessions (#{rank} of {len(durs)})")
    # GROUNDED + CITED, most actionable first
    if this_run.get("has_rules") is False and this_run.get("project"):
        graded.append("no CLAUDE.md/rules file here - a rules file cut agent errors ~41%->11% (Karpathy)")
    elif this_run.get("rules_lines") and this_run["rules_lines"] < 15:
        graded.append(f"your rules file is only {this_run['rules_lines']} lines - thin rules leave the agent guessing (Karpathy/Osmani)")
    if this_run.get("has_plan") is False and this_run.get("project") and tp >= 8:
        graded.append("no plan/spec.md in this project - plan first, save the spec (Hashimoto/Willison)")
    if tc >= 40 and commits == 0:
        graded.append(f"{tc} tool calls, 0 commits - commit per unit of work (Huntley/Willison)")
    elif tp >= 8 and commits and commits < max(1, tp // 20):
        graded.append("few commits for the prompts - commit per unit of work, don't batch (Huntley)")
    if regions >= 5 and tp and regions > tp / 4:
        graded.append(f"touched {regions} regions - one bounded objective per session (Willison)")
    if rig.get("mcps") == 0 and rig.get("skills") == 0:
        graded.append("no MCPs or skills in your rig - a real setup is the cheap edge")
    # DESCRIPTIVE (real ratio, not a verdict) - only if room
    if tp and tc: described.append(f"{round(tc/tp,1)} tool calls per prompt this session")
    return (graded + described)[:4]

def detect_rig() -> dict:
    """Your setup, from local config. Non-sensitive: counts of MCPs + skills. Names stay local."""
    import json as _j
    mcps = skills = 0; mcp_names = []
    for cfg in (os.path.expanduser("~/.claude.json"), os.path.expanduser("~/.claude/settings.json")):
        try:
            d = _j.load(open(cfg))
            m = d.get("mcpServers") or {}
            if m: mcp_names = list(m.keys()); mcps = len(m); break
        except (OSError, ValueError): pass
    sk = os.path.expanduser("~/.claude/skills")
    if os.path.isdir(sk):
        skills = sum(1 for e in os.listdir(sk) if os.path.isdir(os.path.join(sk, e)))
    return {"mcps": mcps, "skills": skills, "mcp_names": mcp_names}
