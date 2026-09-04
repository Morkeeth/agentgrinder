from agentgrinder.mcp_server import _handle


def test_mutating_tool_is_absent_without_explicit_credential(monkeypatch):
    monkeypatch.delenv('AGENTGRINDER_AGENT_TOKEN',raising=False)
    names=[t['name'] for t in _handle({'id':1,'method':'tools/list'})['result']['tools']]
    assert 'agent_action' not in names
    response=_handle({'id':2,'method':'tools/call','params':{'name':'agent_action','arguments':{'action':'draft','payload':{'turns_typed':2}}}})
    assert response['result']['isError']


def test_credential_enables_tool_without_exposing_secret(monkeypatch):
    monkeypatch.setenv('AGENTGRINDER_AGENT_TOKEN','fixture-credential')
    response=_handle({'id':1,'method':'tools/list'})
    assert 'agent_action' in [t['name'] for t in response['result']['tools']]
    assert 'fixture-credential' not in str(response)
