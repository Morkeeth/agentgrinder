import json
from agentgrinder.native_trace import codex_activity


def test_native_authorship_and_time_not_json_format(tmp_path):
    p=tmp_path/'native.jsonl'
    events=[('user_message',{'message':'go'}),('user_message',{'message':'<environment_context>injected'}),('function_call',{'call_id':'one'}),('function_call_output',{'call_id':'one'}),('user_message',{'message':'next'})]
    p.write_text('\n'.join(json.dumps({'type':'event_msg' if typ=='user_message' else 'response_item','timestamp':f'2026-09-04T10:00:{i*3:02d}Z','payload':dict(type=typ,**data)}) for i,(typ,data) in enumerate(events)))
    run=codex_activity(p)
    assert run['typed']==2 and run['tools']==1
    assert run['authorship']['injected']==1
    assert run['trace']==[{'second':0,'kind':'human'},{'second':6,'kind':'tool'},{'second':12,'kind':'human'}]


def test_delegated_task_not_human(tmp_path):
    p=tmp_path/'lane.jsonl'
    p.write_text('\n'.join(json.dumps(r) for r in [{'type':'session_meta','payload':{'source':{'subagent':{'parent':'p'}}}},{'type':'event_msg','payload':{'type':'user_message','message':'delegated task'}}]))
    assert codex_activity(p)['authorship']=={'human':0,'injected':0,'delegated':1}
