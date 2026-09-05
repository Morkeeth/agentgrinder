# Agent Grinder — saved handoff, 5 September 2026

Agent Grinder is live at https://agentgrinder.vercel.app. The product direction remains Strava for agent work: record, flex, improve. This is a build handoff, not a claim that all acceptance work is complete.

## Released

Product code on `main`: `10f9619`. Production deployment: `dpl_ABAkhqBVUuQJCjCeh6G6wBM6xT8K`.

- Local capture for Claude Code, Cursor and Codex; local history and MCP connection setup.
- Private import, audience controls, run links, profiles, Rigs, following, ACKs, inbox, Crews, practices and Challenges.
- My runs search/filter/history → saved comparison → next private practice. Comparison snapshots stay fixed when source runs change or are deleted.
- Run posts led by the work and session trace, with detailed measurements available below.
- Sharing editor with explicit contribution/result/next-run text, square and portrait PNG export, and a review step. Existing notes and project names are not copied. Private-run captions omit the link.
- Searchable Forum discovery across runs, discussions and practices; a reply can become a private practice draft linked to its source.
- Public `/r/RUN_ID` share pages with per-run metadata and a generated 1200×630 PNG. Server reads only public rows and sends no-store headers. Third-party social platforms can retain copies they already fetched.
- Explicit Claude SDK/sidechain capture through CLI `agentgrinder agent capture TRANSCRIPT` and MCP `capture_agent_run`. Zero human turns stay zero. Tool requests do not imply successful work.

GitHub provides sign-in, public identity and local Git evidence. Cursor provides native transcript capture and MCP configuration. Neither is an official partnership or hosted PR synchronization.

## Built and tested, not released

Forum lifecycle implementation: `adc5dd7` on `build/full-product-2026-09-04`.

- Titled questions attached to a run, inheriting its audience.
- Answers, in-app subscriptions and recent-reply indicators.
- Question-author selection of an answer. Editing that answer clears the selection.
- Mark-read bound to the last displayed reply, so later arrivals are not silently marked read.
- Answer → private practice path.

Requires `supabase/migrations/2026-09-05-forum.sql`. The new frontend has not been deployed. At the final check on 5 September, 16:16 UTC, the questions table returned HTTP 404 / PGRST205. Live index, forum and sharing bytes matched released main.

## Verification already completed

- Python: **245 passed, 1 skipped**. The existing skip lacks a second real harness transcript for claim-source calibration.
- Actual ordered PostgreSQL/PGlite migrations and role tests: ownership, privacy, changed retries, frozen baselines, scope/revocation rules, Challenge lifecycle, forum cross-run denial, blocked authors, source deletion and chosen-answer invalidation.
- Browser fixtures: import and auth-return handling, personal history, comparison → practice, forum → practice, question/follow/read controls and PNG downloads. Authentication and server responses are explicitly controlled fixtures.
- Square/portrait exports and phone/desktop screens inspected. Actual PNG dimensions checked.
- Hosted public preview returned HTML 200 and image/png 200; invalid ID returned 404. The downloaded live PNG was inspected.
- Earlier authenticated hosted import/audience/permalink flow passed. The later signed-in Progress and question flows remain unverified.
- A real Claude client invoked local preview, hosted public-feed reading and the new automated capture tool. The automated source returned 0 human turns, 2 tool requests and 6.48 seconds; commit count and quality remained unknown. An agent's prose briefly confused unknown commits with zero; the tool payload is the evidence.
- Outbound site and server sources were checked for private content. Raw transcripts and local evidence remain outside Git.

No independent adoption, retention, quality improvement or successful hosted agent write is claimed. Database scope tests do not substitute for a real client using a hosted credential.

## Next execution sequence

1. Restore the authenticated Brave browser connection and open the project SQL editor. Approval for the migration and release is already recorded; the missing dependency is working access. Browser calls repeatedly timed out or lost their tab. No authenticated database CLI or agent credential was available in the session environment.
2. Apply the tested forum migration. Verify the tables/RPCs and private subscription permissions on the hosted database.
3. Deploy the complete build frontend from a minimal stage containing `site/`, `api/`, `server/`, package files, `vercel.json` and Vercel project metadata. Do not copy environment files. Verify live bytes, then fast-forward main to the integrated build.
4. Drive a controlled hosted question → answer → follow → return → chosen answer → practice journey. Check a second role and a private audience. Label controlled accounts; remove temporary test data after verification.
5. Give a real agent a narrowly scoped test credential. Verify permitted private draft, identical retry, explicit scope denial and denial after revocation. Exercise a bounded evidence question and attributed response without agent conversation loops.
6. Complete the real practice → later run → review loop and the two-Crew event acceptance. Then do a fresh-user friend walkthrough. Do not count controlled test identities as independent users.

## Reproduce

Use Node 22 for database and image checks.

```sh
python3 -m pytest -q
npm ci
npm run test:database
python3 scripts/check-browser-fixtures.py
python3 scripts/check-progress-fixtures.py
python3 scripts/check-sharing-fixtures.py
python3 scripts/check-forum-fixtures.py
python3 scripts/check-question-fixtures.py
node scripts/check-public-preview.mjs
python3 scripts/check-hosted.py
```

The public-preview and hosted scripts make read-only requests. Browser fixture scripts run isolated controlled pages. `scripts/migration-order.txt` specifies the deployment order.
