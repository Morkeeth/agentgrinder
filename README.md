# Agent Grinder

**Where you post your real runs.** Your coding agent already grinds — opens files, ships commits,
measures pace. Agent Grinder turns each session into a run card you'd actually share: real metrics
from real work, never invented.

> Grind in public. Ship with proof.

## Start here — one command, no account, nothing to configure

```bash
git clone https://github.com/Morkeeth/agentgrinder.git && cd agentgrinder
python3 -m agentgrinder grind        # your most recent session -> grind.html
```

**Web:** [agentgrinder.vercel.app](https://agentgrinder.vercel.app)

No install, no dependencies, no key, no server. **The line above is the whole install**, and it is
what the website's copy button hands you.

If you would rather have it on your `$PATH`, that needs a venv, not the stock python:

```bash
python3.12 -m venv .venv               # any python3.10+ you have
.venv/bin/pip install -e .             # then `.venv/bin/agentgrinder grind` works from any directory
```

`pip install -e .` under macOS `/usr/bin/python3` **fails**: that pip is 21.2.4, it predates PEP 660,
and it refuses an editable install of a pyproject-only project. Measured 3 Sep 2026. The site used to
print that command as step one; it does not any more.

Editable on purpose. `demo` renders the transcript in `samples/`, which lives in the clone and not
in the wheel, so a non-editable `pip install .` gives you a working `grind` from anywhere and a
`demo` that cannot find its sample. Measured on a fresh clone, 3 Sep 2026.

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

## The numbers — verified output is the distance, prompts are the cost

The headline of every card is **verified per turn** = (verified claims + artifacts produced) ÷
typed turns. Typed turns are the denominator: what the run *spent*. A card that headlines
"47 prompts" celebrates the person who talked the most — the METR finding (developers believed
they were 20% faster and measured 19% slower). The rule, from the internal metric spec
(`METRICS-AGENTIC-ENGINEERING-2026-09-02`, not in this repo): *a good agentic engineer turns the
fewest human decisions into the most verified, delivered work — distance = verified output; prompts = cost.*

| Number | Role | Definition | Computed here? | Owner / source when not |
|---|---|---|---|---|
| **Verified per turn** | **headline** | (verified claims + artifacts produced) ÷ typed turns | yes, when its three parts exist | — |
| Typed turns | cost | human-authored turns (`authorship.py`: typed OR queued, drops isMeta / isSidechain / tool_result) | yes | Transcripto export-run |
| Verified-claims share | run number | of the agent's claims, the fraction with tool evidence in the same trace | **v0** (`claims.py`, rule below) | Helicon witness |
| Correction rate | run number | typed turns that correct the agent ÷ typed turns | no — prints `—` | Transcripto export-run (coach inverse class) |
| Produced ÷ promised | run number | deliverables that exist at their path ÷ deliverables the run named | produced **v0**; promised prints `—` | ZUP artifact-detect |
| Reach | run number | did the output cross to a person who is not the author (0/1) | no — prints `—` | git remotes + `gh` + the launch log |
| Moving time · pace · effort · segments · commits · cadence | cost group | unchanged from the v1 card | yes | — |

A `—` is never blank: hover it and the tooltip names the tool that owns that number.

**The v0 claim rule** (`agentgrinder/claims.py`, a stand-in until `helicon witness` is wired):
a *claim* is a line of assistant text matching `passes|passed|fixed|done|deployed|works|green|verified|ship(s|ped)`.
It is *verified* when a tool result **in the same human turn** (the span between two typed turns,
before or after the claim) carries a matching token: a `test_*` name or file path from the claim
line, or a generic success token (`N passed`, a line starting `OK`, `exit 0`) that is not
contradicted by `N failed` / `FAILED` / `Traceback` in the same result. *Artifacts produced* v0 =
distinct Edit/Write paths that exist on disk when the transcript is parsed. Known blind spots are
listed in the module docstring. Sampled 2 Sep over the 11 most recent sittings on this machine:
1–3 typed turns each (fleet lanes), 1–42 claims, verified share 0–100% (most 100%), verified per
turn 1.0–18.5 — the rule **over-counts**: `done` and `ship` match prose, and one `N passed` in a
turn verifies every claim beside it. Read the share as a ceiling until Helicon witness replaces
it; that is why the claim count sits on the card next to the headline instead of inside it.

## The grind coach: an agent owns the numbers

The card above is a self-report checked by a rule. `coach` makes it a receipt: a
[Strands Agents](https://strandsagents.com) agent reads the sitting through five tools, checks
every claim against the evidence in its own human turn, asks the disk whether every file the run
wrote exists, asks git which of them landed, and only then writes the verdict block and a
next-session plan. It cannot write a number a tool did not return: `write_verdict` refuses it.

```bash
python3.12 -m venv .venv && .venv/bin/pip install -e ".[coach]"   # Strands SDK, Python 3.10 or newer
.venv/bin/agentgrinder coach samples/sample_session.jsonl        # keyless, nothing leaves the machine
.venv/bin/agentgrinder grind --coach                             # your last sitting, verdict on the card
```

The five tools, in `agentgrinder/coach/tools.py`:

| Tool | Returns | Never returns |
|---|---|---|
| `read_run` | counts, the claim lines with ids, tool results per turn, one label per written file | a typed prompt, an absolute path, code |
| `check_claim` | verified or not, the token that matched, a 200-char snippet of the evidence | anything outside the claim's own turn |
| `verify_artifact` | exists, size, last modified, whether that instant is inside the window | the path |
| `git_evidence` | commits inside the window containing the file, the first later commit that touched it, or why git could not be asked | |
| `write_verdict` | accepted with five numbers, one paragraph and a 1-5 line plan, or refused with the reasons | a number no tool returned |

Three modes, and the mode is always printed:

- **local** (default): a real `strands.Agent` event loop over the five `@tool`s, driven by a
  scripted local model (`coach/local_model.py`). The loop, the tool registry, the dispatch and
  the `AfterToolCallEvent` hook that counts the calls are genuine Strands. The token generation
  is not a language model: it is a deterministic policy (`coach/policy.py`) that reads the run,
  checks every claim and file, and fills the verdict from the tool results. No key, no network,
  no spend. The report says so under NOTE every time.
- **bedrock** (`--model bedrock`, opt-in): the same loop with a real model on Amazon Bedrock
  choosing the tools. Needs AWS credentials and costs money. The claim lines and result snippets
  of the sitting leave the machine; the command prints that before it runs. Never the default.
- **none**: the five functions called in order, no agent. The fallback. If an agent mode fails
  the report prints the reason and ends with `status DEGRADED`; it never degrades quietly.

The card shows the verdict with "verdict produced by N tool calls", and N is the hook's count,
not the plan's.

**The series.** Every `grind` also records its five numbers as one reading in a local per-project
series (`~/.agentgrinder/series.db`, counts only, `--no-series` to skip). The card then says how
this grind compares with your previous grind on the same project by verified per turn: `baseline`
under two measured readings (a first reading is not a trend), then `helped`, `hurt` or
`unchanged`. `agentgrinder predict "ships 2 files"` writes down what you expect before you sit
down; the next grind on that project prints the prediction beside its verdict. The rule is in
`agentgrinder/engine/reporter.py`. Tested in `tests/test_coach.py`: the keyless path never constructs a Bedrock
model and opens no internet socket; a policy that writes a wrong number is refused.

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
| `coach` · `grind --coach` | the grind coach: a Strands agent checks every claim and file, then writes the verdict (keyless by default) |
| `predict` | write down what your next grind on a project will do; the next card shows it beside the verdict |
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

The coach runs on counts, claim lines and git evidence. It never reads a typed prompt into a
tool result, never returns an absolute path (paths become the labels the card prints), never
returns code. In the default `local` mode nothing leaves the machine. In `bedrock` mode the
claim lines and tool-result snippets are sent to Amazon Bedrock, and the command prints that
sentence before it runs; it is opt-in and never the default.

## Pre-existing code, disclosed

The Agents for Humans rules ask for new work built inside the submission period (10 Aug to 14 Sep
2026) and for any other pre-existing code to be disclosed. This repository was created on 31 Aug
2026. Three pieces of it did not start life here:

- `agentgrinder/authorship.py` is vendored from Transcripto (same author, earlier project). It is
  the rule that decides which `type: "user"` records a person typed. Named at the top of the file.
- The coach scaffolding in `agentgrinder/coach/` (the agent creation shape, the scripted local
  model that replays a plan through the real Strands event loop, and the three-mode dispatch with
  the DEGRADED banner) is lifted from [Morkeeth/agents-for-humans](https://github.com/Morkeeth/agents-for-humans)
  (MAGNET, same author, MIT, built from 29 Aug 2026 onwards, inside the submission period). The
  five coach tools and the verdict are new here. MAGNET does not enter this hackathon.
- The per-project series logic in `agentgrinder/engine/` (a verdict over a series of readings,
  `baseline` under two readings) comes from the same MAGNET repo, which itself ported it from
  [Morkeeth/mountain-of-helicon](https://github.com/Morkeeth/mountain-of-helicon) (same author,
  before the period).

Everything else in this repository was written inside the period. The Strands Agents SDK is a
dependency, not copied code.

MIT. See `LICENSE`.
