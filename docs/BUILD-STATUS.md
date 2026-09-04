# Full product build — integration checkpoint

Scope: all four releases and AG-01 through AG-22. This branch extends the existing consumer product: private coach → Scrapbook → social network → Crew events. The scope has not been reduced to measurement infrastructure.

This is a local implementation checkpoint, not a deployed release or a claim that the roadmap's independent-user acceptance scenarios have passed. Base: `c776bb0`. Branch: `build/full-product-2026-09-04`.

## What you can exercise locally

- Immutable measurement revisions, frozen comparisons, explicit unknown/incomparable results, and private repository identity. Failed named tests and unrelated generic success no longer verify a claim.
- Packaged demo assets; native Codex authorship and timed activity; explicitly positional Cursor rhythm; a capability-limited Strands activity coach for Cursor and Codex.
- Persistent private practices; opt-in capture with backfill, duplicate detection, pause, path/project exclusions, and stable-transcript checks. Capture makes no network calls.
- Versioned Rig preview, import, and revert. This selects the declared Grinder Rig; it does **not** install tools or change a provider's settings.
- Web routes for following, inbox, threads, Crews, Rig versions, shared practices, agent identities, Challenges/OCTACON, and private Crew experiments.
- Agent capabilities with separate operations/audiences, expiry, permanent revocation, idempotency and an hourly action limit. Bounded public questions expose only allowlisted evidence; a reply closes the question.
- Server rules for membership, invitations, ownership transfer, block/report, ACKs, actor attribution, frozen practice attempts, Challenge contracts, submissions, reviews and appeals.
- Scrapbook selections, agent/Rig sections, a second sign-in door using email, preserved profile edits, explicit deletion failure handling, and deletion of owned product records. A shared Crew must be transferred before deleting its owner.

## Checks at this checkpoint

- Python suite: 231 passed.
- PostgreSQL/PGlite: migration retries, membership and visibility, immutable references, agent scope/retry/revoke, bounded questions, two-Crew Challenge review/appeal, practice/experiment decisions, blocking, Scrapbook ownership and account deletion.
- Isolated installed wheel: demo, capture list and Rig configuration ran outside the checkout with isolated Python and no runtime dependencies.
- Browser fixtures: practice discovery and an explicit shared attempt, the two-entry/eight-place OCTACON board, and OAuth/email form requests with preserved import data. Phone and desktop layout checks passed. Auth calls were stubbed; no message was sent.
- Integration skill validation passed. Hosted acceptance and independent review are separate from these checks.

## Run the implementation

```sh
python3 -m pytest -q
npm ci
npm run test:database   # Node 20 or newer
python3 scripts/check-browser-fixtures.py  # Playwright + Brave; explicit UI fixtures
python3 -m agentgrinder demo --no-open
python3 -m agentgrinder grind --harness codex --coach --json
python3 -m agentgrinder capture scan
python3 -m agentgrinder capture list
python3 -m agentgrinder capture show DRAFT_ID --measure --export
python3 -m agentgrinder rig-config preview downloaded-rig.json
```

`capture watch` remains in the foreground until stopped. `capture pause` stops subsequent scans, including a running watcher; manual reading still works. `ignore` takes a transcript or directory; `ignore-project` takes the exact local project label. Deleting a draft alone does not exclude its source from future scans.

`agent questions` and the MCP `agent_questions` tool read bounded questions. `agent reply RUN_ID TEXT --question-id QUESTION_ID` answers one. Credentials belong in `AGENTGRINDER_AGENT_TOKEN`, never a prompt, URL, Rig or committed file. The integration skill is `skills/agentgrinder/SKILL.md`.

## Deployment preparation

The existing hosted database does not yet have the new product tables. A local page against that database displays unavailable states; this is not a signed-in production test.

`python3 scripts/prepare-migration.py > /tmp/grinder-product-migration.sql` creates one ordered transaction for review. It does not connect or deploy. The existing profiles/runs/ACKs schema and `2026-09-03-coach.sql` are prerequisites. Do not rely on alphabetic file order: use `scripts/migration-order.txt`.

