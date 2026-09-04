import pytest
from agentgrinder.contract import validate_run
from agentgrinder.push import export_run


def test_legacy_runs_remain_readable_without_inventing_missing_counts():
    exported = export_run({"turns_typed": 3})
    assert exported["schema_version"] == 1
    assert "claims_verified" not in exported


@pytest.mark.parametrize("run", [{"schema_version": 2}, {"claims": True},
                                 {"commits": -1}, {"claims": 1, "claims_verified": 2},
                                 {"claims_verified": 1}, {"claims": None, "claims_verified": 0},
                                 {"duration_s": float("nan")}])
def test_bad_imports_are_rejected(run):
    with pytest.raises(ValueError):
        validate_run(run)


def test_only_revision_references_leave_local_measurement():
    exported = export_run({"turns_typed": 2, "measurement": {
        "revision_id": "a" * 64, "baseline_revision_id": "b" * 64,
        "command": "private-command", "input_digest": "private-digest", "project": "/private/repo"}})
    assert exported["measurement_revision"] == "a" * 64
    assert exported["baseline_revision"] == "b" * 64
    assert "private" not in str(exported)


def test_reexport_preserves_frozen_references():
    from agentgrinder.push import export_run
    original={'schema_version':1,'turns_typed':2,'measurement_revision':'a'*64,'baseline_revision':'b'*64}
    assert export_run(original)['measurement_revision']==original['measurement_revision']
    assert export_run(original)['baseline_revision']==original['baseline_revision']
