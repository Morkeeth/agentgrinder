# AGENT GRINDER

Paste-ready Devpost text. Every number below was produced by a command, and the command is named
next to it. Track: **Professional Agents**.

---

## Tagline

**An agent checks your session before the card counts it**

---

## The problem

Your coding agent tells you it fixed the test, shipped the file, and got the suite green, and you
have no way to check without rereading the whole transcript. The measurement is worse than absent,
it is confidently wrong: a raw session log labels far more turns as coming from the human than a
human ever typed. Over a 14 day window on my own machine on 4 September 2026,
`python3 -m agentgrinder authorship --hours 336` counted **34,032 records marked `type: "user"`
and 966 of them, 2.8%, were typed by a person**. The other 33,066 were tool results, injected skill
bodies, harness envelopes and prompts one agent wrote to another. Narrower windows on the same
machine read 2.4% over 24 hours and 6.9% over one hour, so the share moves a little and the gap
does not move at all. Every dashboard built on that field is inflating
the number it puts in front of you. METR's 2025 randomized trial on experienced open source
developers found the same gap in the other direction: they believed the agent made them 20% faster
and the stopwatch said 19% slower. So the one number that matters, how much verified work a
session actually delivered per human decision, is the number nobody has.

## Why this publishes the measurement and never the transcript

A funded competitor already tried the other way and retreated from it. Amp shipped public,
internet-wide, discoverable thread sharing and withdrew it on 2 June 2026, and the reason they gave
is the whole design constraint of this project in one sentence:

`It's getting too hard to review a thread to ensure it doesn't contain any snippets of sensitive
files.`

That is Sourcegraph, about their own product, at
https://ampcode.com/news/end-of-public-threads. They also note that agents read more files into
context with every model release, so the problem gets worse on its own.

Agent Grinder publishes counts and never had the transcript to leak. `grind` reads your sessions
locally and the card carries numbers, not text. Nothing is uploaded without a human click, and what
uploads is a row of integers. That is not a smaller version of thread sharing. It is the version
that survives a security review, and a competitor's withdrawal notice is the evidence.

## What Agent Grinder does

One command turns your last coding session into a card. Before the card prints a single number, a
Strands agent referees the session: it reads the sitting through tools, checks every claim the
agent made against the evidence in that claim's own turn, asks the disk whether every file the run
promised exists, asks git which of those files actually landed in a commit, and only then writes
the verdict. It cannot write a number a tool did not return. The card is where the verdict lands,
next to how this session compares with your last session on the same project.

```bash
git clone https://github.com/Morkeeth/agentgrinder.git && cd agentgrinder
pip install -e ".[coach]"
python3 -m agentgrinder coach samples/sample_session.jsonl   # keyless, offline, 8 tool calls
python3 -m agentgrinder grind --coach                        # your last session, verdict on the card
```

## The agent, concretely

Five `@tool` functions in `agentgrinder/coach/tools.py`, each one a plain function with a Strands
wrapper over it, all bound to a single `CoachContext` that remembers what every tool returned:

| Tool | Line | What it returns | What it never returns |
|---|---|---|---|
| `read_run` | `coach/tools.py:128` | counts, the claim lines with ids, tool results per turn, one label per written file | a typed prompt, an absolute path, code |
| `check_claim` | `coach/tools.py:146` | verified or not, the token that matched, a 200 character snippet of the evidence | anything outside the claim's own human turn |
| `verify_artifact` | `coach/tools.py:167` | exists, size, last modified, whether that instant is inside the session window | the path |
| `git_evidence` | `coach/tools.py:183` | commits inside the window containing the file, the first later commit that touched it, or the reason git could not be asked | |
| `write_verdict` | `coach/tools.py:207` | accepted, with five numbers, a paragraph and a plan; or refused, with the reasons | a number no tool in this context returned |

The agent is built at `agentgrinder/coach/agent.py:87` (`create_coach`): a real `strands.Agent`
with the five tools, a system prompt that forbids inventing numbers, `callback_handler=None`, and
a hook.

**Three model paths, and the path is printed on screen every time.**

