# Stranger → card · three HOMEs · 2026-09-03

**INSTALL_CMD source:** `local site/index.html`

```
git clone https://github.com/Morkeeth/agentgrinder && cd agentgrinder && python3 -m agentgrinder grind
```

Bare `pip install -e .` still on that page: **no**

| Path | Status | Detail |
|------|--------|--------|
| empty HOME → grind | PASS | rc=1, names paths=True, points at demo=True, demo rc=0, demo card=True |
| claude HOME → grind | PASS | rc=0, card=True (29889B), harness=Claude Code, turns=3, claims=1/2, artifacts=1, headline=0.6667 |
| cursor HOME → grind | PASS | rc=0, card=True (7452B), harness=Cursor, turns=2, claims=0/1, artifacts=1, headline=0.5 |
| codex HOME → grind | PASS | rc=0, card=True (7310B), harness=Codex, turns=2, claims=0/1, artifacts=None, headline=None |

**Overall:** `PASS`

Machine receipt (counts only): `docs/stranger-three-homes-2026-09-04.json`

Fixtures are synthetic lines written for this script (Claude uses `samples/sample_session.jsonl`). No real transcript text is stored.
