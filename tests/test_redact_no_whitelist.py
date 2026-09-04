#!/usr/bin/env python3
"""redact() must not exempt any name. Written after a hardcoded pass-through was found.

`alias["recon"] = "recon"` sat inside redact() for 18 hours. It survived because the
output LOOKS redacted: every other destination becomes "repo N", so a reader scanning
the card sees pseudonyms and stops. A whitelist inside a redaction function is the one
construct that cannot be audited from its own output.

This tests the FUNCTION, not a rendered card, on purpose. The original card could not be
reproduced (the night run's window no longer yields lanes) and a render with zero lanes
reports CLEAN for the wrong reason. That is the failure this file exists to prevent.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agentgrinder.fleet import redact

RUN = {
    "repos": [{"name": "aistrava", "branch": "night/private-branch-name"},
              {"name": "repo B", "branch": "main"}],
    "lanes": [{"repo": "aistrava", "code": "L6", "lane_name": "Agent Grinder", "repos": ["aistrava"]},
              {"repo": "recon", "code": None, "lane_name": "Recon sweep", "repos": []},
              {"repo": "repo B", "code": "L3", "lane_name": "lane B", "repos": []}],
    "sessions": [{"repo": "aistrava", "label": "morkeeth session"}],
    "repos_untracked": ["repo C"],
}

ok = fail = 0
def t(name, cond):
    global ok, fail
    if cond: ok += 1; print("  PASS " + name)
    else:    fail += 1; print("  FAIL " + name)

out = redact(RUN)
blob = repr(out)

t("no real repo name survives anywhere in the output",
  not any(n in blob for n in ("aistrava", "repo B", "repo C")))
t("THE ONE THAT MATTERS: 'recon' is not exempt", "recon" not in blob)
t("a destination that is not a repo still gets a label",
  all(l.get("repo") for l in out["lanes"]))
t("no lane brief name survives",
  not any(n in blob for n in ("Agent Grinder", "lane B", "Recon sweep")))
t("branch names are dropped, they carry project and ticket names",
  not any("branch" in r for r in out["repos"]))
t("counts and shape are untouched",
  len(out["lanes"]) == len(RUN["lanes"]) and len(out["repos"]) == len(RUN["repos"]))
t("the output declares it is redacted", out.get("redacted") is True)
t("the source run is not mutated", RUN["repos"][0]["name"] == "aistrava")

print("\nok=%d fail=%d" % (ok, fail))


def test_redact_has_no_whitelist():
    assert fail == 0, "%d redact checks failed" % fail


if __name__ == "__main__":
    sys.exit(1 if fail else 0)