- **local**, the default. A real `strands.Agent` event loop over the five tools, driven by
  `ScriptedLocalModel` in `agentgrinder/coach/local_model.py`, a subclass of
  `strands.models.model.Model` that streams tool-use blocks from a deterministic policy
  (`agentgrinder/coach/policy.py`). The loop, the tool registry, the dispatch and the hook are
  genuine Strands. The token generation is not a language model, and the report says so under NOTE
  on every run. No key, no network, no spend, which is why a judge can run it in thirty seconds.
- **bedrock**, opt-in behind `--model bedrock`. The same loop with the Strands default provider,
  a real model on Amazon Bedrock choosing the tools. It needs AWS credentials, it costs money, and
  it sends the session's claim lines and result snippets off the machine. The command prints that
  sentence before it runs. It is never the default.
- **none**, the fallback. The five plain functions called in order through the same policy, no
  agent. If an agent mode fails, the run does not degrade quietly: it prints the failure, the
  exact reason, the mode it fell back to, and ends with `status DEGRADED`.

**The hook, and what it proves.** `agentgrinder/coach/agent.py:63` registers a `HookProvider` on
`AfterToolCallEvent`. It appends one record per tool call the SDK actually executed, with the tool
name, the result status, and the duration. The card's line reads "verdict produced by N tool
calls", and N is the hook's count, not the plan's count. On the bundled sample the report prints
`tools dispatched 8 (by the Strands event loop; hook logged 8)`: the number the SDK dispatched and
the number the hook observed agree, so the claim on the card is checkable rather than asserted.

## The refusal

This is the part that makes the card a receipt instead of a self-report. `write_verdict` compares
every number offered against what the tools in that context returned, and a mismatch is a refused
result, not an exception, so the loop sees the reason and can go get the missing evidence. Offer
it a session where the tools verified 1 claim of 2 and 1 file of 2, and claim 2 and 2:

```
{'accepted': False,
 'reasons': ['claims_verified: you wrote 2, the tools returned 1',
             'artifacts_produced: you wrote 2, the tools returned 1'],
 'tools_said': {'turns_typed': 3, 'claims': 2, 'claims_verified': 1,
                'artifacts_produced': 1, 'commits': 0}}
```

It also refuses when `read_run` was never called, when any claim was never passed to
`check_claim`, when any written file was never passed to `verify_artifact`, or when the paragraph
is empty. A card with no verdict is the honest outcome; a card with a wrong verdict is not
available.

## The A and B: this session against your last one

Every `grind` records its five numbers as one reading in a local per-project series
(`~/.agentgrinder/series.db`, counts only, `--no-series` to skip). The card then says how this
session compares with your previous session on the same project by verified per turn:
**baseline** under two measured readings, because one reading is not a trend, then **helped**,
**hurt** or **unchanged**. `agentgrinder predict "ships 2 files"` writes down what you expect
before you sit down, and the next session on that project prints the prediction beside the
verdict. The rule lives in `agentgrinder/engine/reporter.py`.

## What a judge can run in two minutes

```bash
git clone https://github.com/Morkeeth/agentgrinder.git && cd agentgrinder
python3 -m agentgrinder demo                                 # the card, no install, no key
pip install -e ".[coach,dev]"
python3 -m agentgrinder coach samples/sample_session.jsonl   # the agent, keyless, offline
python3 scripts/show-refusal.py                              # watch the verdict tool refuse
python3 scripts/claim-calibration-report.py                  # every published figure, recomputed
python3 -m pytest -q                                         # 170 passed
```

The calibration report is worth thirty seconds of a judge's time, because it **exits non-zero on
purpose**. It recomputes the precision and recall this submission prints, from counts committed
beside them, and then fails on the one stratum that is too thinly labelled to support the headline.
A project that ships a red check pointed at its own headline number is making a different kind of
claim than one that ships a green one.

The bundled sample makes the coach deterministic: 3 typed turns, 2 claims of which 1 has evidence
in its own turn, 2 files written of which 1 exists on disk, 0 commits, verified per turn 0.67, and
8 tool calls dispatched by the Strands loop. Run it twice and you get the same verdict, because
the local path has no model temperature in it.

