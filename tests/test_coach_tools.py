"""The five coach tools, on fixture runs. No Strands needed here: these are the plain functions.

The point under test is the refusal: `write_verdict` accepts a number only when a tool in the
same context returned it. A coach that could write 9 verified claims after checking 3 would be
the regex it replaced, with a model's voice.
"""
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentgrinder.coach.tools import (CoachContext, TOOL_NAMES, attach, check_claim,
                                      git_evidence, read_run, verify_artifact, write_verdict)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(REPO, "samples", "sample_session.jsonl")


def _rec(typ, content, ts, cwd, **kw):
    o = {"type": typ, "timestamp": ts, "cwd": cwd, "message": {"role": typ, "content": content}}
    o.update(kw)
    return o


def _sitting(tmp_path, cwd=None):
    """Two typed turns. Turn 1: a Write that lands and a claim with a passing result. Turn 2: a
    Write that never lands, a claim naming a test nothing ran."""
    cwd = cwd or str(tmp_path)
    made = os.path.join(cwd, "out.md")
    with open(made, "w") as fh:
        fh.write("x")
    never = os.path.join(cwd, "never.md")
    lines = [
        _rec("user", "please fix it", "2026-09-03T10:00:00Z", cwd, promptSource="typed"),
        _rec("assistant", [{"type": "tool_use", "name": "Write", "input": {"file_path": made}}],
             "2026-09-03T10:00:10Z", cwd),
        _rec("user", [{"type": "tool_result", "content": "3 passed in 0.2s"}], "2026-09-03T10:00:20Z", cwd),
        _rec("assistant", [{"type": "text", "text": f"Suite passes, fixed {made}."}], "2026-09-03T10:00:30Z", cwd),
        _rec("user", "and the other thing", "2026-09-03T10:04:00Z", cwd, promptSource="typed"),
        _rec("assistant", [{"type": "tool_use", "name": "Write", "input": {"file_path": never}}],
             "2026-09-03T10:04:10Z", cwd),
        _rec("user", [{"type": "tool_result", "content": "ok"}], "2026-09-03T10:04:12Z", cwd),
        _rec("assistant", [{"type": "text", "text": "Done, test_never_ran passes."}], "2026-09-03T10:05:00Z", cwd),
    ]
    p = tmp_path / "s.jsonl"
    p.write_text("\n".join(json.dumps(x) for x in lines) + "\n")
    return str(p), made, never


def test_tool_names_are_the_five():
    assert TOOL_NAMES == ("read_run", "check_claim", "verify_artifact", "git_evidence", "write_verdict")


def test_read_run_returns_counts_and_claim_lines_never_prompt_text(tmp_path):
    path, made, never = _sitting(tmp_path)
    ctx = CoachContext(path)
    r = read_run(ctx)
    assert r["turns_typed"] == 2 and r["files_edited"] == 2 and r["commits"] == 0
    assert [c["id"] for c in r["claims"]] == [1, 2]
    assert r["claims"][0]["turn"] == 1 and r["claims"][1]["turn"] == 2
    assert r["results_per_turn"] == {"1": 1, "2": 1}
    blob = json.dumps(r)
    assert "please fix it" not in blob and "the other thing" not in blob   # typed prompts
    assert str(tmp_path) not in blob                                          # absolute paths
    assert r["in_git"] is False


def test_check_claim_is_the_same_turn_rule(tmp_path):
    path, made, never = _sitting(tmp_path)
    ctx = CoachContext(path)
    read_run(ctx)
    one = check_claim(ctx, 1)
    two = check_claim(ctx, 2)
    assert one["verified"] is True and "3 passed" in one["evidence"]
    assert two["verified"] is False and two["evidence"] is None and two["results_in_turn"] == 1
    assert "error" in check_claim(ctx, 99)


def test_verify_artifact_reports_disk_not_transcript(tmp_path):
    path, made, never = _sitting(tmp_path)
    ctx = CoachContext(path)
    read_run(ctx)
    a = verify_artifact(ctx, 1)
    b = verify_artifact(ctx, 2)
    assert a["exists"] is True and a["size"] == 1 and a["modified_in_window"] is False
    assert b["exists"] is False
    assert str(tmp_path) not in json.dumps([a, b])


def test_git_evidence_outside_a_work_tree_says_why(tmp_path):
    path, made, never = _sitting(tmp_path)
    ctx = CoachContext(path)
    read_run(ctx)
    g = git_evidence(ctx, 1)
    assert g["asked"] is False and "not inside a git work tree" in g["reason"]


