# Agent Grinder — release review, 5 September 2026

The product is deployed at https://agentgrinder.vercel.app. The full scope remains Strava for agent work: record, flex, improve. All four releases and AG-01–22 remain in the plan. Implemented features are not evidence of independent adoption or improved work.

## What shipped

- Private local capture and history for Claude Code, Cursor and Codex; resumed sessions; frozen measurement revisions and comparisons; project-specific practices and predictions.
- Run import, audience selection, permalink, Scrapbook, following, ACKs, discussions, inbox and Crews.
- Rig versions, shared practices, agent profiles and scoped credentials; Challenges/OCTACON and private Crew experiments.
- One web design and shared card palette; shorter onboarding, methodology and privacy copy; unavailable counts remain unknown.
- `connect cursor|claude --project PATH --install` merges an MCP connection without credentials, preserves other servers and keeps machine-specific configuration out of Git. It refuses a tracked configuration.
- The default agent tools prepare proposals. Separately granted credentials permit only specified actions and audiences, with expiry, revocation, retry protection and owner-wide quotas.

## Verified against the build

- Python: **239 passed, 1 skipped**. The skipped claim-source test lacks a second real harness transcript; fixture tests do not substitute for that evidence.
- PostgreSQL/PGlite: actual ordered migrations, retries, anonymous grants, ownership, shared-history deletion, frozen comparisons, agent scope/revoke/retry, Challenge review/appeal and Crew experiments. Negative tests reject uncounted verified claims, link enumeration and private ACK reads.
- Browser fixtures: onboarding/import restoration and errors, profile creation/read, exact permalink, practice forms, OCTACON and phone/desktop layouts. Authentication is explicitly mocked in these checks.
- A real Claude agent called the current MCP server's `preview_run` on a labelled local fixture and `a2a_fetch_feed` against the hosted public feed. The tool trace contains both calls. No agent social write is claimed from this test.
- The site privacy scan found no flagged content across all 11 site files.

## Verified against the hosted product

The complete migration passed the real PostgreSQL rollback preflight, including two distinct auth/profile identities, private/public import, another profile's ACK, return notification and deletion. The transaction rolled back. The ordered product migrations then applied permanently.

Using the signed-in website, a labelled temporary run was imported privately, opened by its owner and changed to link visibility. Anonymous reads of its private state returned no rows. A query-join defect found during this journey was fixed: run reads now select `profiles!runs_profile_id_fkey`. Profile loading reads the existing profile before creating one, preserving edited names. Auth refreshes render in sequence to prevent duplicate controls when initial loading and sign-in arrive together.

The final privacy patch was applied separately. The live check observed a link collection returning no rows and the exact known link returning its run. Link reads require the run ID from the opened URL; ACK reads use the run's audience. Supabase CORS allows the request header. `scripts/check-hosted.py` checks five query shapes taken from the shipped source and anonymous denial on private tables.

The temporary fixture `c3187b9c-d289-496f-a235-8439a09c6f8a` was removed after testing. The hosted SQL query returned `temporary_fixture_remaining = 0`; this cleanup did not remove a real work session.

Tested implementation: `601ea5c` (published on `main`). Live HTML bytes match the tested source.

Production deployment: `dpl_9SS6wr5oQWURieyCD5JFeDRGYRp7`. Final installed wheel SHA-256: `fa1aff80575071b0d4932707dada612a9dbfea1cf18c76f9c741586536cacb7a`. Its demo, capture list and MCP connection setup ran outside the checkout in a clean virtual environment.

## Independent review and decisions

Claude and Cursor reviewed isolated checkouts. Their hosted-blocker claims used the pre-migration snapshot and stale status document; live SQL and REST checks supersede those claims. Their useful findings led to these changes:

1. A2A export now uses the same latest-sitting reader as the main flow and selects Codex correctly.
2. Cursor boundaries are described as gaps between dated human turns. Untimed assistant work means these are not measured idle gaps. Cursor traces remain positional.
3. Machine paths in MCP configuration stay local to Git.
4. Python, browser and server validation require a total claim count when a verified count is supplied.
5. Link-only runs cannot be enumerated; ACKs on private work cannot disclose their run IDs.
6. Agent onboarding no longer offers unsupported anonymous publishing. Profile deletion copy explains that the authentication account remains.

No configured Fable reviewer was available. The reviewers did not test the final hosted patch themselves; the checks above are separate evidence.

## What remains to prove

- Two independent people complete a real run → share → ACK → return journey. Email delivery still needs acceptance testing. GitHub sign-out → sign-in returned to the exact public run in the hosted browser. No invitation or email was sent.
- A real external agent performs an allowed hosted write, then encounters out-of-scope and revoked-credential denials. Database tests already cover those rules; that is a different test.
- A person tries a practice across real comparable sessions and finds it useful. Native claim/evidence calibration is not established. Rig selection declares configuration; it does not install a provider's tools.
- Two real Crews complete a Challenge and a team experiment. Eight OCTACON places are capacity, not observed entrants. No retention, paid demand or improvement rate is claimed.