Live, and nothing to install: a published run with the verdict on it,
**https://agentgrinder.vercel.app/?run=28d5d0b7-eda2-4d94-a83c-580d2e3b75b2**. Verified per turn
3.67, three typed turns, three of seven claims with evidence in their own turn, eight of fourteen
written files on disk, and the line "verdict produced by 37 tool calls", which is the hook's
count. The site is at **https://agentgrinder.vercel.app**.

## Honest limits

This project's whole claim is that a number without a source is a guess. Its own headline number
was one until 3 September, and the first two bullets below are the receipt for it no longer being
one. Read the length of this section as the product working rather than as a disclaimer.

- **The claim rule publishes its own error rate, and it missed its target.** A rule decides what
  counts as a claim, so that rule has an error rate. 396 lines of assistant text from real sessions
  were hand-labelled against a rubric written before the sample was opened, split by session into a
  tuning half and a held-out half. The rule was iterated on the tuning half only and the held-out
  half was scored once. On that held-out half it reads **precision 0.63, 95% interval 0.43 to 0.83,
  and recall 0.66, interval 0.46 to 0.83**, against 0.32 and 0.37 for the vocabulary regex it
  replaces. **The target was precision above 0.8. It was not reached, and 0.63 is the number the
  site prints.** Method, rubric, per-cell counts and the twelve remaining false positives:
  `docs/CLAIM-RULE-CALIBRATION-2026-09-03.md` and `docs/claim-calibration.json`. A test recomputes
  the published figures from the committed counts and digests the rule's own text, so the rule
  cannot be edited without the suite going red.
- **A third of that figure rests on four predicted positives.** The 0.63 blends three harnesses by
  their share of one machine's corpus, and split out they disagree. Claude Code reads 0.72 precision
  and 0.68 recall over 114 labelled lines carrying 62.9% of the weight. Codex reads 0.86 and 0.62
  over 44 lines carrying 2.2%. **Cursor is not resolved**: the rule predicted 4 positives in total
  there, 1 true and 3 false, from 40 labelled lines standing for 19,403, and a precision off 4
  predicted positives has a 95% interval of 0.00 to 0.86. So the headline is neither a general
  number nor a Claude Code number, and it sits below Claude Code's own 0.72 because that thin
  stratum drags it down. `python3 scripts/claim-calibration-report.py` reproduces every figure and
  **exits non-zero** while any stratum carrying 10% or more of the weight sits under 10 predicted
  positives. The check is red today, on purpose.
- **The card scores one of those three harnesses, and the published figure covers all three.** The
  claim rule runs in two places, `ingest.parse_session` and `solo.py`, and both read Claude Code
  transcripts only. `parse_cursor_session` and `parse_codex_session` return no claim count, checked
  on 4 September 2026 against the 298 Cursor transcripts and 81 Codex rollouts on this machine at
  the paths the tool ships with. A Cursor run's card prints a dash for verified per turn and its
  tooltip names what is missing, which is the gate working. It also means **0.63 is measured over a
  line population 37.1% larger than the population it is ever applied to**, and the figure that
  describes what this card does is the Claude Code row, 0.72 and 0.68. The lower, corpus-wide number
  stays the headline: raising your own published score on your own authority is not a thing this
  project does quietly, and the more conservative figure is the safer one to ship. A test asserts
  that the two non-Claude parsers return no claim count, so the day either is wired into the rule the
  suite goes red and the calibration has to be redone before the number can be republished.
- **Whether a claim was matched to the RIGHT evidence is not measured at all.** A generic `N passed`
  in a turn still verifies any claim beside it. The claim side now carries a measured error, the
  evidence side carries an unmeasured one, and the card's tooltip says so on screen.
- **The network is one person wide.** Queried with the site's own publishable key on 4 September
  2026, the hosted database returns 2 profiles and 2 publicly readable runs, and both runs are the
  author's. One carries a coach verdict, 7 claims of which 3 had evidence in their own turn and 37
  tool calls; the older one predates the coach and correctly prints a dash for verified per turn
  rather than a number invented after the fact. Row-level security means an anonymous key sees only
  public rows, so that count is a floor on the table and an exact count of what a stranger can read.
  Nobody who is not the author has published a run. The tool works; the network has not been proven.
