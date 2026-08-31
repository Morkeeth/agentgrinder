# Branding brief · Agentgrinder

**Date:** 2026-08-30  
**Working name:** Agentgrinder (codename AISTRAVA in repo until rename)  
**Category:** Social fitness network for people who build with coding agents  
**One-line:** **Strava for how you work with AI.**

---

## 1. The problem we name

Coding agents log everything. Operators see almost none of it. Sessions vanish when the terminal closes. There is no shareable proof of effort, no compare-with-friends loop, no “personal best” on focus — only raw transcripts nobody reads.

**Agentgrinder** turns a real session into a **run**: distance = prompts you typed, pace, the grind curve, commits, kudos. Fun first. Metrics only from the log.

---

## 2. Audience

| Segment | Who | Job to be done |
|---------|-----|----------------|
| **Primary — the grinder** | Solo builders using Claude Code, Cursor, Codex daily | “Show I put in reps tonight” — post a run card after a hackathon session or ship night |
| **Secondary — the crew** | Hackathon teams, indie fleets, agent-science circles | Compare cadence on the same event; kudos as lightweight accountability |
| **Tertiary — the curious friend** | Non-operator who sees a card on X/LinkedIn | “What is this?” → installs, runs `agentgrinder run`, posts their own |

**Not for:** enterprise eval buyers (that’s MAGNET). Not for private ops routing (that’s ZUP).

---

## 3. Positioning

| | Strava | Agentgrinder |
|---|--------|--------------|
| Unit of work | Run / ride | **Session run** |
| Distance | km | **Typed prompts** |
| Route | GPS polyline | **Grind curve** (typed-turn rhythm) |
| Proof | Watch + GPS | **Session log** (`promptSource: typed`) |
| Social | Kudos, segments, clubs | Kudos, **events**, crew feeds |
| Vibe | Outdoor athlete | **Terminal athlete** — honest about the grind |

**Promise:** Every number on the card traces to the session. No vanity token counts. No prompt text on the public card (metrics only — privacy by default).

**Enemy:** Dashboards that invent stats. “AI productivity” slides with no receipt.

---

## 4. Name rationale · Agentgrinder

- **Agent** — the harness (Claude, Cursor, Codex), not the human’s vanity label  
- **Grinder** — reps, late-night sessions, hackathon push; not “optimize” or “unlock”  
- **Say it:** AGENT-grine-der (three syllables, stress on GRIND)  
- **Handle:** `@agentgrinder` · hashtag `#agentgrinder` · event tag `#grind`  

**Alternatives considered (parked):** AISTRAVA (too abstract), MAGNET (B2B eval, not social), “RunLog” (generic).

---

## 5. Brand personality

| Axis | We are | We are not |
|------|--------|------------|
| Tone | Direct, sweaty, proud of reps | Corporate AI, wellness spa |
| Humor | Dry — “2h 20m moving time” on a coding session | Meme chaos, mascot animals |
| Visual | Night asphalt, one hot accent, big numbers | Cream serif startup, purple gradient hero |
| Data | Receipted or `—` | Fake precision (“run #2,914”) |
| Social | Opt-in share, kudos | Auto-post, leaderboard shame |

**Voice sample (on-card):**  
*“47 prompts · 2h 20m · 2:59/prompt · ★ focus PB”*  
Not: *“Unlock your AI potential seamlessly.”*

---

## 6. Competitive frame

| Product | Overlap | Our wedge |
|---------|---------|-----------|
| GitHub contribution graph | Activity heatmap | **Session-native** — prompts, tools, grind curve, not commits alone |
| WakaTime / timing apps | Time in editor | **Authorship** — typed turns only, not passive presence |
| Transcripto | Authorship analytics | **Social face** — shareable card + feed (Transcripto = on-ramp) |
| MAGNET | Eval ledger | **Consumer distribution** — MAGNET stays private engine |
| Strava | Athletic social | **Same loop, different sport** — terminal sport |

---

## 7. Signature device (ONE THING)

**THE GRIND CURVE** — typed prompts per time bucket drawn as an elevation profile. The shape *is* the session. Remove it and the card becomes a KPI box.

Rules:
- Derived only from `rhythm[]` in run JSON  
- Peak marker = hardest stretch (max bucket)  
- Never decorative gradient underlay without data  

---

## 8. Deliverables this brief feeds

| Artifact | Path |
|----------|------|
| Full PRD (A2A) | `docs/brand/PRD-A2A-AGENTGRINDER.md` |
| Brandbook (tokens, type, UI law) | `docs/brand/BRANDBOOK-AGENTGRINDER.md` |
| Implementation | `aistrava/render.py` → rebrand pass after Oscar approves book |

---

## 9. Success criteria (brand)

1. Stranger names the product from a screenshot alone (“Strava for coding agents”).  
2. Oscar posts his own run card unprompted after a real session.  
3. One non-Oscar uploads a run and shares URL before Sep 14 (Agents for Humans) or Sep 9 (Cinema fallback).  
4. No slop tells from design-taste kill list on shipped surfaces.

---

## 10. Open decisions (Oscar)

- [ ] **Venue:** Agents for Humans (Sep 14) primary vs Agentic Cinema (Sep 9)  
- [ ] **Repo rename:** `aistrava` → `agentgrinder` on GitHub  
- [ ] **Domain:** TBD  
- [ ] **MAGNET relationship:** subtitle “powered by MAGNET” on eval slice vs silent  

**Next build step after brand approval:** apply brandbook tokens to `render.py` + export `tokens/agentgrinder.css`.