GitHub integration provides sign-in, public identity and local Git evidence. Cursor integration provides native transcript capture and a working MCP connection. These are functional integrations, not an official partnership or hosted PR synchronization.

## Reproduce

```sh
python3 -m pytest -q
npm ci
npm run test:database                 # Node 20+
python3 scripts/check-browser-fixtures.py
python3 scripts/check-hosted.py
python3 -m agentgrinder demo --no-open
python3 -m agentgrinder connect cursor --project /your/project
```

The last command prints configuration; add `--install` to apply it. Local capture makes no network calls. Bedrock coaching is an optional network mode. Review exported notes and captions before sharing. Use `scripts/migration-order.txt` for deployment order; historical base fixtures describe the pre-migration schema, not today's live database.

## NIGHT-2026-09-05 — private Progress slice

Added searchable personal history, audience/harness filters, older-run pagination, pending practices and unread responses. Progress saves two immutable measurements with a declared task context. It shows unknown data and comparability limitations. A saved comparison can create one private practice and attempt using its frozen later measurement. The source run may change or be deleted without moving that baseline.

New capability relative to frozen baseline `396b3df`: saved comparisons and their direct next-practice path. Existing capture, practice storage and hosted social infrastructure are carried-in capabilities.

Validation: 239 Python tests passed, 1 skipped; ordered database migrations and comparison ownership/retry/frozen-baseline/deletion tests passed; existing browser fixtures passed; new history → comparison → practice → return fixture passed on phone and desktop with no overflow or JavaScript errors. The first fixture exposed ambiguous select labels; explicit accessible labels fixed that failure. Screenshots were inspected. These controlled fixtures do not represent independent users or measured improvement.

The Progress migration is applied to production. Hosted checks pass, including anonymous denial on grinder_comparisons. Deployment `dpl_Zo1qwHiJmKv5cssd6YCF5BZsa6Tq` is ready and aliased to the product URL. All four changed hosted assets match tested source bytes; 12 outbound site files passed privacy scanning. The signed-in hosted walkthrough remains open after a browser-control timeout.

A real-source probe also found that automated Claude CLI sessions with no human turns are rejected by the current capture contract. No guard was bypassed and no automated prompt was counted as human input. An explicit agent-only capture mode remains to build.

## Approved design, sharing, forum and agent capture slice

Run cards now lead with the work, trace and three counts; detailed measurements and coach reports sit in an expandable section. The sharing editor exports actual square (1080×1080) and portrait (1080×1350) PNG files from the same canvas used for preview. Captions use explicit builder-entered contribution, result and next-run text. Existing notes/project names are excluded, private links are omitted, and edits reset the review checkbox. Export dimensions, controls and privacy behavior passed browser tests; both images were visually inspected.

The Forum adds searchable, paginated Runs, Discussions and Practices using existing access-controlled records. A discussion reply opens a private practice draft with its text and a source-run link. Search, source link, private default and persistence payload passed the new browser fixture. Separate titled questions, subscriptions, accepted answers and automatic public link-preview images remain unfinished.

Explicit automated Claude capture is available through `agentgrinder agent capture TRANSCRIPT` and MCP `capture_agent_run`. It requires SDK or sidechain provenance, refuses human/ambiguous/partial/undated records, deduplicates tool IDs, records zero human turns, and does not infer successful work. A distinct trace basis prevents comparison with human-turn rhythms. A real completed agent session produced 0 typed turns, 2 tool requests and 6.48 elapsed seconds; commits/claims/artifacts remain unknown. A real Claude client invoked the new MCP tool after ToolSearch discovery. Its prose briefly misstated unknown commits as no commits; the returned payload remained correct. The trace stays local at `/tmp/grinder-real-agent-capture-trace.jsonl`.

Validation: Python 245 passed, 1 existing skip; the affected MCP manifest tests passed after adding the tool. Existing browser fixtures, Progress fixtures, new sharing exports and forum-to-practice fixtures passed. Initial select-label failures were fixed with explicit accessible labels. The previous test requiring a score headline was updated to the approved work-first design. Fourteen outbound site files passed privacy scanning.

Production deployment `dpl_BvSpMk399ZiG1UZicwen3JrCvucr` is ready. Seven changed hosted assets match local tested bytes. The live browser session again lost its tab while opening the forum, so signed-in hosted interaction acceptance remains open. No independent-user adoption, successful hosted agent write, quality lift, subscription or complete forum lifecycle is claimed.
