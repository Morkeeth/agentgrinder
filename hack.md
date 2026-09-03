---
doc: hack
project: AGENT GRINDER — where you post your real runs
phase: BUILD
event: CANDIDATE — Agents for Humans (Devpost, Sun 14 Sep 2026, $40K)
ruling: EYES 1 Sep — Grinder is the product; MAGNET submits Sep 14 · Oscar 2026-09-04 — Grinder STAYS for Sep 14
canonical: docs/AGENT-GRINDER-PRD.md · docs/AGENT-GRINDER-BRANDBOOK.md
last-touched: 2026-09-04 (cloud)
---

# AGENT GRINDER — hack.md

## STATE 2026-09-04 (cloud wave)
- `Morkeeth/agentgrinder` PUBLIC. Live agentgrinder.vercel.app. Claim rule calibrated on main
  (`docs/CLAIM-RULE-CALIBRATION-2026-09-03.md`, fingerprint `e49d8713c3c2df38`).
- Oscar ruled: **Grinder is in** for Sep 14. Cloud owns Phase 0 + Phase 1. Oscar owns film /
  rulings / Devpost submit. Outward acts = Oscar's click.
- Phase 0 numbers are on disk. Evidence matching still has **no** real label set.
- Live copy-button INSTALL_CMD is clone-only (no pip). Get Started / pitch still handed
  `pip install -e .` — measured fail on stock macOS pip 21.2.4 (PEP 660).

> **Where you post your real runs.** Log grinds from Claude, Cursor, Codex — track progression,
> run with crews, earn ACKs. Strava-shaped loop; agent-native vocabulary (see brand book).

## ⭐ NORTH STAR
*"I finished a 2-hour session on agent-attack — 47 prompts, 3 commits, a personal best on focus —
and my friends gave it kudos before I closed the terminal."* A stranger sees a friend's AGENT GRINDER run
and wants their own.

## PROMISE LINE
Where you post your real runs — after any coding-agent session, one command turns it into a card
you'd actually share. Every metric traces to the session log. The headline metric carries a
**measured** precision/recall on the claim detector, or the card does not pretend.

## CONSTRAINT
Every metric traces to the session log. `47 prompts` means 47 typed turns were counted, not a vibe.
On-ramp reuses Transcripto's authorship signal (typed turns only), never raw `type:user` records.
Unmeasured columns print `—` with a tooltip that names the missing fact. Never invent a label set.

## OPEN QUESTIONS
1. **BLOCKING (Oscar):** Strands Agents SDK eligibility for Devpost (`docs/MOONSHOT-MEMO-2026-09-02.md` #1). Cloud does not implement Strands wrapper without ruling.
2. **Evidence matching:** `evidence_matches` has no hand-labelled real corpus on this machine. Synthetic embarrassment eval may ship; real precision/recall for the share stays unmeasured until a label set exists.
3. **Non-Oscar stranger recruit:** one friend cold-runs and says whether they would post the card.

## CONSTITUTION
1. Fun first — if the card isn't shareable, nothing else matters.
2. Reuse Transcripto for authorship; do not re-solve "which turns did the human type."
3. Real metrics or none. `baseline`/`—`, never a fabricated stat.
4. Local-first on-ramp (like Transcripto); the social feed is opt-in upload, explicit.
5. No auto-post, no auto-upload — sharing is the user's click.
6. MIT.
7. A box is truth only when its done-when was RUN. Never carry a number from a prompt — re-derive at the object. Never rank by a title.

## PLAN (risk-first — wave 2026-09-04)
| # | Slice | Done when |
|---|-------|-----------|
| 1 | **Phase 0 — calibrate / honesty** | methodology numbers re-derived from `docs/claim-calibration.json`; card does not pretend unmeasured columns; broken stranger install strings removed from site |
| 2 | **Phase 1 — stranger → card** | three temp HOMEs (Claude / Cursor / Codex) following the live site; each reaches a card **or** honest BLOCKED with exact failing step; evidence on disk |
| 3 | **Sep 14 pack spine (docs only)** | OSCAR-CLICK-LIST + what must be true before Devpost — do not submit |
| 4 | Receipt + tests | `docs/CLOUD-RECEIPT-grinder-2026-09-04.md`; tests green for touched code |

## NOW (updated 2026-09-04 — end of cloud wave)

**Slice 1 (Phase 0) DONE when run:**
`python3 scripts/recompute-claim-calibration.py --check-docs` → shipped 0.63/0.66, v0 0.32/0.37;
site Get Started/pitch bare-pip removed; evidence synthetic eval red-lights the generic matcher.

**Slice 2 (Phase 1) DONE when run:**
`python3 scripts/stranger-three-homes.py --local-cmd` → overall PASS (empty + claude + cursor + codex).
Live fetch → `PASS_WITH_LIVE_PIP_LIE` until Oscar redeploys.

**Slice 3 (Sep 14 spine) DONE:** `docs/OSCAR-CLICK-LIST-2026-09-04.md` — docs only, no submit.

**Next (Oscar):** redeploy site · Strands ruling · film · stranger recruit · Devpost click.

Receipt: `docs/CLOUD-RECEIPT-grinder-2026-09-04.md`

## LOG

| When | What |
|------|------|
| 2026-09-04 | WAVE start: read hack.md, claim calibration, live site. Re-derived holdout P/R from `docs/claim-calibration.json`: shipped 0.63/0.66, v0 0.32/0.37. Fingerprint matches. |
| 2026-09-04 | OPENED THE LIVE OBJECT: INSTALL_CMD is clone-only; Get Started + pitch still print `pip install -e .` (the Mac stock-pip failure). |
| 2026-09-04 | Cold empty HOME: grind exits 1 with paths named + demo hint. `demo --no-open` paints card with correction/promised/reach as `—`. |
| 2026-09-04 | BUILD: killed bare pip on onboard/pitch; Cursor/Codex claim rule + `--json`; stranger-three-homes script; evidence embarrassment eval; Sep 14 click list; receipt. |
| 2026-09-04 | VERIFIED: `stranger-three-homes.py --local-cmd` PASS; live fetch PASS_WITH_LIVE_PIP_LIE; 60 targeted tests passed. |
| 2026-09-02 | LOOP 0–5: stranger pass, Devpost pack, pitch-demo sample fallback (prior wave) |

## PREVIOUS (2 Sep 2026 — stranger pass)
See git history / `docs/CLOUD-RECEIPT-grinder-ambitious-2026-09-02.md`. Claim-rule calibration landed on main 3 Sep (`fable/claim-rule-2026-09-03`).
