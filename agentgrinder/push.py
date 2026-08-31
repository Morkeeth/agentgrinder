"""Build a metrics-only import URL for the web app. No prompt text, no paths."""
from __future__ import annotations

import base64
import json
import os
import urllib.parse

DEFAULT_URL = os.environ.get("AGENTGRINDER_URL", "https://agentgrinder.vercel.app")


def export_run(run: dict) -> dict:
    """Allowlisted fields only — must match site/index.html importRun()."""
    rig = run.get("rig") or {}
    rhythm = run.get("rhythm") or run.get("series")
    out = {
        "harness": run.get("harness"),
        "project": run.get("project"),
        "turns_typed": run.get("turns_typed"),
        "duration_s": run.get("duration_s"),
        "tool_calls": run.get("tool_calls"),
        "files_touched": run.get("files_touched"),
        "commits": run.get("commits"),
        "started": run.get("started"),
        "rhythm": rhythm,
        "route": run.get("route"),
        "rig_mcps": rig.get("mcps"),
        "rig_skills": rig.get("skills"),
        "rig_share_names": rig.get("share_names"),
        "rig_mcp_names": rig.get("mcp_names") if rig.get("share_names") else None,
        "rig_notes": rig.get("notes") or rig.get("stack_notes"),
    }
    return {k: v for k, v in out.items() if v is not None}


def import_url(run: dict, base: str | None = None) -> str:
    base = (base or DEFAULT_URL).rstrip("/")
    payload = export_run(run)
    raw = json.dumps(payload, separators=(",", ":")).encode()
    token = urllib.parse.quote(base64.b64encode(raw).decode(), safe="")
    return f"{base}/#import={token}"
