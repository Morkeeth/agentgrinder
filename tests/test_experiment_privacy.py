"""named_targets must not extract directory paths into coach_plan / export.

Claim text can carry a home directory. The old PATH_NAME regex matched
`Users/casey/Documents/notes/secret-plan.md` inside `/Users/casey/.../secret-plan.md`
and wrote it into friction, instruction, and coach_plan. Export then shipped it.

Local coaching may still name test_ identifiers and slash-free basenames.
"""
from agentgrinder.coach.experiment import (
    named_targets,
    public_experiment,
    public_run_view,
    public_text,
    select_experiment,
)
from agentgrinder.push import export_run
from agentgrinder.solocard import _verdict_block
from agentgrinder.render import render_card
from agentgrinder.metrics import build_activity

HOME = "/Users/casey/Documents/notes/secret-plan.md"
TILDE = "~/private/keys.env"
WIN = r"C:\Users\casey\secret.py"
CLAIM = (
    f"Done, {HOME} and {TILDE} and {WIN} are saved. "
    "test_draft_renders passes."
)


def test_named_targets_drop_directory_paths_and_keep_test_names():
    assert HOME not in named_targets(CLAIM)
    assert "Users/casey/Documents/notes/secret-plan.md" not in named_targets(CLAIM)
    assert "secret-plan.md" not in named_targets(CLAIM)
    assert TILDE not in named_targets(CLAIM)
    assert WIN not in named_targets(CLAIM)
    assert named_targets(CLAIM) == ["test_draft_renders"]
    assert named_targets("Wrote draft.md in this turn.") == ["draft.md"]
    assert named_targets("See docs/secret.md") == []


def test_select_experiment_does_not_name_a_home_path():
    exp = select_experiment(
        claims=[{"id": 2, "turn": 2, "line": CLAIM}],
        checks=[{"claim_id": 2, "verified": False, "results_in_turn": 1}],
        artifacts=[], exists=[], gits=[], turns_typed=2, commits=0,
    )
    blob = " ".join(str(v) for v in exp.values())
    assert exp["kind"] == "unverified-named-claim"
    assert "test_draft_renders" in exp["instruction"]
    assert HOME not in blob
    assert "Users/casey" not in blob
    assert "secret-plan.md" not in blob
    assert "~/" not in blob
    assert "C:\\Users" not in blob


def test_path_only_claim_is_not_a_named_target():
    line = f"Finished {HOME}"
    assert named_targets(line) == []
    exp = select_experiment(
        claims=[{"id": 1, "turn": 1, "line": line}],
        checks=[{"claim_id": 1, "verified": False}],
        artifacts=[], exists=[], gits=[], turns_typed=1, commits=0,
    )
    assert exp["kind"] == "unverified-claim"
    assert HOME not in exp["friction"]
    assert "Users/casey" not in "\n".join(exp["plan"])


def test_export_and_cards_replace_path_tokens_and_drop_local_keys():
    named = select_experiment(
        claims=[{"id": 2, "turn": 2, "line": CLAIM}],
        checks=[{"claim_id": 2, "verified": False, "results_in_turn": 0}],
        artifacts=[], exists=[], gits=[], turns_typed=3, commits=0,
    )
    missing = select_experiment(
        claims=[{"id": 1, "turn": 1, "line": "Suite passes."}],
        checks=[{"claim_id": 1, "verified": True}],
        artifacts=[{"id": 1, "label": HOME}],
        exists=[{"artifact_id": 1, "label": HOME, "exists": False}],
        gits=[], turns_typed=3, commits=0,
    )
    assert missing["kind"] == "missing-artifact"
    assert HOME in missing["friction"]
    assert HOME not in str(public_experiment(missing))
    run = {
        "turns_typed": 3,
        "coach_verdict": f"Missing {HOME} on disk.",
        "coach_plan": "\n".join(missing["plan"]),
        "coach_experiment": missing,
        "coach_experiment_local": missing,
        "private_coach_plan": f"Review {TILDE}",
        "coach_mode": "deterministic fallback · no agent, no model",
    }
    exported = export_run(run)
    dumped = public_run_view(run)
    html = _verdict_block(run)
    card = render_card(build_activity({
        **run, "athlete": "you", "title": "t", "harness": "Cursor", "project": "p",
        "started": "2026-09-11T12:00:00+00:00", "artifacts_produced": 1,
        "claims": 2, "claims_verified": None, "tool_calls": 4, "files_touched": 1,
        "commits": 0, "duration_s": 60, "rhythm": [1, 1],
        "capabilities": {"claim_evidence": False}, "trace_basis": "typed-turn order",
    }))
    for blob in (exported, dumped, html, card):
        text = blob if isinstance(blob, str) else str(blob)
        assert HOME not in text
        assert "Users/casey" not in text
        assert TILDE not in text
        assert "secret-plan.md" not in text
        assert "private/keys.env" not in text
        assert "C:\\Users" not in text
        assert "coach_experiment_local" not in text
        assert "private_coach_plan" not in text
    assert exported["coach_mode"].startswith("deterministic")
    assert "test_draft_renders" in named["instruction"]
    assert public_text(HOME) == "[file]"


def test_file_claim_requests_inspection_not_execution():
    exp = select_experiment(
        claims=[{"id": 1, "turn": 1, "line": "Done, terms.md is complete."}],
        checks=[{"claim_id": 1, "verified": False}],
        artifacts=[], exists=[], gits=[], turns_typed=1, commits=0,
    )
    assert "check that terms.md exists and inspect its contents" in exp["instruction"]
    assert "run terms.md" not in exp["instruction"]
