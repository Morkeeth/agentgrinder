# Release notes · complete focused journey (2026-09-13)

Stacked on candidate `day/2026-09-11-grinder-ambition` @ `be5704c`. PR1 remains the release candidate. This work is an isolated branch. Coordinator owns production deploy and final submission.

## Built

- Stranger landing with one start action, the signature *I tried this. Show me what changed.*, and a labelled bundled example that needs no account.
- Bring-your-own capture stays private by default, with concise local import copy and evidence-availability language (dashes name what was not measured).
- Strands coach still checks every claim and file, then proposes **one** supported friction with tool evidence and **one** next-session experiment. Scripted/demo vs Bedrock/live labels are printed. `agentgrinder coach --live-status` returns exact missing configuration and will not start a fake live run.
- Coaching-to-practice: accept/edit the experiment on a measured grind, freeze that grind as baseline, return with keep/change/drop/incomparable, original measurements preserved, one observed outcome required.
- Bundled example continues through moment review, a second-builder fixture role on **their** baseline, and outcome export using the existing share studio.
- Community overview leads with public techniques (honest empty state if none). Returning builders land on pending practices and recognition, not a marketing page.
- Forward migration `2026-09-13-coach-mode.sql` (nullable `runs.coach_mode`). Not applied to production here.

Preserved: existing moment authoring, adoption RPC, outcome export, practice RLS, nav (Feed / My runs / Community / Inbox).

## Tested

- Unit: coach experiment selection, live-status secrecy, landing contract, bundled fixture hygiene. Full `tests/` minus `test_claim_rule.py`: 269 passed; one pre-existing Cursor/Codex `claims` key assertion in `test_coach_degrade.py` is unchanged from the candidate.
- Clean venv install of the package. `agentgrinder coach --live-status` exit 2 with exact missing items (`strands-agents`, `aws-region`, `aws-credentials`); no credential values printed.
- Database: ordered PGlite migrations including nullable `runs.coach_mode`, plus existing moment/adopt/revocation checks.
- Browser fixtures, labelled: bundled example phone+desktop; practice discovery/attempt; moment author → stranger keep on own baseline → return/export; progress freeze→review; signed-in nav at 390 and 1280.
- Not claimed: hosted auth against production, live Bedrock execution, independent human adoption.

## Hosted

- Not deployed by this agent. Root `main` and agentgrinder.vercel.app are not assumed to contain this candidate.
- Preview: whatever Vercel/GitHub attach to this branch. Bundled example is static (`site/bundled-example.json`, `site/example.js`) and does not need the moments/adopt DDL.
- Moments, adoption, and `coach_mode` on stored runs need the coordinator to apply the listed migrations in `scripts/migration-order.txt`.

## Used

- Bundled public-safe fixture derived from `samples/sample_session.jsonl` via the real coach tools (deterministic mode).
- No private transcripts, credentials, or production writes.
- No new paid-provider spend.
