"""The local series record: one reading per grind, one prediction per upcoming grind.

Named `log` and `record`, never anything else. A reading carries the five numbers the coach
owns (typed turns, claims, verified claims, artifacts produced, commits) and the headline they
make, verified per turn. `value` is NULL when the headline could not be computed; an unmeasured
run is a row that says so, not a zero.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone

from ..metrics import verified_per_turn

DEFAULT_PATH = os.path.expanduser("~/.agentgrinder/series.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL,
    started TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    turns_typed INTEGER,
    claims INTEGER,
    claims_verified INTEGER,
    artifacts_produced INTEGER,
    commits INTEGER,
    value REAL,
    command TEXT NOT NULL,
    UNIQUE(project, started)
);
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL,
    text TEXT NOT NULL,
    made_at TEXT NOT NULL,
    consumed_by TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: str | None = None) -> sqlite3.Connection:
    path = path or os.environ.get("AGENTGRINDER_SERIES") or DEFAULT_PATH
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def record_run(conn: sqlite3.Connection, run: dict, command: str = "agentgrinder grind") -> dict:
    """Store one grind as a reading. The same sitting drawn twice replaces its own row."""
    project = run.get("project") or "session"
    started = run.get("started")
    if not started:
        raise ValueError("a reading needs the sitting's start time")
    value = verified_per_turn(run.get("claims_verified"), run.get("artifacts_produced"), run.get("turns_typed"))
    row = dict(project=project, started=started, recorded_at=_now(),
               turns_typed=run.get("turns_typed"), claims=run.get("claims"),
               claims_verified=run.get("claims_verified"), artifacts_produced=run.get("artifacts_produced"),
               commits=run.get("commits"), value=value, command=command)
    conn.execute("DELETE FROM readings WHERE project = ? AND started = ?", (project, started))
    conn.execute("INSERT INTO readings (project, started, recorded_at, turns_typed, claims, claims_verified, "
                 "artifacts_produced, commits, value, command) VALUES (?,?,?,?,?,?,?,?,?,?)",
                 (project, started, row["recorded_at"], row["turns_typed"], row["claims"],
                  row["claims_verified"], row["artifacts_produced"], row["commits"], value, command))
    conn.commit()
    return row


def list_readings(conn: sqlite3.Connection, project: str) -> list[dict]:
    """Every reading on one project, oldest sitting first (by when the sitting started)."""
    rows = conn.execute("SELECT * FROM readings WHERE project = ? ORDER BY started", (project,)).fetchall()
    return [dict(r) for r in rows]


def predict(conn: sqlite3.Connection, project: str, text: str) -> dict:
    """Write down what you expect the next grind on this project to do, before it happens."""
    text = (text or "").strip()
    if not text:
        raise ValueError("a prediction needs words")
    made = _now()
    cur = conn.execute("INSERT INTO predictions (project, text, made_at) VALUES (?,?,?)", (project, text, made))
    conn.commit()
    return dict(id=cur.lastrowid, project=project, text=text, made_at=made)


def take_prediction(conn: sqlite3.Connection, project: str, started: str) -> dict | None:
    """The newest unconsumed prediction on this project, made before the sitting started,
    marked as consumed by it. None when there is nothing pending."""
    row = conn.execute("SELECT * FROM predictions WHERE project = ? AND (consumed_by IS NULL OR consumed_by = ?) "
                       "AND made_at <= ? ORDER BY made_at DESC LIMIT 1", (project, started, started)).fetchone()
    if row is None:
        return None
    conn.execute("UPDATE predictions SET consumed_by = ? WHERE id = ?", (started, row["id"]))
    conn.commit()
    return dict(row) | {"consumed_by": started}
