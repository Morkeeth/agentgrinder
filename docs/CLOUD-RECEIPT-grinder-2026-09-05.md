# CLOUD-RECEIPT · grinder · 2026-09-05

Day slice: returning user finds a real run, sees grind-trace attribution, and a next practice — on current `main` tip (`83ad116` + this branch).

---

## SHIPPED

- **Run-object grind-trace attribution** — `grindTrace(r)` on run cards and the featured card; `GrinderContract.trace` now captions every history/comparison/challenge trace with `trace_basis` or the honest line `Trace time basis unknown` (never invents a basis).
- **Coach plan framed as Next practice** — on the run card, featured card, and CLI `render_card`; owner CTA `Save as my next practice` prefills `/?practices`.
- **Journey readiness panel** on `/?run=…` — names the missing fields for Progress/practice baselines (`trace_basis`, `measurement_revision`, coach plan).
- **Offline three-beat journey** — `samples/returning_run.json` + `scripts/returning-journey.py` (attributed arm vs naive baseline).
- **Tests** — `tests/test_returning_journey.py`; progress fixture asserts attribution on history tiles.

Not claimed: live deploy of these bytes (Oscar/Vercel). Live featured row still lacks `trace_basis` and `measurement_revision`.

---

## VERIFIED

| Claim | Command | Result |
|-------|---------|--------|
| Offline journey beats naive baseline 3–0 | `python3 scripts/returning-journey.py` | exit 0; attributed beats=3, naive beats=0 |
| Fixture card names basis + Next practice | `python3 -m agentgrinder card samples/returning_run.json -o /tmp/returning-card.html --no-open` then inspect HTML | `trace-basis` + `Next practice` present |
| Contract trace names unknown basis | `pytest tests/test_returning_journey.py` | 3 passed |
| Regression suite | `python3 -m pytest -q` | **242 passed, 1 skipped** |
| Progress UI fixture (history→compare→practice) + attribution | `CHROME_BINARY=/usr/local/bin/google-chrome python3 scripts/check-progress-fixtures.py` | exit 0; `.trace-basis` present |
| Hosted PostgREST shapes | `python3 scripts/check-hosted.py` | exit 0; 5 query shapes |
| Live featured run object | journey script live probe of `28d5d0b7-…` | rhythm ✓, coach_plan ✓, **trace_basis ✗**, **measurement_revision ✗**; live HTML **lacks** `grindTrace` until deploy |
| Live install lines | curl homepage; inspect `INSTALL_CMD` / `COACH_CMD` | Install is clone+`python3 -m agentgrinder grind` (no bare pip). Coach line uses `python3.12 -m venv` + `.venv/bin/pip`. Old pip-lie string remains only in a **comment**. |

---

## WRONG

1. **Live featured run cannot complete the three-beat object journey** — `trace_basis` and `measurement_revision` are null on the hosted row. UI will name the gaps after deploy; it cannot invent the missing facts. Backfill is Oscar-only (DB write).
2. **These site bytes are not on Vercel yet** — live probe `live_source_has_grindTrace=false`. Strangers still see the pre-slice run page until Oscar merges/deploys.
3. **Zero public practices** on the hosted table (`content-range=*/0`) — Browse practices is still a graveyard; coach-plan → private practice is the path this slice wires.
4. **Signed-in hosted walkthrough** (real account: mine → compare → practice) was not completed here — OAuth is Oscar-only; fixtures cover the forms, not a real identity.
5. **Did not film / Devpost / stranger recruit** — stop at the door per brief.

---

## Oscar-only (stop at the door)

- Film
- OAuth / signed-in hosted walkthrough of Progress
- Devpost submit
- Redeploy Vercel after merge
- Optional: backfill `trace_basis` / `measurement_revision` on existing runs that actually have them at source

## Reproduce

```sh
python3 scripts/returning-journey.py
python3 -m agentgrinder card samples/returning_run.json --no-open
python3 -m pytest -q
CHROME_BINARY=/usr/local/bin/google-chrome python3 scripts/check-progress-fixtures.py
python3 scripts/check-hosted.py
```
