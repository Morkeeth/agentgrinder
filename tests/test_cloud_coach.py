"""No network or paid inference: exercise trust boundaries before the spend seam."""
import json
from unittest.mock import Mock
import pytest
from cloud import coach_handler as c

USER='11111111-1111-4111-8111-111111111111'
PROFILE='22222222-2222-4222-8222-222222222222'
RUN='33333333-3333-4333-8333-333333333333'
AUTH='Bearer forged.but.wellformed_token'


def event(**fields):
    return {'requestContext':{'http':{'method':'POST'}}, 'headers':{'Authorization':AUTH},
            'body':json.dumps({'run_id':RUN,'consent_version':'metrics-v1',**fields})}


@pytest.fixture
def seams(monkeypatch):
    run={'id':RUN,'profile_id':PROFILE,'visibility':'private','measurement_revision':'a'*64,
         'prompts':3,'claims':2,'claims_verified':1,'artifacts_produced':None,'commits':0,
         'note':'PRIVATE NOTE MUST NEVER ENTER INFERENCE','title':'PRIVATE TITLE','harness':'claude'}
    def fetch(path, auth):
        assert auth == AUTH
        if path == '/auth/v1/user': return {'id':USER}
        if '/profiles?' in path: return [{'id':PROFILE}]
        assert path == '/rest/v1/runs?select='+','.join(c.COLUMNS)+'&id=eq.'+RUN+'&limit=1'
        return [run]
    monkeypatch.setattr(c,'supabase_get',fetch)
    reserve=Mock(); infer=Mock(return_value=({'title':'Try','instruction':'Inspect','expected':'Record','evidence_fields':['prompts']},2,2))
    monkeypatch.setattr(c,'reserve_quota',reserve);monkeypatch.setattr(c,'infer',infer)
    return run,reserve,infer


def test_owned_private_metrics_only(seams):
    run,reserve,infer=seams
    result=c.handler(event(goal='One smaller change'))
    assert result['statusCode']==200
    reserve.assert_called_once_with(USER)
    metrics,goal=infer.call_args.args
    assert set(metrics)==set(c.METRICS) and metrics['artifacts_produced'] is None
    assert goal=='One smaller change' and 'PRIVATE' not in json.dumps(metrics)
    body=json.loads(result['body'])
    assert body['run_id']==RUN and body['measurement_revision']=='a'*64
    assert 'recorded artifacts: unknown' in body['coach_verdict']
    assert body['requires_review'] is True


@pytest.mark.parametrize('fields',[{'run_id':'not-a-uuid'},{'surprise':'private data'},
    {'goal':'x'*401},{'goal':None},{'consent_version':'wrong'}])
def test_bad_request_never_spends(fields,seams):
    _,reserve,infer=seams
    assert c.handler(event(**fields))['statusCode']==400
    reserve.assert_not_called();infer.assert_not_called()


def test_forged_token_verified_remotely(monkeypatch,seams):
    _,reserve,infer=seams
    monkeypatch.setattr(c,'supabase_get',Mock(side_effect=ValueError('sensitive provider detail')))
    result=c.handler(event())
    assert result['statusCode']==401 and 'sensitive' not in result['body']
    reserve.assert_not_called();infer.assert_not_called()


@pytest.mark.parametrize('change',[{'visibility':'public'},{'visibility':'link'},
    {'profile_id':USER},{'measurement_revision':None},{'prompts':float('nan')},{'commits':True}])
def test_wrong_owner_or_unmeasured_never_spends(change,seams):
    run,reserve,infer=seams;run.update(change)
    assert c.handler(event())['statusCode']==403
    reserve.assert_not_called();infer.assert_not_called()


def test_quota_denial_prevents_inference(seams):
    _,reserve,infer=seams;reserve.side_effect=c.Rejected(429,'quota')
    assert c.handler(event())['statusCode']==429
    infer.assert_not_called()


def test_paid_failure_no_fallback_or_refund(seams):
    _,reserve,infer=seams;infer.side_effect=RuntimeError('secret')
    result=c.handler(event())
    assert result['statusCode']==502 and 'secret' not in result['body']
    assert 'reservation_consumed' in result['body'];reserve.assert_called_once();infer.assert_called_once()


def test_proposal_unknown_and_fabricated_evidence_rejected():
    p=c.Proposal({k:(3 if k=='prompts' else None) for k in c.METRICS})
    args=('Try smaller tasks','Record a smaller change','Compare observations')
    assert not p.propose(*args,['prompts'])['accepted']
    p.read_metrics()
    for fields in [['quality'],['claims_verified'],[],['prompts',{}]]:
        assert not p.propose(*args,fields)['accepted']
        assert p.value is None
    assert not p.propose('x'*161,*args[1:],['prompts'])['accepted']
    assert p.propose(*args,['prompts'])['accepted']


def test_atomic_quota_caps_and_fail_closed(monkeypatch):
    import boto3
    db=Mock();monkeypatch.setattr(boto3,'client',Mock(return_value=db))
    monkeypatch.setenv('COACH_QUOTA_TABLE','test-only-quota')
    c.reserve_quota(USER)
    ops=db.transact_write_items.call_args.kwargs['TransactItems']
    assert len(ops)==2
    assert [o['Update']['ExpressionAttributeValues'][':cap']['N'] for o in ops]==['10','2']
    assert all(o['Update']['ConditionExpression']=='attribute_not_exists(#n) OR #n < :cap' for o in ops)
    assert ops[1]['Update']['Key']['pk']['S'].startswith('user#'+USER+'#')
    db.transact_write_items.side_effect=RuntimeError('network unknown')
    with pytest.raises(c.Rejected) as e:c.reserve_quota(USER)
    assert e.value.status==429


def test_actual_model_wrapper_stops_before_fifth_request(monkeypatch):
    import asyncio
    import strands
    import strands.models
    bases=[]
    class FakeBedrock:
        def __init__(self,**kwargs): self.config=kwargs;bases.append(self)
        async def stream(self,*args,**kwargs): yield {'fake':True}
    class FakeAgent:
        def __init__(self,**kwargs):self.kwargs=kwargs
        def __call__(self,prompt):
            async def run():
                model=self.kwargs['model']
                with pytest.raises(RuntimeError):
                    async for _ in model.stream([{'content':'x'*16001}]):pass
                assert model.calls == 0
                for _ in range(4):
                    async for _ in model.stream([]):pass
                with pytest.raises(RuntimeError):
                    async for _ in model.stream([]):pass
            asyncio.run(run())
            self.kwargs['tools'][0]()
            self.kwargs['hooks'][0].after_tool(None)
            self.kwargs['tools'][1]('Try','Inspect','Record',['prompts'])
            self.kwargs['hooks'][0].after_tool(None)
    monkeypatch.setattr(strands.models,'BedrockModel',FakeBedrock)
    monkeypatch.setattr(strands,'Agent',FakeAgent)
    monkeypatch.setattr(strands,'tool',lambda f:f)
    monkeypatch.setenv('AWS_REGION','us-east-1')
    proposal,calls,tool_calls=c.infer({k:(3 if k=='prompts' else None) for k in c.METRICS},'')
    assert calls==4 and proposal['title']=='Try' and tool_calls==2
    assert bases[0].config['max_tokens']==1024
    assert bases[0].config['boto_client_config'].retries['total_max_attempts']==1
