"""Codex support pointed at a directory Codex does not write to.

Measured 3 Sep 2026 on the author's machine: the shipped glob,
`~/.codex/archived_sessions/*.jsonl`, found 16 files. `~/.codex/sessions/**/*.jsonl`, where Codex
CLI actually writes live sessions, held 64. A person who has just started with Codex has nothing
archived at all, so `grind`, `grind --harness codex`, `grind --harness auto` and `flex` all
answered "nothing to read" while their whole history sat on disk.

These tests run against a fixture HOME, so they measure the reader, not this machine.
"""
import os

from agentgrinder import ingest
from agentgrinder.ingest import CODEX_GLOBS, codex_session_files, latest_codex_session

LINE = ('{"type":"session_meta","payload":{"cwd":"/tmp/proj"}}\n'
        '{"type":"user_message","content":"do the thing"}\n'
        '{"role":"assistant","content":[{"type":"tool_use"}]}\n')


def _codex_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(os.path, "expanduser", lambda p: p.replace("~", str(tmp_path), 1))
    return tmp_path


def test_both_trees_are_searched_and_the_live_one_is_named_first():
    assert "~/.codex/sessions/**/*.jsonl" in CODEX_GLOBS
    assert "~/.codex/archived_sessions/*.jsonl" in CODEX_GLOBS


def test_a_session_nested_by_date_is_found_which_the_old_flat_glob_could_never_do(tmp_path, monkeypatch):
    home = _codex_home(tmp_path, monkeypatch)
    live = home / ".codex" / "sessions" / "2026" / "09" / "03"
    live.mkdir(parents=True)
    (live / "rollout-2026-09-03T10-00-00.jsonl").write_text(LINE, encoding="utf-8")
    found = codex_session_files()
    assert len(found) == 1
    assert found[0].endswith("rollout-2026-09-03T10-00-00.jsonl")
    assert latest_codex_session() == found[0]


def test_archived_sessions_still_count_and_neither_tree_is_listed_twice(tmp_path, monkeypatch):
    home = _codex_home(tmp_path, monkeypatch)
    live = home / ".codex" / "sessions" / "2026" / "09" / "03"
    live.mkdir(parents=True)
    (live / "a.jsonl").write_text(LINE, encoding="utf-8")
    arch = home / ".codex" / "archived_sessions"
    arch.mkdir(parents=True)
    (arch / "b.jsonl").write_text(LINE, encoding="utf-8")
    found = codex_session_files()
    assert len(found) == 2 and len(set(found)) == 2


def test_a_fresh_codex_user_with_only_live_sessions_gets_a_parsed_run(tmp_path, monkeypatch):
    """The whole point: no archived_sessions directory at all, and it still reads."""
    home = _codex_home(tmp_path, monkeypatch)
    live = home / ".codex" / "sessions" / "2026" / "09" / "03"
    live.mkdir(parents=True)
    (live / "rollout.jsonl").write_text(LINE, encoding="utf-8")
    assert not (home / ".codex" / "archived_sessions").exists()
    run = ingest.parse_codex_session(latest_codex_session())
    assert run["harness"] == "Codex" and run["turns_typed"] == 1
    assert run["claims"] is not None and run["claims_verified"] is not None
    assert run["artifacts_produced"] is None
    assert "Write/Edit" in (run.get("produced_reason") or "")


def test_no_codex_at_all_is_an_empty_list_not_a_crash(tmp_path, monkeypatch):
    _codex_home(tmp_path, monkeypatch)
    assert codex_session_files() == []
    assert latest_codex_session() is None
