import pytest
from agentgrinder import practices
from agentgrinder.engine import log
from agentgrinder.push import export_run


def measurement(conn,project='example'):
    return log.record_run(conn,dict(project=project,started='2026-09-04T10:00:00Z',turns_typed=2,
                                   claims=2,claims_verified=1,artifacts_produced=1))


def test_accept_attempt_review_survives_reopen_and_remains_private(tmp_path):
    path=str(tmp_path/'db.sqlite')
    with log.connect(path) as conn:
        revision=measurement(conn)
        practice=practices.accept(conn,'example','Run the named test before claiming success','Fewer unchecked claims',revision['revision_id'])
        attempt=practices.attach_attempt(conn,practice['id'],revision['revision_id'])
        assert attempt['tried']=='unknown' and attempt['outcome'] is None
        assert practices.attach_attempt(conn,practice['id'],revision['revision_id'])['id']==attempt['id']
        practices.review(conn,attempt['id'],'yes','keep','The check caught a failing case.')
    with log.connect(path) as conn:
        items=practices.context(conn,'example')
        assert items[0]['attempts'][0]['outcome']=='keep'
        assert items[0]['source_revision']==revision['revision_id']
    assert 'practice_context' not in export_run({'turns_typed':2,'practice_context':items})


def test_cross_project_evidence_and_untried_success_are_rejected(tmp_path):
    with log.connect(str(tmp_path/'db.sqlite')) as conn:
        revision=measurement(conn)
        with pytest.raises(ValueError):practices.accept(conn,'different','Try it',source_revision=revision['revision_id'])
        practice=practices.accept(conn,'example','Try it')
        attempt=practices.attach_attempt(conn,practice['id'],revision['revision_id'])
        with pytest.raises(ValueError):practices.review(conn,attempt['id'],'no','keep')
        practices.review(conn,attempt['id'],'no','incomparable')
        practices.dismiss(conn,practice['id'])
        assert practices.list_practices(conn)==[]
