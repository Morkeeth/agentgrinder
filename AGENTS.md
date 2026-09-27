<!-- STATE:start -->
## SHARED WORK STATE · revision 97735ea910a7 · rendered 2026-09-11 · scope repo agentgrinder
This repo's rows of the one shared work state. Authorities: todo.md (human), TASKS.yaml (ids), board clocks, Oscar's rulings (local only). Views such as GLANCE, SLASK and ZUP are adapters over the same revision.
**A CLOSED task stays closed. Do not requeue, re-verify or re-poll it.**
Before acting, record that you read this revision, exact session and exact rev: `python3 ~/CODE/fleet-ops/state/state.py ack --session <your session id> --consumer <claude|codex|cursor> --rev 97735ea910a7`. In a cloud sandbox instead append `{"session":"<your session id>","consumer":"<claude|codex|cursor>","rev":"97735ea910a7","ts":"<iso>","stage":"acknowledged"}` to `.fleet/ACK.jsonl` in this repo and commit it.

### CLOSED. Not open work.
- **GRINDER-STRANDS-RULING** · Agents for Humans: rule Strands eligibility, option A or B · **COMPLETED**. by Oscar's ruling (held local-only)

### ACKNOWLEDGED THIS REVISION: nobody yet
<!-- STATE:end -->

## Cursor Cloud specific instructions

- Dependency install is `bash .cursor/install.sh` (Node lockfile plus a Python 3.12 `.venv` with the `dev` and `coach` extras). Use `.venv/bin/pytest` and `.venv/bin/agentgrinder` for tests and the Strands coach. `python3 -m agentgrinder` still runs the dependency-free reader.
- The web app is the static `site/` directory. The `web` terminal serves it at http://127.0.0.1:8765/. The labelled walkthrough is `/?example`.
- `npm run test:database` and `npm run test:journey` replay the hosted schema in disposable PGlite. They do not call production Supabase.
- Coach mode defaults to local and keyless. Do not pass `--model bedrock`.

