"""A second rendering must not rewrite the history another comparison used."""
from agentgrinder.engine import log
from agentgrinder.engine.series import record_and_attach


def run(day, value):
    return dict(project="revision-probe", started=f"2026-09-{day:02d}T12:00:00Z",
                turns_typed=2, claims=3, claims_verified=value,
                artifacts_produced=0, commits=0)


def test_rerender_keeps_original_baseline_and_records_revision(tmp_path):
    path = str(tmp_path / "series.db")
    record_and_attach(run(1, 2), path=path)
    original = record_and_attach(run(2, 3), path=path)
    record_and_attach(run(1, 0), path=path)
    repeated = record_and_attach(run(2, 3), path=path)
    assert repeated["progress"]["previous_value"] == original["progress"]["previous_value"] == 1
    with log.connect(path) as conn:
        revisions = log.list_revisions(conn, "revision-probe", run(1, 0)["started"])
    assert [r["value"] for r in revisions] == [1, 0]
    assert len({r["revision_id"] for r in revisions}) == 2


def test_unmeasured_current_run_never_inherits_earlier_success(tmp_path):
    path = str(tmp_path / "series.db")
    record_and_attach(run(1, 1), path=path)
    record_and_attach(run(2, 3), path=path)
    result = record_and_attach(run(3, None), path=path)
    assert result["progress"]["verdict"] == "unmeasured"
    assert result["progress"]["value"] is None
    assert result["progress"]["delta"] is None
    assert "unmeasured" in result["progress_line"]


def test_identical_replay_is_idempotent(tmp_path):
    with log.connect(str(tmp_path / "series.db")) as conn:
        first = log.record_run(conn, run(1, 2))
        second = log.record_run(conn, run(1, 2))
        assert first["revision_id"] == second["revision_id"]
        assert len(log.list_revisions(conn, "revision-probe", run(1, 2)["started"])) == 1


def test_rule_change_creates_revision_even_when_count_is_same(tmp_path):
    with log.connect(str(tmp_path / "series.db")) as conn:
        first = log.record_run(conn, dict(run(1, 2), rule_version="one"))
        second = log.record_run(conn, dict(run(1, 2), rule_version="two"))
        assert first["revision_id"] != second["revision_id"]


def test_new_revision_compares_its_own_measurement(tmp_path):
    path = str(tmp_path / "series.db")
    record_and_attach(run(1, 1), path=path)
    record_and_attach(run(2, 2), path=path)
    changed = record_and_attach(run(2, 3), path=path)
    assert changed["progress"]["value"] == 1.5
    assert changed["progress"]["previous_value"] == 0.5
    assert changed["measurement"]["revision_id"]


def test_different_rules_do_not_create_an_improvement_claim(tmp_path):
    path = str(tmp_path / "series.db")
    record_and_attach(dict(run(1, 1), rule_version="old"), path=path)
    changed = record_and_attach(dict(run(2, 3), rule_version="new"), path=path)
    assert changed["progress"]["verdict"] == "incomparable"
    assert changed["progress"]["delta"] is None


def test_same_project_name_does_not_join_different_repositories(tmp_path):
    from agentgrinder.engine import log
    db=log.connect(str(tmp_path/'history.db'))
    first={'project':'app','project_identity':'repo-one','started':'2026-09-01T10:00:00Z','turns_typed':2,'claims_verified':1,'artifacts_produced':1}
    a=log.record_run(db,first)
    b=log.record_run(db,dict(first,project_identity='repo-two',started='2026-09-02T10:00:00Z'))
    assert b['baseline_revision_id'] is None
    c=log.record_run(db,dict(first,started='2026-09-03T10:00:00Z'))
    assert c['baseline_revision_id']==a['revision_id']
    db.close()
