# Brandbook · Agentgrinder

**Version:** 1.0 · 2026-08-30  
**Applies to:** Run cards, profile, feed, event pages, Devpost, X/LinkedIn assets  
**Design law:** ONE signature device — **the Grind Curve**. Everything else stays quiet.

---

## 1. Brand lockup

**Wordmark:** AGENTGRINDER  
**Style:** All caps, tight tracking, no icon required v1  
**Lockup with tagline:**

```
AGENTGRINDER
Strava for how you work with AI.
```

**Short taglines (pick one per surface):**

- Strava for how you work with AI. *(primary)*  
- Log the grind. Share the run.  
- Your session, receipted.

---

## 2. Logo usage

v1 is **wordmark-only** — no mascot, no robot, no gradient orb.

| Rule | Spec |
|------|------|
| Clear space | ≥ height of “G” on all sides |
| Min size | 80px wide digital |
| On dark | `#F2F4F8` wordmark |
| On light | `#0B0D10` wordmark |
| Accent | Never color the whole wordmark orange — accent is for data + curve |

---

## 3. Color system (OKLCH)

**Direction:** Night terminal — asphalt ground, one grinder spark. Not cream/serif startup. Not purple gradient.

### Core tokens

| Token | OKLCH | Hex (approx) | Use |
|-------|-------|--------------|-----|
| `--ag-bg` | `oklch(0.14 0.01 260)` | `#0B0D10` | Page background (default dark) |
| `--ag-surface` | `oklch(0.19 0.012 260)` | `#161A21` | Cards, panels |
| `--ag-line` | `oklch(0.28 0.01 260)` | `#252B35` | Borders, stat grid |
| `--ag-ink` | `oklch(0.94 0.01 260)` | `#EEF1F5` | Primary text |
| `--ag-muted` | `oklch(0.62 0.02 260)` | `#98A1AF` | Secondary, labels |
| `--ag-spark` | `oklch(0.68 0.19 45)` | `#FF5C1A` | Accent — curve, PB badge, kudos hover |
| `--ag-spark-dim` | `oklch(0.68 0.19 45 / 0.28)` | — | Curve fill gradient top |

### Light mode (optional, cards shared to LinkedIn)

| Token | Hex | Use |
|-------|-----|-----|
| `--ag-bg` | `#ECEEF2` | Page |
| `--ag-surface` | `#FFFFFF` | Card |
| `--ag-ink` | `#14171F` | Text |
| `--ag-spark` | `#E84E0E` | Accent (slightly deeper for contrast) |

**Banned:** `#F4F1EA` cream paper · purple/indigo heroes · lone acid-green on black · amber pulsing status dots.

---

## 4. Typography

| Role | Face | Weight | Notes |
|------|------|--------|-------|
| **Display / wordmark** | **IBM Plex Sans** | 700 | UI chrome, athlete name |
| **Stats (hero numbers)** | **IBM Plex Mono** | 600 | Distance, time, pace — largest type on card |
| **Labels** | IBM Plex Sans | 500 | 11px uppercase, +0.05em tracking |
| **Body** | IBM Plex Sans | 400 | 15px / 1.5 |

**Hierarchy law:** Three headline stats are **22–28px mono**; labels are **11px** muted; one jump, not five sizes.

**Banned as default:** Inter, Roboto, system-ui stack without argument; monospace as entire UI voice.

---

## 5. Signature device · Grind Curve

**What:** SVG area + stroke from `rhythm[]` — typed prompts per time bucket.

**Rules:**
1. Always present when `rhythm.length > 0`.  
2. Peak dot on max bucket — the hardest stretch.  
3. Fill: `--ag-spark-dim` → transparent (no fake terrain).  
4. Height: 150px on card, 96px on feed row thumbnail.  
5. `aria-label`: “Session grind curve” — not “chart”.

**Never:** Stock wave decoration, lorem curves, gradient hero with no data.

---

## 6. Run card anatomy

