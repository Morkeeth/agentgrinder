"""One call for the CLI: record this grind and attach its progress block to the run dict."""
from __future__ import annotations

from . import log
from .reporter import progress, progress_line


def record_and_attach(run: dict, path: str | None = None, command: str = "agentgrinder grind") -> dict:
    conn = log.connect(path)
    try:
        log.record_run(conn, run, command=command)
        project = run.get("project") or "session"
        pred = log.take_prediction(conn, project, run["started"])
        p = progress(log.list_readings(conn, project), run, pred)
    finally:
        conn.close()
    run["progress"] = p
    run["progress_line"] = progress_line(p, run.get("project") or "session")
    return run
