"""Run the shipped browser boundary with the same real exported payload as the CLI."""
import json
from pathlib import Path
import subprocess

from agentgrinder.push import export_run


def test_browser_accepts_export_and_rejects_invalid_counts():
    module = Path(__file__).resolve().parents[1] / "site/run-contract.js"
    payload = export_run({"turns_typed": 2, "claims": 3, "claims_verified": 1})
    script = """
const {validate}=require(process.argv[1]);
const run=JSON.parse(process.argv[2]);
validate(run);
for(const bad of [{...run,claims_verified:4},{...run,turns_typed:true},{...run,schema_version:999},{...run,measurement_revision:'bad'}]){
  let rejected=false;
  try {validate(bad)} catch(e) {rejected=true}
  if(!rejected) throw new Error('Invalid run accepted');
}
"""
    subprocess.run(["node", "-e", script, str(module), json.dumps(payload)], check=True)


def test_practice_outcome_selector_matches_server_chronology():
    module = Path(__file__).resolve().parents[1] / "site/practice-eligibility.js"
    script = r"""
const {outcomeRuns}=require(process.argv[1]);
const attempt={created_at:'2026-09-02T12:00:00Z',baseline:{measurement_revision:'base'}};
const runs=[
 {id:'valid',started_at:'2026-09-02T12:00:00Z',measurement_revision:'new'},
 {id:'pre-attempt',started_at:'2026-09-02T11:59:59Z',measurement_revision:'older-import'},
 {id:'future',started_at:'2026-09-04T00:00:01Z',measurement_revision:'future'},
 {id:'same-revision',started_at:'2026-09-03T00:00:00Z',measurement_revision:'base'},
 {id:'missing-time',started_at:null,measurement_revision:'missing'}
];
const ids=outcomeRuns(attempt,runs,Date.parse('2026-09-04T00:00:00Z')).map(r=>r.id);
if(JSON.stringify(ids)!=='["valid"]') throw new Error('wrong eligible outcomes: '+JSON.stringify(ids));
if(outcomeRuns({...attempt,created_at:null},runs).length) throw new Error('attempt without server chronology accepted');
"""
    subprocess.run(["node", "-e", script, str(module)], check=True)
