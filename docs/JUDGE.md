# Judge path · Agent Grinder (under five minutes)

This is the product path a stranger can complete without a walkthrough.

**Branch for this candidate work:** the isolated branch opened from `day/2026-09-11-grinder-ambition` (expected parent `be5704c`). Production `main` and the live site are not assumed to include it.

## What to open

1. Hosted preview of this branch, if the coordinator attached one, **or**
2. Local: from the repo root

```bash
python3 -m http.server 8765 --directory site
```

Then open `http://127.0.0.1:8765/?example` on a phone-width window and a desktop window.

Label: **BUNDLED EXAMPLE · public-safe fixture**. Not live users. Not a live language model.

The bundled example (`site/example.js`) is labelled onboarding only. Persistence, adoption and revocation are the real moments/practices RPCs, exercised in an isolated disposable Postgres.

## The five-minute loop

1. **Landing** (`/`). One start action: *Try the bundled example*. Signature on screen: *I tried this. Show me what changed.* Bring-your-own copy is private by default. No account.
2. **Example** (`/?example`). A deterministic Strands/tool sequence (recorded) finds a **named** friction: `test_draft_renders` was claimed without evidence in that turn. Consequence and one experiment are visible. Mode banner says this is **not autonomous reasoning**.
3. Accept or edit the experiment. Freeze the fixture sitting as baseline.
4. Return with the later labelled sitting. Keep / change / drop / incomparable. Original measurements remain. One observed outcome, not a score-as-proof.
5. Author a moment. Tick the review box. Switch to **another builder (fixture role)** — their own baseline, not the author's counts. Return, save an outcome, optional PNG/caption review (`/?example=share`).
6. **Persisted APIs (disposable, not production):**

```bash
npm run test:journey
python3 scripts/check-persisted-journey.py
```

Two authenticated TEST DATA contexts hit the real `grinder_start_attempt` / `grinder_review_attempt` / `grinder_adopt_moment` RPCs. Coach → accept/edit on the same card → freeze own baseline → later run and review → deliberate share → second builder adopts onto **their** baseline → their outcome → revocation leaves owned work. Different harnesses with claim counts do not get a green comparable badge.

7. **Live model (optional, your machine only):**

```bash
python3.12 -m venv .venv && .venv/bin/pip install -e ".[coach]"
.venv/bin/agentgrinder coach --live-status
```

If AWS/Bedrock is missing, that command prints the **exact** missing item and does not invent a live review. Do not spend against a paid provider for this judgement.

Bring-your-own: `python3 -m agentgrinder grind` then `grind --push`. Import audience defaults to **private**. Coach text is metrics-only: directory paths are stripped before import, cards, JSON and push.

## What success looks like

- A stranger gets the promised value without an explanation.
- Demo and live modes cannot be confused.
- A second builder's attempt sits on **their** freeze, and revocation language is on the return.
- Community (`/?community`) leads with techniques to try, then Forum / Crews / Challenges. Empty public lists stay empty — no fake adoption.

## What this is not

Hosted production acceptance. Independent real-world adoption. A Bedrock session unless you already have credentials and choose to spend. Private transcripts do not belong in Git or in the cloud preview. The disposable PGlite journey is TEST DATA, not live users.
