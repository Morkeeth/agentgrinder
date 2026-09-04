"""`authorship` must count the window it was asked for, not the last burst inside it.

Found 4 September 2026 by another lane trying to reproduce a figure from a document. On a machine
with 1,534 transcripts, `agentgrinder authorship --hours 336` reported one session and 62 records,
and printed a span next to it. Every window anyone tried returned the same reading, which is what
made it look like the flag was being ignored. The flag was fine.

`fleet.collect` narrows its window to the LAST contiguous burst of activity, which is exactly right
for the night-run card it was written for: a run is one run, not everything since the earliest
stray lane. `authorship` reused it and inherited the narrowing. Measured that day over 336 hours:
296 files passed the mtime filter, 57 held a typed turn in the window, 966 typed turns in total,
and the command reported 5 human out of 62. The burst discarded 56 sessions and 961 typed turns.

That is a number correct about the wrong object, printed by the command whose entire job is to
correct a number that is about the wrong object. No test caught it because every test built one
burst.

So these build TWO bursts, hours apart, and assert the difference.
"""
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentgrinder import fleet


def _session(path, start, typed_count=3, spacing_min=2):
    """A minimal Claude Code transcript: `typed_count` human turns plus one tool result each."""
    lines = []
    for i in range(typed_count):
        ts = (start + timedelta(minutes=i * spacing_min)).isoformat()
        lines.append(json.dumps({
            "type": "user", "timestamp": ts, "cwd": "/tmp/p",
            "promptSource": "typed",
            "message": {"role": "user", "content": "do the thing"}}))
        lines.append(json.dumps({
            "type": "user", "timestamp": ts, "cwd": "/tmp/p",
            "message": {"role": "user", "content": [
                {"type": "tool_result", "content": "42 passed"}]}}))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _two_bursts(tmp_path, monkeypatch):
    """Two sessions six hours apart, which is far more than the 30 minute burst gap."""
    projects = tmp_path / "projects"
    (projects / "proj-a").mkdir(parents=True)
    (projects / "proj-b").mkdir(parents=True)
    now = datetime.now().astimezone()
    old_start = now - timedelta(hours=6)
    new_start = now - timedelta(minutes=20)
    _session(projects / "proj-a" / "old.jsonl", old_start)
    _session(projects / "proj-b" / "new.jsonl", new_start)
    monkeypatch.setattr(fleet, "PROJECTS", str(projects))
    return now - timedelta(hours=24), now


def test_the_burst_default_still_keeps_only_the_last_run(tmp_path, monkeypatch):
    """The night-run card depends on this, so the fix must not quietly change it."""
    since, until = _two_bursts(tmp_path, monkeypatch)
    run = fleet.collect(since, until)
    assert len(run["sessions"]) == 1, "the burst default stopped narrowing to the last run"
    assert run["authorship"]["by_category"]["human"] == 3


def test_without_the_burst_the_whole_window_is_counted(tmp_path, monkeypatch):
    """Both sessions are inside the window the caller asked for, so both must be counted."""
    since, until = _two_bursts(tmp_path, monkeypatch)
    run = fleet.collect(since, until, burst=False)
    assert len(run["sessions"]) == 2, "the earlier session is still being discarded"
    assert run["authorship"]["by_category"]["human"] == 6
    # and the categories still sum, which is the property the whole command exists to print
    a = run["authorship"]
    assert sum(a["by_category"].values()) == a["user_records_total"]


def test_the_authorship_command_asks_for_the_whole_window(tmp_path, monkeypatch, capsys):
    """The command, not the function. This is the surface a person reads."""
    from agentgrinder import cli
    since, until = _two_bursts(tmp_path, monkeypatch)
    rc = cli.main(["authorship", "--hours", "24"])
    out = capsys.readouterr().out
    assert rc == 0
    # `"6" in out` was the first version of this and it passed with the fix disabled, because a
    # digit 6 appears in a timestamp. Assert the row, not the character.
    import re as _re
    m = _re.search(r"^\s*([\d,]+)\s+[\d.]+%\s+human\b", out, _re.M)
    assert m, out
    assert m.group(1) == "6", f"the human row reads {m.group(1)}, so the earlier session is still dropped"
    # the header must not print a span the numbers do not describe
    assert "in the window you asked for" in out
    assert "earliest and latest record actually found" in out


def test_a_window_with_one_burst_reads_the_same_either_way(tmp_path, monkeypatch):
    """The fix must be invisible when there is nothing to narrow. Watched the other way."""
    projects = tmp_path / "projects"
    (projects / "only").mkdir(parents=True)
    now = datetime.now().astimezone()
    _session(projects / "only" / "s.jsonl", now - timedelta(minutes=15))
    monkeypatch.setattr(fleet, "PROJECTS", str(projects))
    since, until = now - timedelta(hours=24), now
    assert (fleet.collect(since, until)["authorship"]["by_category"]["human"]
            == fleet.collect(since, until, burst=False)["authorship"]["by_category"]["human"] == 3)
