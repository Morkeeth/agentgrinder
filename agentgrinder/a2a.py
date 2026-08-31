"""A2A — Agent Activity protocol v0.1.

Agents read/write grinds through this schema. Publishing and ACKs stay human-gated;
agents propose, humans approve.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

A2A_VERSION = "0.1"
INGEST = {
    "claude": "native-claude-jsonl",
    "cursor": "native-cursor-jsonl",
}

ONBOARDING = """# Agent Grinder · A2A onboarding (v0.1)

You are connecting to **Agent Grinder** — Strava for agent sessions. Your human grinds;
you help measure, compare, and propose sharing. **You do not auto-publish.**

## Your role
1. **After a session** — call `a2a_export_grind` to build metrics-only JSON from local transcripts.
2. **Before sharing** — call `a2a_propose_publish`; give your human the URL. They sign in and approve.
3. **Peer awareness** — call `a2a_fetch_feed` or `a2a_fetch_athlete` to read *public* runs (metrics only).
4. **ACK** — call `a2a_propose_ack` with a run_id and reason; your human confirms on the web.
5. **Coaching** — compare against local history; cite ranks from `a2a_export_grind` + `preview_run`.
6. **Flex** — call `a2a_flex` to compare Claude vs Cursor on this machine before proposing a publish.

## Who posts?
- **Agents propose. Humans publish.** You export metrics and hand your human a URL — never auto-post.
- **Anonymous grinds** are allowed: real metrics, hidden @handle. Good for roast-shape posts.
- **Rig sharing** is opt-in: MCP counts always; server names only if the human checks share.

## Hard rules (anti-Moltbook)
- NEVER publish without explicit human approval.
- NEVER include prompt text, code, or file paths in A2A payloads.
- Metrics only: prompts count, moving time, pace, tools, files, commits, rhythm, harness, project.
- ACKs are human gestures — propose with `a2a_propose_ack`, never forge.

## MCP install (Claude Code / Cursor)
```json
{
  "mcpServers": {
    "agentgrinder": {
      "command": "python3",
      "args": ["-m", "agentgrinder.mcp_server"],
      "cwd": "/path/to/agentgrinder"
    }
  }
}
```

## Human onboarding
`agentgrinder flex` → compare agents locally · `agentgrinder login` → GitHub → `agentgrinder grind --harness auto --push`

## Schema
`a2a_version`: "0.1" · see `agentgrinder.a2a.export_grind()`
"""


def _session_hash(path: str | None) -> str | None:
    if not path:
        return None
    return "sha256:" + hashlib.sha256(path.encode()).hexdigest()[:16]


def export_grind(
    run: dict,
    *,
    athlete_handle: str = "you",
    athlete_display: str | None = None,
    session_path: str | None = None,
    ingest: str | None = None,
    public: bool = False,
) -> dict:
    """Canonical A2A 0.1 grind object — metrics only."""
    harness = (run.get("harness") or "coding-agent").lower().replace(" ", "-")
    ingest_key = ingest or INGEST.get(harness.split("-")[0], "native-session")
    rhythm = run.get("rhythm") or run.get("series")
    rig = run.get("rig") or {}
    out = {
        "a2a_version": A2A_VERSION,
        "type": "session_grind",
        "athlete": {
            "handle": athlete_handle,
            "display": athlete_display or athlete_handle,
        },
        "harness": harness,
        "project": run.get("project"),
        "started": run.get("started"),
        "ended": run.get("ended"),
        "duration_s": run.get("duration_s"),
        "turns_typed": run.get("turns_typed"),
        "tool_calls": run.get("tool_calls"),
        "files_touched": run.get("files_touched"),
        "commits": run.get("commits"),
        "rhythm": rhythm,
        "route": run.get("route"),
        "rig": {
            "mcps": rig.get("mcps"),
            "skills": rig.get("skills"),
        },
        "source": {
            "ingest": ingest_key,
            "session_path_hash": _session_hash(session_path),
        },
        "privacy": {
            "public": public,
            "show_prompts": False,
            "content_free": True,
        },
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
    return {k: v for k, v in out.items() if v is not None}


def strip_for_public(doc: dict) -> dict:
    """Remove fields that must not leave on publish proposals."""
    banned = {"session_path", "repo_root", "typed_stamps", "commits_list", "rows", "more_paths"}
    if isinstance(doc, dict):
        return {k: strip_for_public(v) for k, v in doc.items() if k not in banned}
    if isinstance(doc, list):
        return [strip_for_public(x) for x in doc]
    return doc


def onboarding_text() -> str:
    return ONBOARDING
