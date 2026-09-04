# PRD · A2A · Agentgrinder

**Product:** Agentgrinder  
**Protocol name:** **A2A** — *Agent Activity* (run schema + social graph)  
**Version:** 0.1 draft · 2026-08-30  
**Owner:** Oscar  
**Status:** Slice 1–2 shipped locally · Slice 3–5 spec’d here

---

## 1. Summary

Agentgrinder is a social fitness network for people who build with coding agents. **A2A** is the open run schema and API surface: session → run JSON → public activity → feed → kudos → events.

**North star metric:** Weekly active grinders who **share ≥1 run** (not just generate locally).

---

## 2. Goals & non-goals

### Goals (v1 — Sep 2026)

| # | Goal | Metric |
|---|------|--------|
| G1 | Run card people post unprompted | Oscar + ≥1 stranger share |
| G2 | Real ingest from Claude Code | `agentgrinder run` on latest `.jsonl` |
| G3 | Public run URL | Cold open without auth |
| G4 | Hackathon event page | ≥2 athletes on same event |
| G5 | Authorship integrity | 100% metrics from `typed` turns |

### Non-goals (v1)

- Prompt content on public cards  
- Full auth/OAuth (magic link or GitHub later)  
- Agent-to-agent autonomous posting (humans share)  
- Leaderboards / global rank (kudos only)  
- Mobile native apps  

---

## 3. Users & stories

### Grinder (primary)

- As a grinder, after a session I run one command and get a card I’d post.  
- As a grinder, I see distance (typed prompts), pace, and grind curve — not token vanity.  
- As a grinder, I opt in to upload; nothing auto-posts.

### Crew member

- As a crew member, I kudos a friend’s run without commenting.  
- As a crew member, I join a hackathon **event** and see our runs on one page.

### Stranger (launch gate)

- As a stranger, I open a run URL with no account and understand what happened.  
- As a stranger, I install CLI and reproduce my own card in &lt;10 minutes.

---

## 4. A2A — Agent Activity schema

### 4.1 Run object (canonical)

```json
{
  "a2a_version": "0.1",
  "run_id": "uuid",
  "athlete": { "handle": "oscar", "display": "Oscar" },
  "title": "repo A WAVE-7 moonshot",
  "harness": "claude-code",
  "project": "repo A",
  "started": "2026-08-30T14:00:00Z",
  "duration_s": 8400,
  "turns_typed": 47,
  "tool_calls": 213,
  "files_touched": 12,
  "commits": 3,
  "rhythm": [2, 5, 8, 12, 9, 4, 3, 4],
  "source": {
    "session_path_hash": "sha256:…",
    "ingest": "native-claude-jsonl"
  },
  "privacy": { "show_prompts": false, "public": true }
}
```

### 4.2 Derived display (card)

| Field | Source | Display label |
|-------|--------|---------------|
| `turns_typed` | count `promptSource==typed` | **Distance** |
| `duration_s` | first/last timestamp | **Moving time** |
| `duration_s / turns_typed` | derived | **Pace** |
| `tool_calls` | assistant tool_use count | **Effort** |
| `files_touched` | edit/write paths | **Segments** |
| `commits` | git hook or manual | **Commits** |
| `rhythm` | bucketed typed counts | **Grind curve** |

Missing field → display `—`, never guess (constitution).

### 4.3 Activity types (A2A enum)

| Type | Description |
|------|-------------|
| `session_run` | Default — one coding session |
| `event_run` | Tagged to an `event_id` (hackathon) |
| `crew_run` | Visible to crew only (v1.1) |

### 4.4 Social objects

| Object | Fields | v1 |
|--------|--------|-----|
| **Kudo** | `run_id`, `from_handle`, `created` | ✅ |
| **Comment** | `run_id`, `body` (280 char) | optional |
| **Event** | `slug`, `name`, `starts`, `ends`, `venue` | ✅ |
| **Feed** | ordered `run_id[]` per athlete or event | ✅ |

---

## 5. Feature slices (build plan)

