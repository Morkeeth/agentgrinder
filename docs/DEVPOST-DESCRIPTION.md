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
human ever typed. Over a 40 minute window on my own machine this afternoon,
`python3 -m agentgrinder authorship` counted **334 records marked `type: "user"` and 12 of them,
3.6%, were typed by a person**. The other 322 were tool results, injected skill bodies, harness
envelopes and prompts one agent wrote to another. Every dashboard built on that field is inflating
the number it puts in front of you. METR's 2025 randomized trial on experienced open source
developers found the same gap in the other direction: they believed the agent made them 20% faster
and the stopwatch said 19% slower. So the one number that matters, how much verified work a
session actually delivered per human decision, is the number nobody has.

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
pip install -e ".[coach]"
python3 -m agentgrinder coach samples/sample_session.jsonl   # the agent, keyless, offline
python3 -m pytest -q                                         # 54 passed
```

The bundled sample makes the coach deterministic: 3 typed turns, 2 claims of which 1 has evidence
in its own turn, 2 files written of which 1 exists on disk, 0 commits, verified per turn 0.67, and
8 tool calls dispatched by the Strands loop. Run it twice and you get the same verdict, because
the local path has no model temperature in it.

Live: **https://agentgrinder.vercel.app**

## Honest limits

- **The claim rule is v0 and it over-counts.** A claim is a line of agent text matching
  `passes|passed|fixed|done|deployed|works|green|verified|ship(s|ped)`, and it is verified when a
  tool result in the same human turn carries a token from the claim line or an uncontradicted
  success token. The words `done` and `ship` match ordinary prose, and one "N passed" in a turn
  verifies every claim beside it. Read the verified share as a ceiling. The module docstring in
  `agentgrinder/claims.py` says the same thing, and the claim count sits on the card next to the
  headline instead of inside it for exactly this reason. Replacing that rule with a real witness
  is the next slice, and the coach is the seam it plugs into: the agent already calls the rule
  per claim rather than in bulk.
- **Two profiles today.** The hosted database holds 2 profiles and 2 runs, and both runs were
  posted before the coach shipped, so their cards correctly print a dash for verified per turn
  rather than a number invented after the fact. Nobody who is not the author has published a
  coached run yet. The local path is what has been used; the network has not been proven.
- **Bedrock is opt-in and it has a privacy cost.** The default is keyless and offline. Choosing
  `--model bedrock` sends claim lines and tool-result snippets to AWS, and the command says so
  before it runs. Nothing else in the tool ever leaves the machine, and no session is ever
  uploaded without a human click.
- **Correction rate, produced over promised, and reach print a dash.** They are real numbers owned
  by tools that are not wired in yet. A dash is never blank here: hovering it names the tool that
  owns the number.
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
- Architecture diagram: `docs/architecture.md`

---

## The numbers, and the command behind each

Every figure in the text above, run on 3 September 2026.

| Number | Command | Result |
|---|---|---|
| 334 `type: "user"` records, 12 typed by a person, 3.6% | `python3 -m agentgrinder authorship` | `12 3.6% human` of `334 100.0% total`, parts sum to the total |
| 8 tool calls on the sample, 3 typed turns, 1 of 2 claims verified, 1 of 2 files on disk, 0.67 verified per turn | `python3 -m agentgrinder coach samples/sample_session.jsonl` | exit 0, `tools dispatched 8 (by the Strands event loop; hook logged 8)` |
| The refusal reasons | the five tools called in order, then `write_verdict(..., claims_verified=2, artifacts_produced=2, ...)` | `accepted: False`, two reasons, `tools_said` block |
| 54 tests | `python3 -m pytest -q` | `54 passed in 2.76s` |
| 122 tracked files | `git ls-files \| wc -l` | 122 |
| 15 commits, first on 31 August 2026 | `git rev-list --count HEAD` | 15, first commit `2026-08-31 23:43:39 +0200` |
| 7 coach columns live on the hosted database | `information_schema.columns` on `public.runs` | `claims`, `claims_verified`, `artifacts_produced`, `coach_verdict`, `coach_plan`, `coach_tool_calls`, `progress_verdict`, all nullable |
| Live site and hosted card reachable | `curl -o /dev/null -w "%{http_code}"` on `/` and on `/?run=<id>` | 200 and 200; headless render shows the card |
| 7,262 participants in the field | `curl -sL https://agentsforhumans.devpost.com/` | `Participants (7262)` |

The METR figure (20% believed faster, 19% measured slower) is from METR's 2025 randomized
controlled trial on experienced open source developers. It is a published external result, not a
measurement made here.
