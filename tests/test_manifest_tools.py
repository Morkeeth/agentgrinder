"""The agent surface must not describe a server that does not exist.

Three defects from the 3 Sep 2026 cold audit, pinned here:

1. `.well-known/agent-grinder.json` listed 8 tools; the server registers 11. `a2a_flex`,
   `a2a_roast` and `a2a_rig_preview` were callable but undeclared, and `a2a.py` tells the agent
   in its onboarding to call `a2a_flex`, which the manifest did not name.
2. `list_sessions` returned absolute paths, home directory and project directory included, while
   the onboarding the agent reads first says "NEVER include prompt text, code, or file paths in
   A2A payloads". The second tool in the list broke the rule stated by the first.
3. The MCP harness enum was ["claude","cursor"] in all three places while the CLI accepted codex.
"""
import json
import os
import re
import subprocess
import sys

from agentgrinder import mcp_server
from agentgrinder.mcp_server import TOOLS, list_sessions

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO, "site", ".well-known", "agent-grinder.json")


def test_the_manifest_lists_exactly_the_tools_the_server_registers():
    declared = json.load(open(MANIFEST, encoding="utf-8"))["mcp"]["tools"]
    registered = [t["name"] for t in TOOLS]
    assert sorted(declared) == sorted(registered), (
        f"undeclared: {sorted(set(registered) - set(declared))} · "
        f"declared but absent: {sorted(set(declared) - set(registered))}")


def test_every_declared_tool_is_actually_dispatchable():
    """A name in the manifest that tools/call cannot route is worse than one that is missing."""
    src = open(os.path.join(REPO, "agentgrinder", "mcp_server.py"), encoding="utf-8").read()
    routed = set(re.findall(r'name == "([a-z0-9_]+)"', src))
    for t in TOOLS:
        assert t["name"] in routed, t["name"]


def test_every_tool_the_onboarding_tells_the_agent_to_call_is_declared():
    """a2a.py told the agent to `call a2a_flex`, which the manifest did not name."""
    from agentgrinder.a2a import ONBOARDING
    declared = set(json.load(open(MANIFEST, encoding="utf-8"))["mcp"]["tools"])
    called = set()
    for a, b in re.findall(r"call `([a-z0-9_]+)`(?: or `([a-z0-9_]+)`)?", ONBOARDING):
        called.add(a)
        if b:
            called.add(b)
    assert called, "the onboarding stopped naming any tool to call"
    for name in sorted(called):
        assert name in declared, f"{name} is named in the onboarding but not in the manifest"


def test_list_sessions_returns_no_path(tmp_path, monkeypatch):
    """The rule the onboarding states, tested against the tool that used to break it."""
    home = tmp_path / "home"
    d = home / ".cursor" / "projects" / "Users-alice-secret-client-work" / "agent-transcripts" / "a"
    d.mkdir(parents=True)
    (d / "t.jsonl").write_text(
        '{"role":"user","message":{"content":"<user_query>hi</user_query>"}}\n', encoding="utf-8")
    monkeypatch.setattr(os.path, "expanduser", lambda p: p.replace("~", str(home), 1))
    out = list_sessions()
    assert "t.jsonl" in out and "Cursor" in out
    assert str(home) not in out
    assert "/Users/" not in out and "secret-client-work" not in out
    assert not re.search(r"(^|\s)/[\w./-]{6,}", out), out   # no absolute path anywhere in it


def test_list_sessions_with_nothing_says_where_it_looked(tmp_path, monkeypatch):
    monkeypatch.setattr(os.path, "expanduser", lambda p: p.replace("~", str(tmp_path), 1))
    out = list_sessions()
    assert "~/.codex/sessions/**/*.jsonl" in out and "~/.claude/projects" in out


def test_the_mcp_harness_enum_matches_what_the_cli_reads():
    for t in TOOLS:
        enum = ((t.get("inputSchema") or {}).get("properties") or {}).get("harness", {}).get("enum")
        if enum:
            assert "codex" in enum, t["name"]


def test_the_server_still_answers_over_stdio_with_the_declared_count():
    """Drive it the way an agent does: initialize, then tools/list, over a pipe."""
    msgs = "\n".join([
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
    ]) + "\n"
    proc = subprocess.run([sys.executable, "-m", "agentgrinder.mcp_server"],
                          input=msgs, capture_output=True, text=True, cwd=REPO)
    lines = [json.loads(l) for l in proc.stdout.strip().splitlines() if l.strip()]
    listed = [r for r in lines if r.get("id") == 2][0]["result"]["tools"]
    declared = json.load(open(MANIFEST, encoding="utf-8"))["mcp"]["tools"]
    assert sorted(t["name"] for t in listed) == sorted(declared)
