"""--coach must never be accepted and then silently skipped.

The defect this file pins, measured 3 Sep 2026 in a 3.12 venv with the Strands SDK installed:
`grind --harness cursor --coach` printed the "trace cannot be drawn" line, no coach block, no
verdict, no warning, and exited 0. This was not a missing dependency; the coach had no inputs. The
README's own claim is "it never degrades quietly", and this was the one place it did.

Cursor and Codex now score the claim rule over assistant text (4 Sep). They still cannot feed
every coach input: commits are absent on both, Write/Edit paths are often absent, and without
those the coach stays degraded. The banner names the fields the *parsed run* actually lacks —
not a frozen list — and exits non-zero. Nothing about either harness is fabricated to make the
coach run.
"""
import os
import tempfile
from pathlib import Path

from agentgrinder.cli import COACH_NEEDS, coach_degraded_banner

from test_harness_auto import codex_home, cursor_home, run_grind

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_the_banner_names_the_fields_the_parsed_run_actually_lacks():
    """Read off the run, not off a list someone must remember to update."""
    run = {"files_touched": None, "commits": None, "turns_typed": 3}
    text = coach_degraded_banner("Cursor", run)
    assert "DEGRADED" in text
    for field in COACH_NEEDS:
        assert field in text, field
    # a harness that does supply a field must not be accused of missing it
    text2 = coach_degraded_banner("Cursor", dict(run, files_touched=4, commits=1))
    assert "files_touched" not in text2 and "commits" not in text2
    assert "claims" in text2


def test_cursor_plus_coach_exits_non_zero_and_says_which_fields_are_missing(tmp_path):
    proc = run_grind(cursor_home(tmp_path / "home"), tmp_path, "--coach")
    assert proc.returncode != 0, proc.stdout
    assert "DEGRADED" in proc.stdout
    # Minimal cursor fixture has no Write paths and no commits — those stay missing.
    assert "commits" in proc.stdout
    assert (tmp_path / "card.html").exists()   # the card the run did produce is still written


def test_codex_plus_coach_exits_non_zero_and_says_which_fields_are_missing(tmp_path):
    proc = run_grind(codex_home(tmp_path / "home"), tmp_path, "--coach")
    assert proc.returncode != 0, proc.stdout
    assert "DEGRADED" in proc.stdout and "Codex" in proc.stdout


def test_cursor_without_coach_is_still_a_clean_exit_zero_and_no_false_alarm(tmp_path):
    """A red light that is always on is not a check. No --coach, no banner."""
    proc = run_grind(cursor_home(tmp_path / "home"), tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "DEGRADED" not in proc.stdout


def test_codex_without_coach_is_still_a_clean_exit_zero_and_no_false_alarm(tmp_path):
    proc = run_grind(codex_home(tmp_path / "home"), tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "DEGRADED" not in proc.stdout


def test_a_degraded_coach_request_does_not_push(tmp_path):
    """Publishing a run the person asked to have coached, uncoached, is the quiet degrade again."""
    proc = run_grind(cursor_home(tmp_path / "home"), tmp_path, "--coach", "--push")
    assert proc.returncode != 0
    assert "push ->" not in proc.stdout
    assert "#import=" not in proc.stdout


def test_no_cursor_or_codex_field_is_invented_when_the_transcript_lacks_it():
    """Parsers return None for what that transcript does not contain — verified by running them."""
    from agentgrinder import ingest

    home = Path(tempfile.mkdtemp())
    d = home / ".cursor" / "projects" / "x" / "agent-transcripts" / "a"
    d.mkdir(parents=True)
    (d / "t.jsonl").write_text(
        '{"role":"user","message":{"content":"<timestamp>Wednesday, Sep 03, 2026, 10:00 AM</timestamp>'
        '<user_query>build the thing</user_query>"}}\n'
        '{"role":"assistant","message":{"content":[{"type":"tool_use"},{"type":"text","text":"ok"}]}}\n',
        encoding="utf-8")
    c = home / ".codex" / "sessions" / "2026" / "09" / "03"
    c.mkdir(parents=True)
    (c / "rollout.jsonl").write_text(
        '{"type":"session_meta","payload":{"cwd":"/tmp/proj"}}\n'
        '{"type":"user_message","content":"do the thing"}\n'
        '{"role":"assistant","content":[{"type":"tool_use"}]}\n',
        encoding="utf-8")

    old_home = os.environ.get("HOME")
    os.environ["HOME"] = str(home)
    old_exp = os.path.expanduser
    os.path.expanduser = lambda p, _h=str(home): p.replace("~", _h, 1)
    try:
        cur = ingest.parse_cursor_session(ingest.latest_cursor_session())
        cod = ingest.parse_codex_session(ingest.latest_codex_session())
    finally:
        if old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = old_home
        os.path.expanduser = old_exp

    assert cur["commits"] is None and cur["artifacts_promised"] is None and cur["corrections"] is None
    assert cur["artifacts_produced"] is None   # no Write path in this fixture
    assert cur["files_touched"] is None
    assert cod["commits"] is None and cod["files_touched"] is None
    assert cod["artifacts_produced"] is None and "Write/Edit" in (cod.get("produced_reason") or "")
    assert isinstance(cur["claims"], int) and isinstance(cod["claims"], int)
