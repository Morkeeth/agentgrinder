"""The coach agent: a real Strands loop, keyless by default, never a number a tool did not return.

Pattern lifted from MAGNET's tests/test_agent_loop.py (same author, disclosed in the README):
assert the SDK dispatched the tools, assert local mode never constructs a BedrockModel or opens
an internet socket, assert the mode is printed and a failing mode shouts DEGRADED.
"""
import json
import os
import socket
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

strands = pytest.importorskip("strands")   # the coach is the [coach] extra; the base suite runs without it
from strands import Agent  # noqa: E402

from agentgrinder.coach import agent as coach_agent  # noqa: E402
from agentgrinder.coach.agent import MODES, create_coach, run_coach  # noqa: E402
from agentgrinder.coach.local_model import ScriptedLocalModel, history_of  # noqa: E402
from agentgrinder.coach.tools import CoachContext, TOOL_NAMES  # noqa: E402
from tests.test_coach_tools import _sitting  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(REPO, "samples", "sample_session.jsonl")


def _tool_results(agent):
    return [b["toolResult"] for m in agent.messages for b in m.get("content", []) if "toolResult" in b]


def test_create_coach_is_a_real_strands_agent_with_the_five_tools(tmp_path):
    path, _, _ = _sitting(tmp_path)
    agent = create_coach(CoachContext(path), model=ScriptedLocalModel())
    assert isinstance(agent, Agent)
    assert sorted(agent.tool_names) == sorted(TOOL_NAMES)


def test_the_sdk_event_loop_dispatches_every_tool_and_the_hook_logs_each(tmp_path):
    path, _, _ = _sitting(tmp_path)
    ctx = CoachContext(path)
    agent = create_coach(ctx, model=ScriptedLocalModel())
    agent("referee it")
    dispatched = coach_agent.dispatched(agent)
    # 2 claims, 2 artifacts, no git tree: read, 2 checks, 2 verifies, verdict
    assert dispatched == ["read_run", "check_claim", "check_claim", "verify_artifact", "verify_artifact",
                          "write_verdict"]
    results = _tool_results(agent)
    assert len(results) == 6 and all(r["status"] == "success" for r in results)
    # the AfterToolCallEvent hook saw the same six, in the same order
    assert [d["tool"] for d in ctx.dispatch] == dispatched
    assert all(d["source"] == "strands AfterToolCallEvent" for d in ctx.dispatch)


def test_verdict_numbers_equal_the_tool_results_not_the_plan(tmp_path):
    path, _, _ = _sitting(tmp_path)
    ctx = CoachContext(path)
    agent = create_coach(ctx, model=ScriptedLocalModel())
    agent("referee it")
    hist = history_of(agent.messages)
    checks = [r for n, _, r in hist if n == "check_claim"]
    exists = [r for n, _, r in hist if n == "verify_artifact"]
    rr = next(r for n, _, r in hist if n == "read_run")
    verdict = next(r for n, _, r in hist if n == "write_verdict")
    assert verdict["accepted"] is True
    n = verdict["verdict"]["numbers"]
    assert n["claims"] == len(rr["claims"]) == 2
    assert n["claims_verified"] == sum(1 for c in checks if c["verified"]) == 1
    assert n["artifacts_produced"] == sum(1 for e in exists if e["exists"]) == 1
    assert n["turns_typed"] == rr["turns_typed"] == 2
    assert n["commits"] == rr["commits"] == 0
    # and the same numbers the card computed by rule
    assert ctx.run["claims"] == 2 and ctx.run["claims_verified"] == 1 and ctx.run["artifacts_produced"] == 1
    assert verdict["verdict"]["matches_card"] is True


def test_a_policy_that_lies_is_refused_by_write_verdict(tmp_path):
    """If the model writes 2 verified when the tools said 1, the tool refuses and the loop ends
    on the refusal. The card gets no verdict rather than a wrong one."""
    from agentgrinder.coach.policy import coach_policy

    def liar(history):
        step = coach_policy(history)
        if step and step[0] == "write_verdict":
            step[1]["claims_verified"] = step[1]["claims_verified"] + 1
        return step

    path, _, _ = _sitting(tmp_path)
    ctx = CoachContext(path)
    agent = create_coach(ctx, model=ScriptedLocalModel(policy=liar))
    out = agent("referee it")
    verdict = next(r for n, _, r in history_of(agent.messages) if n == "write_verdict")
    assert verdict["accepted"] is False
    assert verdict["reasons"] == ["claims_verified: you wrote 2, the tools returned 1"]
    assert ctx.verdict is None
    assert "refused" in str(out)


def test_local_mode_report_says_what_it_is_and_is_not(tmp_path):
    path, _, _ = _sitting(tmp_path)
    ctx, text = run_coach(path, mode="local")
    assert "strands agent loop" in text and "local scripted model" in text
    assert "tools dispatched     6" in text and "hook logged 6" in text
    assert "not an LLM" in text
    assert "DEGRADED" not in text
    assert ctx.run["coach_tool_calls"] == 6
    assert ctx.run["coach_verdict"].startswith("1 of 2 claims had evidence")
    assert "Claims [2] had no evidence" in ctx.run["coach_plan"]
    assert ctx.run["coach_numbers"]["claims_verified"] == 1
    # the report carries no typed prompt and no absolute path
    assert "please fix it" not in text and str(tmp_path) not in text


