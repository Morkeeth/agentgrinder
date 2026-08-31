# Agent Grinder

**Where you post your real runs.** Your coding agent already grinds — opens files, ships commits,
measures pace. Agent Grinder turns each session into a run card you'd actually share: real metrics
from real work, never invented.

> Grind in public. Ship with proof.

## Start here — one command, no account, nothing to configure

```bash
cd aistrava                          # the checkout; there is no published remote yet
python3 -m agentgrinder grind        # your most recent session -> grind.html
```

No install, no dependencies, no key, no server. If you would rather have it on your `$PATH`:

```bash
pip install .          # then `agentgrinder grind` works from any directory
```

**Python 3.9 or newer**, which is what macOS already ships — checked by running every command
under `/usr/bin/python3` (3.9.6) and under 3.12.5, 31 Aug. The manifest said 3.10 until that was
measured, and `pip install` refused on a stock Mac because of it.

**If you have never run Claude Code**, `grind` has nothing to read and says so, and
`python3 -m agentgrinder demo` renders the bundled sample instead.

It finds your last Claude Code sitting, keeps only the turns **you typed**, asks git what actually
shipped, and draws **the grind trace**: one row per file, your prompts as ticks on your own line,
commits on the row of every file git says they contain, and the longest span nobody typed through.

Nothing is uploaded. Sharing is your click.

```bash
python3 -m agentgrinder grind --list          # the sittings in that transcript
python3 -m agentgrinder grind --pick 2        # render a specific one
python3 -m agentgrinder grind --harness auto  # freshest Claude or Cursor session
python3 -m agentgrinder share                  # fun share card from latest grind
python3 -m agentgrinder share --claim          # invite card — claim your handle
python3 -m agentgrinder history               # every grind on this machine, ranked
python3 -m agentgrinder nightrun --since ISO  # a whole multi-agent night as one grind
python3 -m agentgrinder authorship            # who wrote every type:user record
```

## What a grind is

**A sitting, not a file.** A `.jsonl` transcript is a terminal that stays open; 151 of the 194
transcripts on this machine that carry a human turn hold more than one sitting, and the median
holds 3 (re-measured 31 Aug 06:4x over all 1,370 transcripts; a `171 … median 5` written earlier
the same night no longer reproduces — `human_sittings` over `~/.claude/projects/*/*.jsonl`). A grind is a
contiguous burst of work, ended by 30 minutes of total idle — the same rule at solo and fleet
scale, so the two cards cannot disagree about where a grind begins.

## The honesty rule — no ghost grinds

Every number names what it counted and over which population, or it prints an em-dash.

- **A prompt is a keystroke.** `type: "user"` is not a person: on this machine, in one night-run
  window, 2,415 records carried it and 40 were typed by a human. The gate is Transcripto's
  measured signal — `promptSource` typed or queued, dropping injected and sidechain records —
  vendored in `agentgrinder/authorship.py`, which sorts every record into five disjoint categories
  that **sum to the raw total**. The card prints the sum so you can check it.
- **Shipping is git's word, never the transcript's.** Every edited file is in exactly one of four
  states, and they add up too: landed in a commit made during the grind · committed after it
  closed · nothing has committed it since · outside the repository or git-ignored, so git was
  never asked.
- **A rank is a real rank.** "#12 of 625" is your place among every sitting on this machine. A
  badge fires when **any one** of five measures — longest no-typing stretch, moving time, tool
  calls, files changed, prompts typed — clears *that measure's* top-2% bar. Five bars, so the
  badge is rarer than a coin flip but commoner than 2%: replayed over all 625 sittings on this
  machine it fires on **34 of them, 5.4%** (31 Aug; the replay is `history.badge` over
  `history.load()`, and the per-measure cut is `max(3, 2% of the population)`).

## The lexicon

| Term | Meaning | Strava analogue |
|---|---|---|
| **Grind** | one logged agent work session against a goal | an activity |
| **The grind trace** | the drawing: where the work went, and how hard | the route + elevation |
| **Rig** | your setup: model, harness, tools, MCPs, human gates | your gear |
| **The Box** | the bounded workspace a grind runs in | — |
| **Ship** | a checked release that left the Box | a PR |
| **ACK** | evidence-linked recognition — never a like | kudos |
| **Crew** | a human and their agents; also a group you grind with | a club |
| **Scrapbook** | your public history of grinds, ships, failures and ACKs | your profile |

Retired, and not used here: Loop, Push, Builder's Diary, LOOPMAXXER, run/route/lap.

## Commands

| | |
|---|---|
| `grind` | one sitting → the grind card (`run` is kept as an alias; `--harness auto` picks freshest agent) |
| `flex` | compare your real runs across Claude, Cursor, and Codex on this machine |
| `share` | screenshot-ready share card with claim-your-handle stub (`--vibe` `--roast`) |
| `vibe` · `roast` | meme label and honest shape roast — no streaks |
| `rig` | share your stack with friends (`--share-names` opt-in) |
| `heist` | rig heist card when someone ACKs your setup |
| `login` · `grind --push` | GitHub onboard and publish flow |
| `a2a` | Agent Activity protocol (export, feed, ACK propose) |
| `history` | every grind on this machine, ranked. Local only |
| `nightrun` | a whole multi-agent night as one grind, with `--public` redaction |
| `authorship` | the authorship tally as a table, so the card's claim is checkable without opening it |
| `profile <github-user>` | your Scrapbook: GitHub public data + your grinds |
| `demo` · `card RUN.json` · `v1card` | the bundled sample and the pre-trace card |

## Privacy

Local-first and dependency-free. `history` caches one small record per sitting in
`~/.agentgrinder/history.json`: **counts and timestamps only** — never a line of a prompt, never a
file path from inside a repository. Its *keys* are the transcript paths on this machine, and
Claude Code encodes the working directory into those, so the file does name the directories you
have worked in. It never leaves the machine, and nothing reads it but `agentgrinder history`.
Delete it and the next run rebuilds it: **7.8s** over 1,370 transcripts here, 0.04s warm (measured 31 Aug 06:2x; a 6.8s figure written on 30 Aug had already been re-measured at 6.1s and was never corrected here — it is a timing, so it moves).
`nightrun --public` redacts repository and lane names while leaving every number and the shape
unchanged. No auto-post, no auto-upload.

MIT.
