"""The per-project series: baseline under two readings, helped/hurt after, predictions consumed."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentgrinder.engine import log
from agentgrinder.engine.reporter import progress, progress_line, verdict
from agentgrinder.engine.series import record_and_attach


def _run(started, verified, produced, typed, project="p"):
    return dict(project=project, started=started, turns_typed=typed, claims=verified + 1,
                claims_verified=verified, artifacts_produced=produced, commits=1)


def test_one_reading_is_a_baseline_never_a_trend(tmp_path):
    db = str(tmp_path / "s.db")
    run = record_and_attach(_run("2026-09-01T10:00:00+02:00", 1, 1, 2), path=db)
    assert run["progress"]["verdict"] == "baseline" and run["progress"]["delta"] is None
    assert run["progress"]["runs_on_project"] == 1
    assert "baseline on p" in run["progress_line"] and "first grind" in run["progress_line"]


def test_second_reading_gives_helped_or_hurt_by_verified_per_turn(tmp_path):
    db = str(tmp_path / "s.db")
    record_and_attach(_run("2026-09-01T10:00:00+02:00", 1, 1, 4), path=db)         # 0.50
    run = record_and_attach(_run("2026-09-02T10:00:00+02:00", 2, 2, 4), path=db)   # 1.00
    p = run["progress"]
    assert p["verdict"] == "helped" and p["delta"] == 0.5
    assert p["previous_value"] == 0.5 and p["value"] == 1.0 and p["runs_on_project"] == 2
    assert "helped vs your last grind on p" in run["progress_line"]
    assert "+0.50 (0.50 -> 1.00)" in run["progress_line"]
    run = record_and_attach(_run("2026-09-03T10:00:00+02:00", 0, 1, 4), path=db)   # 0.25
    assert run["progress"]["verdict"] == "hurt" and run["progress"]["delta"] == -0.75
    run = record_and_attach(_run("2026-09-04T10:00:00+02:00", 0, 1, 4), path=db)   # 0.25 again
    assert run["progress"]["verdict"] == "unchanged" and run["progress"]["delta"] == 0.0


def test_unmeasured_reading_is_null_and_does_not_count(tmp_path):
    db = str(tmp_path / "s.db")
    record_and_attach(_run("2026-09-01T10:00:00+02:00", 1, 1, 4), path=db)
    nohead = dict(project="p", started="2026-09-02T10:00:00+02:00", turns_typed=3, commits=0,
                  claims=None, claims_verified=None, artifacts_produced=None)
    run = record_and_attach(nohead, path=db)
    assert run["progress"]["verdict"] == "unmeasured"
    conn = log.connect(db)
    rows = log.list_readings(conn, "p")
    assert len(rows) == 2 and rows[1]["value"] is None
    # a later measured run compares with the last MEASURED one, skipping the null
    run = record_and_attach(_run("2026-09-03T10:00:00+02:00", 2, 2, 4), path=db)
    assert run["progress"]["verdict"] == "helped" and run["progress"]["previous_started"] == "2026-09-01T10:00:00+02:00"


def test_redrawing_the_same_sitting_replaces_its_row_and_compares_backwards(tmp_path):
    db = str(tmp_path / "s.db")
    record_and_attach(_run("2026-09-01T10:00:00+02:00", 1, 1, 4), path=db)
    record_and_attach(_run("2026-09-02T10:00:00+02:00", 2, 2, 4), path=db)
    # drawing the FIRST sitting again: still one row for it, still a baseline (nothing before it)
    run = record_and_attach(_run("2026-09-01T10:00:00+02:00", 1, 1, 4), path=db)
    assert run["progress"]["verdict"] == "baseline"
    assert len(log.list_readings(log.connect(db), "p")) == 2


def test_projects_do_not_mix(tmp_path):
    db = str(tmp_path / "s.db")
    record_and_attach(_run("2026-09-01T10:00:00+02:00", 1, 1, 4, project="a"), path=db)
    run = record_and_attach(_run("2026-09-02T10:00:00+02:00", 2, 2, 4, project="b"), path=db)
    assert run["progress"]["verdict"] == "baseline"


def test_prediction_is_consumed_by_the_next_grind_on_that_project(tmp_path):
    db = str(tmp_path / "s.db")
    conn = log.connect(db)
    log.predict(conn, "p", "ships 2 files")
    conn.close()
    run = record_and_attach(_run("2026-12-01T10:00:00+02:00", 1, 1, 2), path=db)
    assert run["progress"]["prediction"] == "ships 2 files"
    again = record_and_attach(_run("2026-12-02T10:00:00+02:00", 1, 1, 2), path=db)
    assert again["progress"]["prediction"] is None        # consumed once
    with pytest.raises(ValueError):
        log.predict(log.connect(db), "p", "   ")


def test_verdict_rule_direct():
    rs = [dict(started="1", value=0.5), dict(started="2", value=None), dict(started="3", value=0.75)]
    assert verdict(rs) == ("helped", 0.25)
    assert verdict(rs, at="2") == ("unmeasured", None)
    assert verdict(rs, direction="down") == ("hurt", 0.25)
    assert progress_line(None, "p") == ""
    p = progress(rs, dict(started="3"))
    assert p["previous_started"] == "1" and p["runs_on_project"] == 3
