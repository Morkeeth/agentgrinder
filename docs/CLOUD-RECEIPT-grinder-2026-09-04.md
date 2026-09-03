# CLOUD RECEIPT · Agent Grinder · 2026-09-04

Wave: **Phase 0 + Phase 1 + Sep 14 pack spine**. Oscar owns film / rulings / Devpost submit.
Outward acts were not taken.

## SHIPPED

What exists now that did not exist (or was broken) at wave start:

1. **Phase 0 honesty fixes**
   - Get Started + pitch no longer hand bare `pip install -e .` (live still does until Oscar redeploys).
   - Cursor + Codex parsers now run the claim rule over assistant text; Cursor counts Write/Edit paths when present; produced/reach dashes carry harness-specific reasons.
   - Cursor/Codex `grind --json` honored (was silently ignored).
   - `scripts/recompute-claim-calibration.py` — re-derives P/R from `docs/claim-calibration.json`, compares to v0 baseline, `--check-docs` pins surfaces.
   - `tests/test_evidence_match_eval.py` — synthetic embarrassment eval (token-only baseline beats shipped precision on the generic-`N passed` hole).
2. **Phase 1 stranger evidence**
   - `scripts/stranger-three-homes.py` — three temp HOMEs + empty HOME, following INSTALL_CMD from the live site object.
   - Receipts: `docs/stranger-three-homes-2026-09-04.{md,json}` · live pip-lie: `docs/stranger-three-homes-LIVE-2026-09-04.{md,json}`
3. **Sep 14 pack spine (docs only)**
   - `docs/OSCAR-CLICK-LIST-2026-09-04.md` — what must be true before Devpost; no submit.
4. **Contract**
   - `hack.md` NOW/LOG updated for this wave.

## VERIFIED (at the object, with the command)

| Claim | Command | Result |
|-------|---------|--------|
| Held-out claim-rule P/R | `python3 scripts/recompute-claim-calibration.py --check-docs` | shipped **0.63 / 0.66**, v0 **0.32 / 0.37**; docs match; target >0.8 **NOT REACHED** |
| Rule fingerprint | `python3 -c '… rule_fingerprint() …'` vs `docs/claim-calibration.json` | `e49d8713c3c2df38` match |
| Live methodology carries numbers | fetch `https://agentgrinder.vercel.app/methodology` | 0.63, 0.66, 0.32, 0.37, fingerprint present; `live==local` at start of wave |
| Live INSTALL_CMD is clone-only | fetch live HTML, regex `INSTALL_CMD` | `git clone … && python3 -m agentgrinder grind` |
| Live Get Started / pitch still lie | same fetch | bare `pip install -e .` on L959, L1013 (**PASS_WITH_LIVE_PIP_LIE**) |
| Local site no longer lies | `python3 scripts/stranger-three-homes.py --local-cmd` | bare pip: **no** |
| Empty HOME | same script | grind rc=1, names all three harness paths, points at demo; demo rc=0, card written |
| Claude / Cursor / Codex HOMEs | same script | all three **PASS** with card files; claude headline 0.67; cursor 0.5; codex headline `—` (no artifacts) |
| Demo five-row dashes | `HOME=$empty python3 -m agentgrinder demo --no-open` | correction / promised / reach print `—` |
| Evidence synthetic arms | `python3 -m pytest -q tests/test_evidence_match_eval.py` | shipped P≈0.57, token_only P=1.00, silent takes no bait; suite pins the hole |
| Touched tests | `pytest tests/ --ignore=tests/test_coach_missing_sdk.py` | **139 passed**, 1 skipped |

## WRONG

1. **Held-out precision target (>0.8) was not reached.** 0.63 is the number. Carried forward, not fixed tonight — fixing the rule invalidates the fingerprint without a new label set, and this machine has no real corpus.
2. **Evidence matching has no real label set.** The synthetic eval embarrasses the shipped matcher; it is not a held-out measurement and must not be quoted as one on Devpost.
3. **Live site still serves the Get Started / pitch `pip install -e .` lie** until Oscar redeploys. Local checkout is fixed; strangers hitting production tonight still see the old strings (`PASS_WITH_LIVE_PIP_LIE`).
4. **Codex headline stays `—`** when no Write/Edit paths exist — honest, but a stranger on Codex-only may think the product is broken. The card and tooltips say why.
5. **Pre-existing:** `tests/test_coach_missing_sdk.py::test_the_coach_still_runs_and_exits_zero_when_the_sdk_is_there` fails here because `strands-agents` is not installed (exit 1 with install hint). Not touched this wave.
6. **Bootstrap intervals** recomputed here ([0.44,0.83] / [0.47,0.84]) differ slightly from the doc's [0.43,0.83] / [0.46,0.83] — seed / off-by-one on percentile index. Point estimates match when rounded to 2 decimals; intervals were not rewritten.
7. **No non-Oscar human** cold-ran tonight. Phase 1 used fixture HOMEs. Recruit is on the Oscar click list.
8. **Did not film, submit, buy a domain, or push public** beyond this agent's feature-branch PR (forge PR tooling only).
