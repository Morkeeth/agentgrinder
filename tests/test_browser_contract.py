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
