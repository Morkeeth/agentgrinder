"""Returning-user journey: grind-trace attribution and next practice on the run object."""
import json
from pathlib import Path

from agentgrinder.metrics import build_activity
from agentgrinder.render import render_card

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "samples" / "returning_run.json"


def test_fixture_card_names_trace_basis_and_next_practice():
    run = json.loads(FIXTURE.read_text())
    html = render_card(build_activity(run))
    # render_card HTML-escapes string fields; assert against the rendered object.
    assert "typed turns per equal-width bucket over moving time" in html
    assert "idle gaps" in html and "20m excluded" in html
    assert "Next practice" in html
    assert "Run the named check in the same turn as the claim." in html
    assert "Trace time basis unknown" not in html


def test_missing_trace_basis_is_named_not_invented():
    run = json.loads(FIXTURE.read_text())
    run = {**run, "trace_basis": ""}
    html = render_card(build_activity(run))
    assert "Trace time basis unknown" in html
    assert "typed turns per equal-width" not in html


def test_contract_trace_includes_attribution():
    import subprocess, sys

    script = r"""
const fs=require('fs');
const vm=require('vm');
const src=fs.readFileSync('site/run-contract.js','utf8');
const sandbox={module:{exports:{}}, globalThis:{}};
vm.runInNewContext(src, sandbox);
const api=sandbox.module.exports;
const known=api.trace({rhythm:[1,3,2],trace_basis:'elapsed minutes'});
if(!known.includes('elapsed minutes')) throw new Error('named basis missing');
const unknown=api.trace({rhythm:[1,2]});
if(!unknown.includes('Trace time basis unknown')) throw new Error('unknown basis missing');
const empty=api.trace({rhythm:[]});
if(!empty.includes('Trace unavailable')) throw new Error('empty rhythm should be unavailable');
console.log('ok');
"""
    result = subprocess.run(
        [sys.executable and "node" or "node", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "ok" in result.stdout
