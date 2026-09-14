"""Cold repair: refuse elapsed rates on untimed Cursor traces; safe titles."""
import json
import subprocess
from agentgrinder.ingest import parse_cursor_session
from agentgrinder.metrics import build_activity
from agentgrinder.render import render_card


def _repo(tmp_path, name="proj"):
    root = tmp_path / name
    (root / "src").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    return root


def _cursor(tmp_path, blocks, turns=2):
    lines = []
    for i in range(turns):
        lines.append(json.dumps({"role": "user", "message": {"content":
            f"<timestamp>Wednesday, Sep 03, 2026, {10 + i}:00 AM</timestamp>"
            "<user_query>go</user_query>"}}))
    lines.append(json.dumps({"role": "assistant", "message": {"content": blocks}}))
    path = tmp_path / "c.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def test_cursor_refuses_elapsed_rates_when_trace_is_turn_order(tmp_path):
    root = _repo(tmp_path)
    made = root / "src" / "a.py"
    made.write_text("x=1\n")
    path = _cursor(tmp_path, [
        {"type": "tool_use", "name": "Write", "input": {"path": str(made)}},
    ], turns=3)
    run = parse_cursor_session(path)
    assert run["capabilities"]["timed_trace"] is False
    assert run["duration_s"] is None
    assert "Cursor sitting" in run["title"]
    assert "go" not in run["title"]
    assert run.get("private_title_prompt")
    a = build_activity(run)
    assert a.moving_time == "—"
    assert a.pace == "—"
    assert a.prompts_per_hour == "—"
    html = render_card(a)
    assert "15m" not in html and "2:30" not in html
    assert "not a measured elapsed clock" in html


def test_timed_trace_still_shows_duration_when_capability_true():
    run = {
        "athlete": "you", "title": "real timed", "harness": "Claude Code", "project": "p",
        "started": "2026-09-01T10:00:00+00:00", "duration_s": 900, "turns_typed": 6,
        "tool_calls": 10, "files_touched": 2, "commits": 0, "rhythm": [1, 1],
        "claims_verified": 2, "artifacts_produced": 4,
        "capabilities": {"timed_trace": True, "claim_evidence": True},
    }
    a = build_activity(run)
    assert a.moving_time != "—"
    assert "m" in a.moving_time
    assert a.prompts_per_hour != "—"
