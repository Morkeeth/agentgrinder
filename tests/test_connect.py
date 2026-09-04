import json
import os
import subprocess
from pathlib import Path
from agentgrinder.cli import main
from test_native_sittings import resumed


def test_installed_connection_runs_real_stdio_from_another_directory(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    sessions = home / '.codex/sessions'
    sessions.mkdir(parents=True)
    source = resumed(tmp_path)
    (sessions / 'rollout-fixture.jsonl').write_text(source.read_text())
    project = tmp_path / 'project'
    target = project / '.cursor/mcp.json'
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps({'mcpServers': {'other': {'command': 'existing'}}}))
    assert main(['connect', 'cursor', '--project', str(project), '--install']) == 0
    config = json.loads(target.read_text())
    assert config['mcpServers']['other']['command'] == 'existing'
    server = config['mcpServers']['agentgrinder']
    messages = [
        {'jsonrpc':'2.0','id':1,'method':'initialize'},
        {'jsonrpc':'2.0','id':2,'method':'tools/list'},
        {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'preview_run','arguments':{'harness':'codex'}}},
    ]
    env = dict(os.environ, HOME=str(home))
    env.pop('AGENTGRINDER_AGENT_TOKEN', None)
    result = subprocess.run([server['command'], *server['args']], cwd=tmp_path,
        env=env, input='\n'.join(map(json.dumps,messages))+'\n', text=True, capture_output=True, check=True)
    replies = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(replies) == 3
    assert not replies[2]['result']['isError']
    text = replies[2]['result']['content'][0]['text']
    assert '"duration_s": 120' in text
    assert str(tmp_path) not in text
    assert '"project"' not in text
    assert 'agent_action' not in str(replies[1])


def test_connection_refuses_to_replace_an_existing_definition(tmp_path):
    target=tmp_path/'.mcp.json'
    original='{"mcpServers":{"agentgrinder":{"command":"custom"}}}'
    target.write_text(original)
    assert main(['connect','claude','--project',str(tmp_path),'--install']) == 1
    assert target.read_text() == original
