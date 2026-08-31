# AGENT GRINDER — what a Run is, what to post, how profiles rank

The foundational definitions. Strava's genius is that it auto-records *every* workout, not just races.
AGENT GRINDER copies that: log *every session*, automatically, not just finished projects.

## What is a Run?
**A Run = one bounded agent work session** — from when you start working with an agent to when the
session closes (or you call `agentgrinder run`). Like a Strava activity is one workout, not your whole
fitness journey. A Run is **not** a finished project, a launch, or a PR to main. It's a *session*.

A session qualifies as a Run when it clears a floor (so noise doesn't post): e.g. **≥5 typed prompts
or ≥10 minutes**. Below that it's a warm-up, not logged.

## What people post — automatically, not manually
The whole point is **low-friction, high-frequency**. You don't decide to "post a project." The
CLI/MCP logs **every qualifying session**, you approve (or auto-approve public/private rules), and it
streams to your feed. Strava-cadence: a few a day, honest, ambient. The feed is **daily grind**, not
launch announcements.

Default posture: **auto-draft every session → you set a standing rule** (auto-public, auto-private,
or ask-each-time). Titles/projects are yours to edit; metrics flow automatically.

## What data is interesting (the shareable signals)
Basics: typed prompts (distance), duration (time), pace, commits, tool calls (effort).
The signals people actually care about:
- **Grind curve** — the session's rhythm/intensity (elevation profile).
- **Code route** — the journey across your codebase's regions (the GPS map). Focused fix = one
  region; refactor = a sweep. Privacy-safe (region indices, never file names).
- **Ship** — did it produce a *checked* release? (the outcome that matters)
- **Recovery** — did it fail then fix? A comeback is more interesting than a clean run.
- **The rig** — model, harness, MCPs, skills used. **People want to copy setups** — this is huge.
- **Streak** — consecutive days grinding.
- **PRs** — longest session, most prompts, most commits, best sustained pace.

## How a profile ranks (without becoming shame-y / gameable)
**Never** a global vanity leaderboard, never token/prompt count (kill-listed, gameable). Rank on
**consistency + real output + earned recognition**, shown as a qualitative shape, not one Elo:
- **Consistency** — streak, sessions/week (the Strava retention signal).
- **Ships** — count of *checked* releases (real output, not activity).
- **Recognition** — ACKs *received*, evidence-linked, same-owner excluded (can't self-inflate).
- **Range** — variety of projects/regions (breadth of craft).
A profile reads like **"consistent shipper · deep-focus · 14-day streak"** + a few real stats.
Ranking is **among friends / within an event**, never a global "top builders" board.

## Fun onboarding (the "boom" moment)
The magic: **install → `agentgrinder run` → it instantly shows a beautiful card of a session you
already did today.** No setup, immediate payoff — like Strava showing your first recorded run. The
ASCII runner + the code-route map + your *real* numbers from work you just finished = the delight.
Then "push it" and your profile lights up. First-run feeling: *"oh — it already knows what I did."*

Onboarding steps, 60 seconds:
1. Sign in with GitHub (identity only).
2. `agentgrinder run` — see your last session as a Run (local, nothing sent).
3. Push it — your profile has its first Run + your rig.
4. See one public run in the feed, give it an ACK.

## THE GOAL (proposed)
> **A stranger installs AGENT GRINDER, and within 60 seconds sees a Run auto-made from a session they
> already did today, understands what a Run is without being told, pushes it, and lands on a profile
> worth ranking — all without any prompt text or code ever leaving their machine.**

Done-when: cold install → first Run visible → pushed → profile shows rig + Run + a grind-score shape,
with a visible "exactly these numbers were sent" receipt. Build the onboarding to hit that.

---
## THE GROWTH SEQUENCE (locked) — all three, in order, compounding
AGENT GRINDER becomes all three. They are LAYERS that compound, not competing paths. Private-coach
is the wedge (day-one value, privacy-safe, useful with zero other users); each layer earns the next.

1. **Layer 1 — Private coach (the wedge, launch).** Your own insight, private by default. Kills the
   "scared of it" fear, works solo, no network needed. *Come for the tool.*
2. **Layer 2 — Proof-of-work profile (the bridge).** Your private grind becomes a shareable, verifiable
   record — rig, ships, grind score. The moment you *want* to share the link. Turns single-player value
   into a public artifact. *This is what makes coach users into profiles.*
3. **Layer 3 — Social network (the compounding).** Feed, ACK, crews, events, agent-to-agent comparison.
   Network effect, once there are profiles worth following. *Stay for the network.*

Why sequence beats launching all-at-once: a social feed with no users is a graveyard (chicken-and-egg);
a coach is valuable to user #1 on day one. So we LEAD with coach, ship proof as the share moment, and
the social layer lights up as the base grows. The schema (profiles/runs/follows/acks) and the app
already scaffold all three — coach is home, the profile is the proof surface, Explore is the social layer.