- **Bedrock is opt-in and it has a privacy cost.** The default is keyless and offline. Choosing
  `--model bedrock` sends claim lines and tool-result snippets to AWS, and the command says so
  before it runs. Nothing else in the tool ever leaves the machine, and no session is ever
  uploaded without a human click.
- **Reach is now computed, and it still prints a dash on every published run.** `agentgrinder/reach.py`
  answers one question from the machine: did a commit made inside the session window reach a remote
  owned by someone who is not the author. True when it did, False when the window closed with
  commits that are on no remote at all, and None with a named sentence for every ambiguous case, so
  a dash always says why. It refuses True on a push to an organisation the author belongs to,
  because that is not another person, and it refuses True on a weak identity, because an email local
  part is not a GitHub login. Both published runs predate the column being populated, so both read
  null today. The rule is measured and wired; nothing has been published through it yet.
- **All three harnesses now read their own file writes, commits and repository.** Until 4 September
  the Cursor and Codex cards printed a dash for files touched, commits, artifacts and reach, with a
  tooltip blaming the harness. The tooltip was wrong: Cursor's `Write` and `StrReplace` blocks carry
  an absolute path on every one of the 2,279 edit blocks in the 298 transcripts on this machine, and
  Codex names every path it wrote in `patch_apply_end` and its working directory in `session_meta`.
  Both parsers read them now, a failed patch is not counted as a write, and reach answers from git
  on all three. What a Cursor and Codex card still does **not** carry is the grind trace and the
  verified-per-turn headline: the trace needs a timestamp on each edit and Cursor stamps typed turns
  only, and the headline needs the claim rule, which is deliberately left unwired so the published
  precision keeps describing the population it was measured on.
- **Correction rate and produced over promised print a dash.** They are real numbers owned by tools
  that are not wired in yet. A dash is never blank here: hovering it names the tool that owns the
  number and says what it would need.
- **This is a local-first tool with an optional hosted layer.** It reads transcripts you already
  have. If you have never run a coding agent there is nothing to read, and it says so and exits 1
  rather than rendering something invented.

## Pre-existing code, disclosed

The rules ask for work built inside the submission period, 10 August to 14 September 2026, and for
any other pre-existing code to be disclosed. This repository was created on 31 August 2026. Three
pieces of it did not start life here:

- **`agentgrinder/authorship.py` is vendored from Transcripto**, an earlier project by the same
  author. It is the rule that decides which `type: "user"` records a person actually typed, and it
  is named at the top of the file.
