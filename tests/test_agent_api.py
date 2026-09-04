import json
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import pytest
from agentgrinder.agent_api import AgentClient,run_payload


def test_private_source_and_coach_prose_are_not_sent():
    payload=run_payload({'turns_typed':3,'source_path':'/private/transcript','coach_verdict':'private text','title':'Chosen title'})
    assert payload['visibility']=='private'
    assert 'private text' not in str(payload) and '/private' not in str(payload)


def test_network_client_sends_one_scoped_request_and_returns_no_credential():
    seen=[]
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            seen.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()
            self.wfile.write(b'{"id":"draft-id","action":"draft"}')
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        client=AgentClient('fixture-token',f'http://127.0.0.1:{server.server_port}')
        rid='00000000-0000-0000-0000-000000000001'
        result=client.perform('draft',run_payload({'turns_typed':2}),rid)
        assert len(seen)==1 and seen[0]['request_id']==rid and seen[0]['token']=='fixture-token'
        assert 'fixture-token' not in json.dumps(result)
    finally:server.shutdown();server.server_close();thread.join()


def test_credentials_never_travel_over_remote_plain_http():
    with pytest.raises(ValueError):AgentClient('fixture-token','http://example.com')
