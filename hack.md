---
doc: hack
project: AGENT GRINDER — where you post your real runs
phase: BUILD
event: CANDIDATE — Agents for Humans (Devpost, Sun 14 Sep 2026, $40K)
ruling: PENDING Oscar — AGENT GRINDER as Sep 14 entry
canonical: docs/AGENT-GRINDER-PRD.md · docs/AGENT-GRINDER-BRANDBOOK.md
last-touched: 2026-08-30
---

# AGENT GRINDER — hack.md

> **Where you post your real runs.** Log grinds from Claude, Cursor, Codex — track progression,
> run with crews, earn ACKs. Strava-shaped loop; agent-native vocabulary (see brand book).

## ⭐ NORTH STAR (the press-release line)
*"I finished a 2-hour session on agent-attack — 47 prompts, 3 commits, a personal best on focus —
and my friends gave it kudos before I closed the terminal."* A stranger sees a friend's AGENT GRINDER run
and wants their own.

## 🚀 MOONSHOT GATE (every hack.md carries this now — Oscar 2026-08-30)
**Next slice is not the plan. The 10x is.** This project ships to a *stranger*, not to Oscar.
- **The 10x:** the social layer for AI-native work — "Strava for agents." Network effect = friends' feeds.
- **The company:** the shareable/consumer face of the same data MAGNET tracks privately. Distribution engine for the whole verification thesis.
- **The stranger + date:** ≥1 person who is not Oscar uploads a run and shares it, by the hackathon deadline.
- **Kill if:** the run-card isn't cool enough that Oscar wants to post his own on day one. Coolness is the gate, measured by "would you share this," not by tests passing.

## PROMISE LINE
Where you post your real runs — after any coding-agent session, one command turns it into a card
you'd actually share. Every metric traces to the session log.

## CONSTRAINT
Every metric traces to the session log. `47 prompts` means 47 typed turns were counted, not a vibe.
On-ramp reuses Transcripto's authorship signal (typed turns only), never raw `type:user` records.

## CONSTITUTION
1. Fun first — if the card isn't shareable, nothing else matters.
2. Reuse Transcripto for authorship; do not re-solve "which turns did the human type."
3. Real metrics or none. `baseline`/`—`, never a fabricated stat.
4. Local-first on-ramp (like Transcripto); the social feed is opt-in upload, explicit.
5. No auto-post, no auto-upload — sharing is the user's click.
6. MIT.

## PLAN (risk-first — the wow spike is slice 1)
| # | Slice | Done when |
|---|-------|-----------|
| 0 | Repo + memo + this hack.md | clone works |
| 1 | **Run card generator** (session JSON → shareable HTML activity card, the signature "session route") | `python3 -m agentgrinder demo` opens a card you'd post |
| 2 | Ingest real sources: Transcripto output + GitHub events → run JSON | `agentgrinder from-transcripto` makes a real card from your last session |
| 3 | Upload + feed (Supabase): a run gets a public URL; a feed page lists runs | a second person opens your run URL cold |
| 4 | Friends + kudos; hackathon "event" pages (group runs) | two athletes, one kudos |
| 5 | Stranger pass + launch trio | STRANGER-PASS.md green; posts drafted |

## NOW (updated 1 Sep 2026 — pitch-ready)

**Pitch doc:** `docs/PITCH-2026-09-01.md` · **Demo:** `scripts/pitch-demo.sh` · **Web:** `/?pitch`

Shipped this wave: OAuth onboard · A2A/MCP · ACK + bingo · flex (Claude/Cursor/Codex) · share/claim cards · vibe/roast · rig + rig heist · ghost (anonymous) grinds · Option A seed pipeline.

**Before Sep 14:** stranger cold-read · public repo push · ≥1 non-Oscor publish.

**The solo card is now the product; the night-run card is the flex.** `agentgrinder grind` turns
ONE ordinary Claude Code sitting into the same signature drawing, one scale down — and that is the
door almost every entrant and every judge can walk through, because almost nobody runs a fleet.

- **THE GRIND TRACE.** One row per FILE ordered by first arrival, marks where the work was, the
  path it took between them, commits on the row of every file git says they contain, your prompts
  as ticks on your own line, and the longest span nobody typed through shaded across all of it.
  Same grammar as the night-run route with one substitution — *a place is a file, not a repo* —
  and that substitution is measured, not preferred (probe in `agentgrinder/solo.py`).
- **A grind is a SITTING, not a transcript.** 151 of the 194 transcripts here with a human turn
  hold more than one (re-measured 31 Aug 06:4x; the 171 this line carried does not reproduce). This was the v1 card's biggest correctness bug and it is fixed at both scales.
- **Four ship states asked of git per file**, disjoint and summing to files-edited.
- **Progression**: your place among all 625 grinds on this machine; a badge when any one of five
  measures clears that measure's top-2% bar — replayed over the 625, that is 34 cards, 5.4%
  (measured 31 Aug; "only in the top 2%" was the wrong object — five bars, not one).
- **Vocabulary**: `grind` (brand book §4), `run` kept as an alias. README rewritten off the
  retired Loop/Push lexicon it was still shipping.

Receipts, the three false sentences caught by control, and the honest "would a stranger post this":
`NIGHTRUN-2026-08-31.md`. Shots: `docs/shots/grind-*.png` (light, dark, and a MEASURED 390px).

Next: (1) a cold stranger read of the SOLO card, by someone who is not the builder; (2) slice 3 —
a grind gets a URL a second person opens cold, share = an explicit human click; (3) Codex/Cursor
parity (Cursor transcripts carry no file paths, so they honestly fall back to the v1 card).

## PREVIOUS (31 Aug 02:10)
Slices 1-2 shipped. **The NIGHT RUN card ships** — `agentgrinder nightrun [--public]` turns a whole
multi-agent night (orchestrator + every subagent lane) into one Run and draws THE SESSION ROUTE:
a human trunk, agent lanes forking at real spawn times, a lanes-open elevation profile, a commit
rail, and an annotated handoff. Rendered and looked at in light, dark and at a true 390px.
Receipts + the honest "would I post this" answer: `NIGHTRUN-2026-08-31.md`. Shots: `docs/shots/`.

Next: (1) a cold stranger read of the card; (2) slice 3/D — a run gets a URL a second person opens
cold, share = an explicit human click (redaction now exists, hosting is Oscar's); (3) give the SOLO
card the same treatment — it is still the v1 sparkline and it is the one most users generate first.