```
┌──────────────────────────────────────┐
│ [avatar] Athlete · date    AGENTGRINDER │
│ Session title              [★ focus PB] │
│ harness · project                       │
├──────────┬──────────┬──────────────────┤
│ DISTANCE │  TIME    │ PACE             │
│ 47 prompts│ 2h 20m  │ 2:59 /prompt     │
├──────────────────────────────────────┤
│ ▁▂▃▅▇▅▃▂  GRIND CURVE (full bleed)   │
├──────────────────────────────────────┤
│ Effort · Segments · Commits · Cadence │
├──────────────────────────────────────┤
│ kudos · comment        Made with …    │
└──────────────────────────────────────┘
```

| Element | Spec |
|---------|------|
| Card radius | `14px` (not 2xl everywhere) |
| Border | 1px `--ag-line` |
| Shadow | `0 8px 30px oklch(0 0 0 / 0.35)` dark only |
| PB badge | 11px, spark border, text “★ focus PB” — only when rule fires |
| Footer kudos | Text + subtle icon — no emoji in v1 brand surfaces |

---

## 7. Voice & copy

### Do

- Short, athletic, receipted: *“47 prompts · 3 commits · ★ focus PB”*  
- Honest gaps: *“—”* when data missing  
- Imperative CLI: *“Log the grind.”*

### Don’t

- seamlessly, unlock, supercharge, empower, effortless  
- “AI-powered insights”  
- Fake precision: *“Run #2,914”*  
- Shame: *“You’re slower than 82% of users”*

### Sample strings

| Context | Copy |
|---------|------|
| Empty feed | No runs yet. `agentgrinder run` to log one. |
| Upload CTA | Share this run |
| Event page | {Event name} · {n} grinders · {date} |
| Error | No typed turns found — is this a human session? |

---

## 8. Motion

- **None** on card static export.  
- Feed: 150ms border-color on hover (`--ag-line` → `--ag-spark`).  
- **No** pulse, bounce, parallax, kudos explosion particles v1.

---

## 9. Social & Devpost assets

| Asset | Size | Content |
|-------|------|---------|
| Devpost thumbnail | 1200×675 | Card mock + wordmark + tagline |
| X card | 1200×628 | One real run (Oscar’s) — real numbers |
| GitHub social | 1280×640 | Dark bg, grind curve hero, mono stats |

**Screenshot test:** Stranger names “Strava for coding agents” without caption.

---

## 10. CSS tokens (implementation)

Save as `tokens/agentgrinder.css`:

```css
:root {
  --ag-bg: oklch(0.14 0.01 260);
  --ag-surface: oklch(0.19 0.012 260);
  --ag-line: oklch(0.28 0.01 260);
  --ag-ink: oklch(0.94 0.01 260);
  --ag-muted: oklch(0.62 0.02 260);
  --ag-spark: oklch(0.68 0.19 45);
  --ag-spark-dim: oklch(0.68 0.19 45 / 0.28);
  --ag-radius-card: 14px;
  --ag-font-display: "IBM Plex Sans", system-ui, sans-serif;
  --ag-font-mono: "IBM Plex Mono", ui-monospace, monospace;
}
```

---

## 11. Relationship to sibling brands

| Brand | Relationship |
|-------|--------------|
| **Transcripto** | “Numbers from Transcripto” footnote on ingest path |
| **MAGNET** | Private eval — not on public card v1 |
| **ZUP** | Private ops — no co-brand |
| **Strava** | Metaphor only — never use their orange hex `#FC4C02` verbatim; we use `--ag-spark` |

---

## 12. Approval checklist

- [ ] Oscar: name **Agentgrinder** locked for Sep 14  
- [ ] Oscar: dark-first card approved  
- [ ] Oscar: post one real run card with new wordmark  
- [ ] Implement tokens in `render.py`  
- [ ] Rename module `aistrava` → `agentgrinder` when ready  

---

*Brandbook v1 · derived from design-taste Gate 0 + AISTRAVA slice 1 device · 2026-08-30*