| Slice | Feature | Done when | Status |
|-------|---------|-----------|--------|
| **0** | Repo, hack.md, memo | clone + demo | ✅ |
| **1** | Run card HTML + grind curve | `demo` opens postable card | ✅ |
| **2** | Native Claude ingest | `run` on latest session | ✅ |
| **2b** | Transcripto ingest | `from-transcripto` parity | 🔲 |
| **2c** | GitHub enrich | commits + repos on profile | 🔲 partial |
| **3** | Upload + public URL | Supabase `runs` table + `/r/{id}` | 🔲 |
| **4** | Feed + kudos + events | 2 athletes, 1 event page | 🔲 |
| **5** | Stranger pass + launch | STRANGER-PASS.md green | 🔲 |

---

## 6. System architecture

```
┌─────────────────┐     ingest      ┌──────────────┐
│ Claude / Cursor │ ──────────────► │ Run JSON     │
│ session logs    │                 │ (A2A 0.1)    │
└─────────────────┘                 └──────┬───────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────┐
         ▼                                 ▼                     ▼
  ┌─────────────┐                  ┌─────────────┐        ┌─────────────┐
  │ Local card  │                  │ Supabase    │        │ Transcripto │
  │ render.html │                  │ runs, kudos │        │ authorship  │
  └─────────────┘                  │ events      │        │ on-ramp     │
                                   └──────┬──────┘        └─────────────┘
                                          │
                                          ▼
                                   ┌─────────────┐
                                   │ Public feed │
                                   │ /u /e /r    │
                                   └─────────────┘
```

**Stack (v1):** Python CLI · static HTML cards · Supabase (Postgres + storage) · optional Vercel/Cloudflare for `/r/` pages.

**MAGNET integration (later):** private eval deltas attached to run metadata — not on public card.

---

## 7. API surface (A2A v0.1)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/v1/runs` | upload token | Create run, return `run_id` + public URL |
| `GET` | `/v1/runs/{id}` | none | Public run JSON + render hints |
| `GET` | `/v1/athletes/{handle}/feed` | none | Paginated runs |
| `GET` | `/v1/events/{slug}/feed` | none | Event runs |
| `POST` | `/v1/runs/{id}/kudos` | session | Add kudo |
| `GET` | `/v1/runs/{id}/kudos` | none | List kudos |

CLI wraps upload: `agentgrinder push [--event slug]`.

---

## 8. Metrics & analytics

### Product

- Runs generated (local)  
- Runs uploaded (public)  
- Kudos per run (median)  
- Stranger cold-open success (manual STRANGER-PASS)  
- Time to first card (install → card &lt;10 min)

### Integrity

- % runs with `source.ingest` declared  
- Authorship audit sample: typed count vs Transcripto gate  

### Not tracked (v1)

- Prompt content, file paths on public objects  
- Token counts  

---

## 9. Privacy & trust

1. **Default private** — card generates locally; upload is explicit.  
2. **No prompt text** on public run or feed.  
3. **Metrics only** — athlete, project name, harness, counts, grind curve.  
4. **Session hash** — prove provenance without exposing path.  
5. **Delete** — athlete can delete uploaded run (GDPR-simple v1).

---

## 10. Launch requirements (Agents for Humans · Sep 14)

| Requirement | Owner |
|-------------|-------|
| 3-min demo video (card + feed + kudos) | Oscar |
| Public GitHub repo | Oscar |
| Devpost submit | Oscar |
| ≥1 stranger run URL | Product |
| README cold path ≤10 min | Product |
| Architecture diagram | Product |

**Demo script beat:**  
Terminal → `agentgrinder run` → card opens → upload → share URL → friend kudos on feed.

---

## 11. Risks

| Risk | Mitigation |
|------|------------|
| “Ick” — sharing work habits | Metrics not content; private default |
| GitHub-only enough | Transcripto typed-turn moat |
| Strava trademark vibe | Distinct visual system (brandbook); “inspired by athletic social” |
| Low stranger adoption | Hackathon event pages = built-in crew |
| Name confusion with “grinder” apps | Always pair with tagline “Strava for agents” |

---

## 12. Appendix · CLI (target)

```bash
agentgrinder demo              # sample card
agentgrinder run [session]     # latest Claude session → card
agentgrinder card run.json     # render JSON
agentgrinder push [-e EVENT]   # upload → public URL
agentgrinder feed [@user]      # open feed in browser
agentgrinder event create      # hackathon page
```

Current implementation: `python3 -m aistrava` (rename pending).
