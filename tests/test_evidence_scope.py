import pytest
from agentgrinder.claims import Claim, evidence_matches


@pytest.mark.parametrize('claim,tokens,result',[
    ('test_login passed',{'test_login'},'FAILED test_login'),
    ('test_login passed',{'test_login'},'test_login FAILED, 3 passed'),
    ('I deployed the site',set(),'3 passed'),
    ('I wrote src/new.py',{'src/new.py'},'Read src/new.py'),
    ('test_login passed',{'test_login'},'test_login_extra PASSED'),
    ('Suite passes. Also the deploy is done.',set(),'5 passed'),
])
def test_unrelated_or_failed_result_never_proves_claim(claim,tokens,result):
    assert not evidence_matches(Claim(line=claim,tokens=tokens),result)


def test_named_passing_test_still_matches():
    assert evidence_matches(Claim(line='test_login passed',tokens={'test_login'}),'test_login PASSED')


def test_plain_suite_summary_can_match_a_suite_claim():
    assert evidence_matches(Claim(line='The suite passed',tokens=set()),'3 passed in 0.2s')
