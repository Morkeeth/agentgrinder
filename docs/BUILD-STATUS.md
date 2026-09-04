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

- Python suite: 223 passed.
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

The database tests run these real migrations and PostgreSQL row-level security in PGlite. Authentication and the pre-existing base tables are explicit test fixtures. Passing them does not establish compatibility with the live schema or hosted Auth configuration. Inspect the live schema and apply to a staging copy before applying to production. Test the signed-in browser journey against the migrated deployment before releasing the frontend.

Email sign-in uses the documented Supabase `signInWithOtp` interface: https://supabase.com/docs/reference/javascript/auth-signinwithotp. Hosted email delivery and redirect configuration have not been exercised. No verification email was sent during this build.

## Remaining acceptance work

**AG-01–03:** repeat the installed-wheel check if packaging changes after this checkpoint. Expand native-source contract coverage. Resolve timezone normalization and project-scoped prediction/practice selection before claiming robust cross-project history. The new private repository key prevents baseline mixing, but legacy records lack that identity.

**AG-04–07:** the native trace and coach render, but a full design pass across solo/fleet/share/mobile remains. Run actual OAuth/email → import → permalink → ACK → delete on staging with two accounts. Native claim/evidence calibration remains unmeasured; the limited coach correctly leaves it unknown. Rig import is a declared configuration, not a provider installer.

**AG-08–14:** validate advice → attempt → review across real sessions and between two people. Local attempts require explicit linking/review. Practice discovery currently searches up to 100 recent accessible versions; there is no quality ranking. Browser fixture tests cover the practice form, not every authenticated social flow. Reports are stored; no staffed moderation service or response time is claimed.

**AG-15–18:** exercise a real external agent against the hosted endpoint with a permitted action, out-of-scope denial and revoked credential. Test the tool trace, not just the client. Public evidence is client-reported counts and revision references, not raw test output; a named-test question can therefore need an unavailable-evidence answer. Agent participation in private Crews is not yet an audience scope.

**AG-19–22:** run two real test Crews through entry → fresh session → locked-Rig declaration → submission → review → appeal. Rig use and counts are client declarations. Reviews are organiser judgments, not independent automated scores. OCTACON capacity is eight, not observed participation. Crew experiments are implemented; two real team cycles and willingness to pay remain untested. No entrants, users, retention or revenue are invented.

## Review boundaries

No production migration, deployment, package publication, domain purchase, recruitment message or paid offer was sent. The original main worktree's `hack.md` edit is preserved.

Public entries, practices and discussions can be removed through source/account deletion; frozen versions prevent silent edits, not an owner's right to delete their material. The deletion migration requires explicit review of those cascade effects against the live schema.

Independent review and final release checks are still required. A green test count is not a completed roadmap ticket.