def test_none_mode_is_labelled_as_not_an_agent(tmp_path):
    path, _, _ = _sitting(tmp_path)
    ctx, text = run_coach(path, mode="none")
    assert "deterministic fallback" in text and "no agent, no model" in text
    assert "strands agent loop" not in text
    assert ctx.verdict is not None and ctx.verdict["numbers"]["claims_verified"] == 1
    assert all(d["source"] == "direct call, no agent" for d in ctx.dispatch)


def test_a_failing_agent_mode_shouts_degraded(tmp_path, monkeypatch):
    def boom(ctx, mode):
        raise RuntimeError("no credentials")

    monkeypatch.setattr(coach_agent, "run_strands_coach", boom)
    path, _, _ = _sitting(tmp_path)
    printed = []
    ctx, text = run_coach(path, mode="bedrock", out=printed.append)
    assert "FAILED" in text and "DEGRADED" in text and "RuntimeError: no credentials" in text
    assert "deterministic fallback" in text
    assert printed and "BEDROCK" in printed[0]      # the banner printed before the attempt


def test_unknown_mode_is_rejected(tmp_path):
    path, _, _ = _sitting(tmp_path)
    with pytest.raises(ValueError):
        run_coach(path, mode="totally-not-a-mode")
    assert MODES == ("local", "bedrock", "none")


def test_keyless_path_never_constructs_a_bedrock_model(tmp_path, monkeypatch):
    import strands.models
    import strands.models.bedrock

    def boom(*a, **k):
        raise AssertionError("local mode constructed a BedrockModel, possible spend")

    monkeypatch.setattr(strands.models, "BedrockModel", boom)
    monkeypatch.setattr(strands.models.bedrock, "BedrockModel", boom)
    path, _, _ = _sitting(tmp_path)
    ctx, text = run_coach(path, mode="local")
    assert "tools dispatched     6" in text and "DEGRADED" not in text


def test_keyless_path_opens_no_internet_socket(tmp_path, monkeypatch):
    path, _, _ = _sitting(tmp_path)
    run_coach(path, mode="local")            # warm imports first; this measures the RUN
    opened = []
    real = socket.socket

    class Watched(real):
        def __init__(self, *a, **k):
            opened.append(a)
            super().__init__(*a, **k)

    monkeypatch.setattr(socket, "socket", Watched)
    ctx, text = run_coach(path, mode="local")
    assert "DEGRADED" not in text
    internet = [a for a in opened if a and a[0] in (socket.AF_INET, socket.AF_INET6)]
    assert internet == [], f"local mode opened internet socket(s): {internet}"


def test_agent_module_has_no_top_level_bedrock_or_boto_import():
    src = open(coach_agent.__file__).read()
    assert "import boto3" not in src and "BedrockModel" not in src.split('"""', 2)[2].replace("BEDROCK_LABEL", "")


def test_cli_coach_on_the_bundled_fixture_is_keyless_and_exits_zero():
    proc = subprocess.run([sys.executable, "-m", "agentgrinder", "coach", "samples/sample_session.jsonl"],
                          cwd=REPO, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "strands agent loop" in proc.stdout
    assert "tools dispatched     8" in proc.stdout          # 1 read + 2 checks + 2 verifies + 2 git + 1 verdict
    assert "1 verified of 2" in proc.stdout
    assert "1 on disk of 2 written" in proc.stdout
    assert "[fixture]" not in proc.stdout                    # the typed prompts never print
    assert "DEGRADED" not in proc.stdout


def test_cli_grind_coach_json_carries_the_verdict_fields(tmp_path):
    env = dict(os.environ, AGENTGRINDER_SERIES=str(tmp_path / "series.db"))   # never the real series
    proc = subprocess.run([sys.executable, "-m", "agentgrinder", "grind", "samples/sample_session.jsonl",
                           "--coach", "--json"], cwd=REPO, capture_output=True, text=True, env=env)
    assert proc.returncode == 0, proc.stderr
    run = json.loads(proc.stdout)
    assert run["coach_tool_calls"] == 8
    assert run["coach_numbers"] == dict(turns_typed=3, claims=2, claims_verified=1, artifacts_produced=1, commits=0)
    assert run["coach_verdict"] and run["coach_plan"]
    assert "strands agent loop" in run["coach_mode"]
    # the project label is the checkout's own directory name, not the literal "agentgrinder": a
    # clone into any other folder used to red this one test and nothing else, so a contributor's
    # first `pytest` was 60 passed, 1 failed. Measured 3 Sep 2026 in ./clone1.
    assert run["progress"]["verdict"] == "baseline"
    assert f"baseline on {os.path.basename(REPO)}" in run["progress_line"]