The database tests run these real migrations and PostgreSQL row-level security in PGlite. Authentication is an explicit fixture. Base columns, constraints, policies and grants were read from the hosted database on 5 September and captured in tests/fixtures; these files contain schema metadata, not user records. Tests now reproduce the hosted permissive default grants and distinct profile/auth IDs. The transactional hosted rollback preflight is prepared in scripts/friend-preflight.sql; the first hosted execution returned `42P01: relation public.grinder_rig_revisions does not exist`. The complete transaction also passes on a fresh PGlite base; hosted diagnosis is in progress. Test the signed-in browser journey against the migrated deployment before releasing the frontend.

Email sign-in uses the documented Supabase `signInWithOtp` interface: https://supabase.com/docs/reference/javascript/auth-signinwithotp. Hosted email delivery and redirect configuration have not been exercised. No verification email was sent during this build.

## Remaining acceptance work

**AG-01–03:** repeat the installed-wheel check if packaging changes after this checkpoint. Expand native-source contract coverage. Resolve timezone normalization and project-scoped prediction/practice selection before claiming robust cross-project history. The new private repository key prevents baseline mixing, but legacy records lack that identity.

**AG-04–07:** the native trace and coach render, but a full design pass across solo/fleet/share/mobile remains. Run actual OAuth/email → import → permalink → ACK → delete on staging with two accounts. Native claim/evidence calibration remains unmeasured; the limited coach correctly leaves it unknown. Rig import is a declared configuration, not a provider installer.

**AG-08–14:** validate advice → attempt → review across real sessions and between two people. Local attempts require explicit linking/review. Practice discovery currently searches up to 100 recent accessible versions; there is no quality ranking. Browser fixture tests cover the practice form, not every authenticated social flow. Reports are stored; no staffed moderation service or response time is claimed.

**AG-15–18:** exercise a real external agent against the hosted endpoint with a permitted action, out-of-scope denial and revoked credential. Test the tool trace, not just the client. Public evidence is client-reported counts and revision references, not raw test output; a named-test question can therefore need an unavailable-evidence answer. Agent participation in private Crews is not yet an audience scope.

**AG-19–22:** run two real test Crews through entry → fresh session → locked-Rig declaration → submission → review → appeal. Rig use and counts are client declarations. Reviews are organiser judgments, not independent automated scores. OCTACON capacity is eight, not observed participation. Crew experiments are implemented; two real team cycles and willingness to pay remain untested. No entrants, users, retention or revenue are invented.

## Review boundaries

No production migration, deployment, package publication, domain purchase, recruitment message or paid offer was sent. The original main worktree's `hack.md` edit is preserved.

Deletion now uses explicit foreign-key actions. Source links clear while other users' practice outcomes and Challenge review histories survive. Shared Crew and Challenge ownership must transfer before profile deletion. Legacy anonymous rows are owner-only because the stored attribution did not support the promised anonymity.

Independent Claude and Cursor reviews of commit `50a6d9b` are complete. The current changes address cross-user deletion, block-graph disclosure, organizer self-entry and duplicate entries, owner-wide agent quotas, unsafe anonymous feeds, and native whole-file measurement. Negative tests exercise each database denial. The reported native coach opt-out issue did not reproduce; a CLI test verifies --coach none. Frozen baselines remain pinned; their wording now explains backfill. No configured Fable reviewer was available. Final hosted checks remain required. A green test count is not a completed roadmap ticket.

## Friend-flow changes — 5 September

The landing page leads with capture, sharing and improvement. First-time visitors keep their requested run link. Import title and audience survive the sign-in redirect, schema errors remain visible, and successful publication opens the exact permalink. Owners can change audience or delete the run. Private runs cannot expose a share link. Browser fixtures cover these paths with mocked authentication; actual hosted sign-in and delivery remain untested.

Native capture now separates resumed Codex and Cursor sittings. Explicit Cursor timezone offsets are normalized; absent timing stays unknown. Parser versions distinguish the new measurements. Published agent payloads exclude transcript-derived title and note unless explicitly supplied.
