#!/usr/bin/env python3
"""Show `write_verdict` refusing a number the tools did not return.

The claim on the card is that the coach cannot write a figure no tool produced. This script is
how you check that claim in ten seconds, with no agent loop in the way: it calls the five real
coach tools on the bundled sample sitting, then offers `write_verdict` an inflated verdict and
prints what comes back. Nothing here is a mock. Every function is the one the Strands agent
calls.

    python3 scripts/show-refusal.py [TRANSCRIPT]

Default transcript: samples/sample_session.jsonl, where the tools verify 1 claim of 2 and find
1 written file of 2 on disk. The offered verdict says 2 and 2.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from agentgrinder.coach.tools import (  # noqa: E402
    CoachContext, check_claim, git_evidence, read_run, verify_artifact, write_verdict,
)

DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                       "samples", "sample_session.jsonl")


def main(argv: list[str]) -> int:
    transcript = argv[1] if len(argv) > 1 else DEFAULT
    ctx = CoachContext(transcript)

    run = read_run(ctx)
    for c in run["claims"]:
        check_claim(ctx, c["id"])
    for a in run["artifacts"]:
        verify_artifact(ctx, a["id"])
        git_evidence(ctx, a["id"])

    print("\n  the tools were called on", os.path.basename(transcript))
    print(f"  {len(run['claims'])} claims, {len(run['artifacts'])} written files, "
          f"{run['turns_typed']} typed turns\n")

    offered = dict(turns_typed=run["turns_typed"], claims=len(run["claims"]),
                   claims_verified=len(run["claims"]),
                   artifacts_produced=len(run["artifacts"]), commits=run["commits"])
    print("  now offering write_verdict a verdict that says every claim and every file checked out:")
    print("   ", json.dumps(offered), "\n")

    out = write_verdict(ctx, paragraph="Everything shipped.", plan=["ship more"], **offered)
    print("  write_verdict returned:\n")
    print("    accepted:", out["accepted"])
    for r in out.get("reasons", []):
        print("    refused: ", r)
    if out.get("tools_said"):
        print("    the tools said:", json.dumps(out["tools_said"]))
    print()
    return 0 if out["accepted"] is False else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
