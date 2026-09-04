from agentgrinder.coach.native import review_activity


def test_activity_coach_preserves_unknowns_and_uses_actual_dispatch():
    import pytest
    pytest.importorskip('strands')
    run={'harness':'Codex','turns_typed':2,'tool_calls':3,'claims':None,'claims_verified':None}
    text=review_activity(run)
    assert run['coach_tool_calls']==2
    assert run['coach_numbers']['claims_verified'] is None
    assert 'unavailable' in text
    assert run['claims_verified'] is None


def test_direct_mode_is_explicit():
    run={'harness':'Cursor','turns_typed':3,'tool_calls':4}
    text=review_activity(run,'none')
    assert 'no agent or model' in text
    assert run['coach_numbers']['artifacts_produced'] is None


def test_private_practice_cannot_escape_through_coach_prose():
    from agentgrinder.push import export_run
    run={'harness':'Cursor','turns_typed':2,'tool_calls':3,'practice_context':[{'title':'PRIVATE_FIXTURE_INTENTION'}]}
    review_activity(run,'none')
    assert 'PRIVATE_FIXTURE_INTENTION' in run['private_coach_plan']
    assert 'PRIVATE_FIXTURE_INTENTION' not in str(export_run(run))
