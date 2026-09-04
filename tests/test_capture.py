import json
from agentgrinder.capture import connect, scan


def transcript(tmp_path):
    p = tmp_path/'session.jsonl'
    p.write_text(json.dumps({'type':'event_msg','timestamp':'2026-09-04T10:00:00Z','payload':{'type':'user_message','message':'go'}})+'\n')
    return p


def test_capture_dedup_pause_ignore_and_update(tmp_path):
    p=transcript(tmp_path)
    db=connect(tmp_path/'private')
    source=[('codex',p)]
    assert scan(db,source)['created']==1
    assert scan(db,source)['unchanged']==1
    with p.open('a') as f:
        f.write(json.dumps({'type':'response_item','timestamp':'2026-09-04T10:00:02Z','payload':{'type':'function_call','call_id':'c1','name':'test'}})+'\n')
    assert scan(db,source)['updated']==1
    assert db.execute('select count(*) from drafts').fetchone()[0]==1
    assert json.loads(db.execute('select payload from drafts').fetchone()[0])['tool_calls']==1
    db.execute("insert into settings values('paused','true')")
    assert scan(db,source)['paused']
    db.execute("update settings set value='false'")
    db.execute('insert into ignored values(?)',(str(tmp_path),))
    assert scan(db,source)['ignored']==1
    db.close()


def test_moving_transcript_does_not_create_false_snapshot(tmp_path,monkeypatch):
    from agentgrinder import capture
    p=transcript(tmp_path)
    original=capture.read_run
    def read(*args,**kwargs):
        run=original(*args,**kwargs)
        with p.open('a') as f:f.write('\n')
        return run
    monkeypatch.setattr(capture,'read_run',read)
    db=connect(tmp_path/'private')
    assert scan(db,[('codex',p)])['retry']==1
    assert db.execute('select count(*) from drafts').fetchone()[0]==0
    db.close()
