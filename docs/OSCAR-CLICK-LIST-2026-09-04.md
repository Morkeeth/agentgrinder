# OSCAR-CLICK-LIST · Sep 14 pack spine · 2026-09-04

**Oscar only.** Cloud prepared Phase 0 + Phase 1. Does not execute outward acts.
Devpost submit · buy domain · create PyPI token · film · post publicly = **your click**.

---

## What must be true before Devpost (checklist, not a submit)

Re-check each item at its object the day you submit. Do not trust a figure written earlier.

| # | Must be true | How to verify at the object |
|---|--------------|-----------------------------|
| 1 | Claim rule numbers on the live methodology page match `docs/claim-calibration.json` | `python3 scripts/recompute-claim-calibration.py --check-docs` then open https://agentgrinder.vercel.app/methodology |
| 2 | Live Get Started / pitch do **not** hand bare `pip install -e .` | View-source or `/?onboard` + `/?pitch` after Vercel redeploy of this branch's `site/index.html` |
| 3 | Cold clone one-liner reaches a card (or honest empty-HOME → demo) | `git clone … && cd agentgrinder && python3 -m agentgrinder grind` under an empty `HOME`, then `demo` |
| 4 | Claude / Cursor / Codex each reach a card from fixture HOMEs | `python3 scripts/stranger-three-homes.py --local-cmd` → overall PASS |
| 5 | Card dashes for correction rate + promised are `—`, never `0` | `python3 -m agentgrinder demo --no-open` and read the five-number row |
| 6 | Evidence-matching still disclosed as **unmeasured** on methodology | `/methodology` contains "Still unmeasured" for evidence matching |
| 7 | Strands eligibility ruled | `docs/MOONSHOT-MEMO-2026-09-02.md` OPEN Q #1 — **blocking**; cloud does not ship a wrapper without your ruling |
| 8 | Public repo + live site | https://github.com/Morkeeth/agentgrinder · https://agentgrinder.vercel.app |
| 9 | Screenshots eyeballed | `docs/shots/` at real size (OCR not run) |
| 10 | One non-Oscar stranger cold-ran | Recruit template below; their note exists outside this repo |

If any row is false, **do not submit**. Fix or disclose.

---

## Your clicks (in order)

### 1. Vercel redeploy
Push/merge the Phase 0+1 branch to `main` (or redeploy the preview). Confirm:
- `/?onboard` grind step = clone + `python3 -m agentgrinder grind` (no bare pip)
- `/?pitch` same
- `/methodology` still prints held-out 0.63 / 0.66 (re-derived, not remembered)

### 2. Supabase OAuth redirect URLs
Project `xengine-review` (schema `agentgrinder`). Auth → URL Configuration:

| URL | Purpose |
|-----|---------|
| `https://agentgrinder.vercel.app` | Production |
| `https://agentgrinder.vercel.app/` | Trailing slash |
| `http://localhost:3000` | Local web (if used) |

**Verify:** `agentgrinder login` on your machine completes without redirect error.

### 3. Film (your hands)
Shot list: `docs/VIDEO-SHOTLIST.md` · scout: `docs/FILM-SCOUT-COMMANDS.md`.
Cloud does not film.

### 4. Devpost — only after the table above is green
1. https://agentsforhumans.devpost.com/ → Join
2. Fields from `docs/DEVPOST-READY.md` / `docs/DEVPOST-DESCRIPTION.md`
3. Upload 3 screenshots from `docs/shots/`
4. 5-min demo video
5. Public repo link
6. Optional: builder.aws blog for bonus

**Do not submit until Strands ruling** (row 7).

### 5. Stranger recruit — one friend DM

```
Hey — I'm entering Agent Grinder in the Agents for Humans hackathon (Sep 14).
It's "Strava for coding-agent sessions" — one command after Claude/Cursor/Codex turns
your session into a shareable card (metrics only, no prompt text).

Would you cold-run this and tell me honestly if you'd post the card?

git clone https://github.com/Morkeeth/agentgrinder.git
cd agentgrinder
python3 -m agentgrinder grind
# if that says no session: python3 -m agentgrinder demo

No account, no keys. Takes ~2 min. Brutal honesty welcome.
```

---

## What cloud already put on disk (do not re-do; do re-verify)

- Phase 0 numbers: `docs/CLAIM-RULE-CALIBRATION-2026-09-03.md` · `docs/claim-calibration.json`
- Recompute: `scripts/recompute-claim-calibration.py`
- Evidence embarrassment (synthetic): `tests/test_evidence_match_eval.py`
- Phase 1 evidence: `docs/stranger-three-homes-2026-09-04.md` (+ `.json`)
- Live pip-lie receipt (until redeploy): `docs/stranger-three-homes-LIVE-2026-09-04.md`
- Wave receipt: `docs/CLOUD-RECEIPT-grinder-2026-09-04.md`