- **The coach scaffolding in `agentgrinder/coach/`** (the agent creation shape, the scripted local
  model that replays a plan through the real Strands event loop, and the three-mode dispatch with
  the DEGRADED banner) is lifted from
  [Morkeeth/agents-for-humans](https://github.com/Morkeeth/agents-for-humans), the same author's
  MIT repository, built from 29 August 2026 onwards, inside the submission period. The five coach
  tools, the refusal and the verdict are new here. That repository does not enter this hackathon;
  it is used as a disclosed engine library only.
- **The per-project series logic in `agentgrinder/engine/`** (a verdict over a series of readings,
  `baseline` under two readings) comes from the same repository, which itself ported the stack
  logic from [Morkeeth/mountain-of-helicon](https://github.com/Morkeeth/mountain-of-helicon), also
  the same author, written before the period.

Everything else in this repository was written inside the period. The Strands Agents SDK is a
dependency, not copied code.

## Built with

Python 3.9 or newer for the card, Python 3.10 or newer for the coach. Strands Agents SDK
(`strands.Agent`, `@tool`, `strands.models.model.Model`, `strands.hooks.AfterToolCallEvent`).
Amazon Bedrock, opt-in. Supabase for the optional hosted card and feed. Vercel for the static web
app. No runtime dependencies for the local card path.

## Links

- Repository: https://github.com/Morkeeth/agentgrinder (MIT, licence file at the root)
- Live: https://agentgrinder.vercel.app
- A published run, with the coach's verdict on it:
  https://agentgrinder.vercel.app/?run=28d5d0b7-eda2-4d94-a83c-580d2e3b75b2
- Architecture diagram: `docs/architecture.md`

---

## The numbers, and the command behind each

Every figure in the text above, re-measured on 4 September 2026 at commit `cd9a1a3`. Each row is
anchored to that commit, so it stays true after the branch moves; re-run the table at whatever
commit is actually submitted, because two of these rows change with every merge. The repository
counts move as the repository does; the coach numbers on the bundled sample do not, because the
keyless path is deterministic.

| Number | Command | Result |
|---|---|---|
| 244 `type: "user"` records, 4 typed by a person, 1.6% | `python3 -m agentgrinder authorship` | `4 1.6% human` of `244 100.0% total`, parts sum to the total |
| 334 records and 12 typed, 3.6%, over a 40 minute window on 3 September | same command, previous day | the reading the text quotes first |
| 95 records and 4 typed, 4.2%, over a 31 minute window earlier on 4 September | same command, same day | three readings, 1.6% to 4.2%: the share moves with the window, the order of magnitude does not |
| 8 tool calls on the sample, 3 typed turns, 1 of 2 claims verified, 1 of 2 files on disk, 0.67 verified per turn | `python3 -m agentgrinder coach samples/sample_session.jsonl` | exit 0, `tools dispatched 8 (by the Strands event loop; hook logged 8)` |
| The refusal reasons | the five tools called in order, then `write_verdict(..., claims_verified=2, artifacts_produced=2, ...)` | `accepted: False`, two reasons, `tools_said` block |
| precision 0.63 (0.43 to 0.83), recall 0.66 (0.46 to 0.83) on the held-out half | `python3 scripts/claim-calibration-report.py` | the table, recomputed from `docs/claim-calibration.json` |
| Claude Code 0.72 / 0.68, Codex 0.86 / 0.62, Cursor not resolved | same command | per-harness rows, with 114, 44 and 40 labelled lines |
| The calibration check fails on the thin stratum | `python3 scripts/claim-calibration-report.py; echo $?` | `FAIL: cursor is under the floor at 4 predicted positives while carrying 34.9 percent of the weight`, exit `1` |
| 170 tests | `python3 -m pytest -q` | `170 passed in 14.82s` |
| 145 tracked files | `git ls-files \| wc -l` | 145 |
| 73 commits, first on 31 August 2026 | `git rev-list --count HEAD` | 73, first commit `2026-08-31 23:43:39 +0200` |
| 7 coach columns and `reach` live on the hosted database | `select *` on `public.runs` with the site's publishable key | `claims`, `claims_verified`, `artifacts_produced`, `coach_verdict`, `coach_plan`, `coach_tool_calls`, `progress_verdict`, plus `reach`, all nullable |
| Live site and hosted card reachable | `curl -o /dev/null -w "%{http_code}"` on `/` and on `/?run=28d5d0b7...` | 200 and 200 |
| The published figure is on the live site, not only in the tree | `curl -s https://agentgrinder.vercel.app/methodology \| grep -c 0.63` | 1, and the root page matches `precision 0.63` twice in the card tooltips |
| 2 profiles, 2 publicly readable runs, 1 of them coached, 0 by anyone but the author | `GET /rest/v1/runs` and `/profiles` with `Prefer: count=exact`, publishable key | `content-range: 0-1/2` on both; one row has `coach_tool_calls` 37 |
| 7,509 participants in the field | `curl -sL https://agentsforhumans.devpost.com/` | `Participants (7509)` |

Two figures above are quoted from outside this repository, and neither was measured here. The METR
figure (20% believed faster, 19% measured slower) is from METR's 2025 randomized controlled trial on
experienced open source developers. The Amp sentence is quoted from Sourcegraph's own withdrawal
notice at https://ampcode.com/news/end-of-public-threads, dated 2 June 2026, fetched and read on
4 September 2026.
