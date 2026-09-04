"""--coach must never be accepted and then silently skipped.

The defect this file pins, measured 3 Sep 2026 in a 3.12 venv with the Strands SDK installed:
`grind --harness cursor --coach` printed the "trace cannot be drawn" line, no coach block, no
verdict, no warning, and exited 0. This was not a missing dependency; the coach had no inputs. The
README's own claim is "it never degrades quietly", and this was the one place it did.

A Cursor or Codex transcript carries no file paths, no commits and no claim lines, so three of the
coach's five tools have nothing to read. The fix names those fields and exits non-zero. Nothing
about either harness is fabricated to make the coach run.
"""
import os
import subprocess
import sys

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
    for field in ("files_touched", "commits", "claims", "claims_verified", "artifacts_produced"):
        assert field in proc.stdout, field
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


def test_no_cursor_or_codex_field_is_invented_to_feed_the_coach(tmp_path):
    """A field the transcript does not contain reads None, never a fabricated 0.

    This used to grep ingest.py for the literal `"files_touched": None`. That pinned one
    IMPLEMENTATION of the rule rather than the rule, and it went red on 4 Sep 2026 when those
    parsers learned to read the file writes that were in the transcript all along. The rule it was
    protecting is the one that matters and it is asserted here on behaviour instead: a session that
    wrote nothing reports nothing, and an empty count never becomes a zero.
    """
    from agentgrinder.ingest import parse_cursor_session, parse_codex_session
    cur = tmp_path / "c.jsonl"
    cur.write_text('{"role":"user","message":{"content":"<timestamp>Wednesday, Sep 03, 2026, '
                   '10:00 AM</timestamp><user_query>go</user_query>"}}\n', encoding="utf-8")
    cod = tmp_path / "rollout-x.jsonl"
    cod.write_text('{"type":"session_meta","payload":{"cwd":"/no/such/dir"}}\n'
                   '{"type":"user_message","content":"go"}\n', encoding="utf-8")
    for run, harness in ((parse_cursor_session(str(cur)), "Cursor"),
                         (parse_codex_session(str(cod)), "Codex")):
        assert run["harness"] == harness
        for field in ("files_touched", "commits", "artifacts_produced",
                      "artifacts_promised", "corrections", "reach"):
            assert run[field] is None, f"{harness} invented {field} = {run[field]!r}"
        assert run["reach_reason"], f"{harness} prints a dash with no sentence behind it"
        # and the claim rule stays out of these parsers: see tests/test_claim_rule.py
        assert "claims" not in run and "claims_verified" not in run