def test_git_evidence_finds_the_commit_inside_the_window(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    path, made, never = _sitting(tmp_path, cwd=str(repo))
    env = dict(os.environ, GIT_AUTHOR_DATE="2026-09-03T10:02:00Z", GIT_COMMITTER_DATE="2026-09-03T10:02:00Z",
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x")
    subprocess.run(["git", "-C", str(repo), "add", "out.md"], check=True, env=env)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "land out.md"], check=True, env=env)
    ctx = CoachContext(path)
    r = read_run(ctx)
    assert r["in_git"] is True and r["commits"] == 1
    g = git_evidence(ctx, 1)
    assert g["asked"] is True and len(g["in_window"]) == 1
    assert g["in_window"][0]["subject"] == "land out.md"
    assert str(repo) not in json.dumps(g)
    g2 = git_evidence(ctx, 2)
    assert g2["in_window"] == [] and g2["committed_later"] is None


def test_write_verdict_refuses_until_every_claim_and_artifact_was_checked(tmp_path):
    path, made, never = _sitting(tmp_path)
    ctx = CoachContext(path)
    r = write_verdict(ctx, 2, 2, 2, 2, 0, "looks great", ["ship"])
    assert r["accepted"] is False
    assert any("read_run was not called" in x for x in r["reasons"])
    read_run(ctx)
    check_claim(ctx, 1)
    r = write_verdict(ctx, 2, 2, 1, 1, 0, "p", ["x"])
    assert r["accepted"] is False
    assert any("1 of 2 claims were never passed to check_claim" in x for x in r["reasons"])
    assert any("2 of 2 artifacts were never passed to verify_artifact" in x for x in r["reasons"])
    assert ctx.verdict is None


def test_write_verdict_refuses_a_number_the_tools_did_not_return(tmp_path):
    path, made, never = _sitting(tmp_path)
    ctx = CoachContext(path)
    read_run(ctx)
    for cid in (1, 2):
        check_claim(ctx, cid)
    for aid in (1, 2):
        verify_artifact(ctx, aid)
    r = write_verdict(ctx, 2, 2, 2, 1, 0, "p", ["x"])     # claims_verified: 2 claimed, tools said 1
    assert r["accepted"] is False
    assert r["reasons"] == ["claims_verified: you wrote 2, the tools returned 1"]
    assert r["tools_said"]["claims_verified"] == 1
    r = write_verdict(ctx, 2, 2, 1, 1, 0, "   ", ["x"])    # empty paragraph
    assert r["accepted"] is False and "the paragraph is empty" in r["reasons"]


def test_write_verdict_accepts_the_tools_numbers_and_matches_the_card(tmp_path):
    path, made, never = _sitting(tmp_path)
    ctx = CoachContext(path)
    read_run(ctx)
    for cid in (1, 2):
        check_claim(ctx, cid)
    for aid in (1, 2):
        verify_artifact(ctx, aid)
        git_evidence(ctx, aid)
    r = write_verdict(ctx, 2, 2, 1, 1, 0, "One of two claims had evidence; one of two files exists.",
                      ["Name the test in the claim", "Commit out.md"])
    assert r["accepted"] is True
    v = r["verdict"]
    assert v["numbers"] == dict(turns_typed=2, claims=2, claims_verified=1, artifacts_produced=1, commits=0)
    assert v["verified_per_turn"] == 1.0            # (1 + 1) / 2
    assert v["matches_card"] is True                 # same rule as solo.py, so the card agrees
    assert v["unverified_claims"] == [2] and v["missing_artifacts"] == [2]
    assert ctx.run["claims"] == 2 and ctx.run["claims_verified"] == 1 and ctx.run["artifacts_produced"] == 1
    run = attach(ctx, "test mode")
    assert run["coach_verdict"].startswith("One of two")
    assert run["coach_plan"] == "Name the test in the claim\nCommit out.md"
    assert run["coach_numbers"]["claims_verified"] == 1


def test_bundled_fixture_reads_from_the_repo_root():
    """`agentgrinder coach samples/sample_session.jsonl` is the stranger's first command."""
    cwd = os.getcwd()
    os.chdir(REPO)
    try:
        ctx = CoachContext(FIXTURE)
        r = read_run(ctx)
        assert r["turns_typed"] == 3 and len(r["claims"]) == 2 and len(r["artifacts"]) == 2
        assert check_claim(ctx, 1)["verified"] is True
        assert check_claim(ctx, 2)["verified"] is False
        assert verify_artifact(ctx, 1)["exists"] is True
        assert verify_artifact(ctx, 2)["exists"] is False
    finally:
        os.chdir(cwd)
