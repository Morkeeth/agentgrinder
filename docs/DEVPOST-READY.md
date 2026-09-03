# DEVPOST-READY · Agent Grinder · THE SEPTEMBER 14 SUBMISSION

> **This is the entry.** Ruled by Oscar on 3 September 2026: Agent Grinder is the Agents for Humans
> submission. `Morkeeth/agents-for-humans` does not enter; it is a disclosed engine library, named
> in the written description and never on screen.
>
> This file used to say the opposite. It was rewritten on 3 September 2026 and the old text is in
> the git history.

**Event:** [Agents for Humans](https://agentsforhumans.devpost.com/) · Devpost · deadline **Monday
14 September 2026, 17:00 PDT** (02:00 CEST on 15 September) · $40,000 · 7,262 participants as of
3 September.

**Track: Professional Agents.** The track is defined on the event's main page as an agent that
makes someone dramatically better at the work they already do, aimed at the repetitive,
judgment-heavy tasks that eat the day. Reviewing an agent's own claims is exactly that task, and
it is the one nobody does because it means rereading the transcript.

---

## 1. What is done, and what is not

| Requirement (from the rules page, Submission Requirements) | State | Where |
|---|---|---|
| A project built with the required developer tools | **done** | `strands.Agent`, five `@tool` functions, a `strands.models.model.Model` subclass, a `strands.hooks` `AfterToolCallEvent` hook. `agentgrinder/coach/` |
| Text description of features and functionality | **done, paste-ready** | `docs/DEVPOST-DESCRIPTION.md` |
| Public code repository URL | **done** | https://github.com/Morkeeth/agentgrinder, `PUBLIC` |
| MIT or Apache licence file, detectable in the About section | **done** | `LICENSE` at the root; `gh repo view` reports `MIT License` |
| README | **done** | `README.md`, includes the disclosure paragraph |
| Architecture diagram | **done** | `docs/architecture.md`, mermaid, renders on GitHub |
| Video, 5 minutes maximum, public on YouTube or Vimeo | **shot list ready and verified, no recording exists** | `docs/VIDEO-SHOTLIST.md`, a 2:55 cut, every command in it run once |
| Video demonstrates the working project | ready | shots 3 to 8 are live commands, no slides |
| Pitch covers the problem, who it is for, why it matters | ready | shots 1, 2 and 9 |
| AWS Builder ID | **Oscar, not done** | needed on the form |
| Optional live demo link, which strengthens Technical Implementation | **done** | https://agentgrinder.vercel.app, and a published run carrying the coach's verdict at https://agentgrinder.vercel.app/?run=28d5d0b7-eda2-4d94-a83c-580d2e3b75b2 |
| builder.aws blog post, bonus up to 0.6 | **not written** | see section 5 |

Nothing on this list is blocked by code. What is left is Oscar's accounts, Oscar's camera, and one
optional stranger.

---

## 2. What Oscar pastes where

Devpost's form labels are read off the live form; the text below is written to fit the usual
fields. Everything comes from `docs/DEVPOST-DESCRIPTION.md`, so edit that file, not this one.

| Field | Paste this |
|---|---|
| Project name | `Agent Grinder` |
| Elevator pitch / tagline | `An agent checks your session before the card counts it` (54 characters) |
| About the project | the whole of `docs/DEVPOST-DESCRIPTION.md` from **The problem** down to **Built with**, in that order. It is written to be read top to bottom by a judge who will not open the repo |
| Built with | `python`, `strands-agents`, `amazon-bedrock`, `supabase`, `vercel`, `sqlite` |
| Try it out links | `https://github.com/Morkeeth/agentgrinder` and `https://agentgrinder.vercel.app` |
| Video demo link | the public YouTube URL, once it exists |
| Track | Professional Agents |
| AWS Builder ID | the ID from section 4 |
| Image gallery | the card screenshot first, the coach report second, the refusal third. Generate them with the commands in `docs/VIDEO-SHOTLIST.md` shots 3, 4 and 5 |

**The disclosure paragraph is not optional and it is not a footnote.** The rules allow pre-existing
code and require that it is disclosed. The paragraph headed **Pre-existing code, disclosed** in the
description covers `authorship.py` from Transcripto, the coach scaffolding and the series logic
from `Morkeeth/agents-for-humans`, and the stack logic that repository ported from
`Morkeeth/mountain-of-helicon`. Paste it. It costs nothing and its absence is the kind of thing
that gets found.

---

## 3. Two repository settings worth thirty seconds

Both are on the GitHub repository page, right side, under About:

1. **Set the website field to `https://agentgrinder.vercel.app`.** It is empty today. The rules say
   a live demo link strengthens the Technical Implementation score, and a judge who lands on the
   repository first will not find the live site otherwise.
2. **Consider leading the description with the coach.** It currently reads "Strava for agent
   sessions, where you post your real runs", which sells the card and not the referee. Something
   closer to the tagline reads better next to a Strands entry.

---

## 4. What Oscar must have before the form will submit

| Thing | How | Time |
|---|---|---|
| **AWS Builder ID** | sign in at `https://profile.aws.amazon.com` with an email, no AWS account needed. The form asks for the ID | 5 minutes |
| **Public video URL** | the shot list is written, timed at 2:55, and every command in it has been run: `docs/VIDEO-SHOTLIST.md`. The local Kokoro TTS in `~/CODE/voice-generation` is installed and ready for the voiceover. What does not exist is the recording and a public YouTube URL | about 2 hours of recording time including the cold review pass |
| **Devpost account registered for the event** | the Join button on the event page | 2 minutes |
| **AWS credentials**, only if the Bedrock take is filmed | the `bedrock` mode is opt-in and costs money. The video does not need it; the local mode is honest and the report prints the mode. `docs/BEDROCK-COACH-RECEIPT-TEMPLATE.md` has the command and the receipt fields if it is worth doing | 30 minutes |

---

## 5. The builder.aws post, worth up to 0.6

The rules ask for a post on `builder.aws.com` covering the journey of building with AWS for this
hackathon, and give submissions that reach Stage Two up to 0.6 additional points, 0.2 per piece.
So three short posts beat one long one.

The material is already written and each of these has an honest, specific spine:

1. **Building a tool that refuses.** Why `write_verdict` compares every offered number against what
   the tools returned, why a refusal is a result and not an exception, and what that does to the
   agent's next move. Source: `agentgrinder/coach/tools.py:207` and `scripts/show-refusal.py`.
2. **A keyless demo path with a real Strands event loop.** Subclassing `strands.models.model.Model`
   so a judge can run the agent with no AWS credentials, what stays genuine (the loop, the tool
   registry, the dispatch, the hooks) and what does not (the token generation), and why the report
   prints that distinction on every run. Source: `agentgrinder/coach/local_model.py`.
3. **Counting what the SDK actually did.** Using `strands.hooks.AfterToolCallEvent` so the number
   on the card is the SDK's dispatch count rather than the plan's intention. Source:
   `agentgrinder/coach/agent.py:63`.

Each title must contain the words **Agents for Humans**. Each post must be public.

---

## 6. The order for the last days

1. The video is the only item with a long tail and the weakest criterion on the scorecard. The
   shot list, the commands, the published run it points at and the voice tooling are all ready;
   the recording and the public URL are the gap. Everything else is text that already exists.
2. Register on Devpost, get the AWS Builder ID, set the repository website field.
3. Fill the form, paste from `docs/DEVPOST-DESCRIPTION.md`, attach the video URL, save as draft.
4. Publish one builder.aws post. Two more if the evening allows.
5. Optional and high value for the Impact score: one person who is not Oscar runs the cold path and
   publishes a coached run. `docs/STRANGER-RECRUIT.md` has three named candidates and the message.
6. Submit. Do not leave it to the last hour; the deadline is 17:00 PDT, which is 02:00 the next
   morning in Stockholm.

---

## 7. The honest weak spots, so nobody is surprised by a score

- **Presentation** is the criterion with no artifact yet. There is no video. The shot list is
  built to fix it in one afternoon.
- **Impact** is thin in one specific way: the hosted database holds 2 profiles and 3 runs and every
  one of them is the author's. One of the three now carries a full coach verdict and renders it,
  which is what shot 8 of the video points at, so the surface is no longer empty. What is still
  missing is a person who is not Oscar. One stranger publishing one coached run changes the
  sentence, and `docs/STRANGER-RECRUIT.md` names three.
- **Technical Implementation** is the tie-break criterion, and the honest reading is that the coach
  landed in the last week of the period while the rest of the repository does not touch Strands.
  The counter is that the coach owns the number the whole product is about, so it is the spine and
  not a bolt-on, and the description says which parts of the loop are genuine and which are not.
- **The claim rule is v0 and over-counts.** Said plainly in the description, in the README, and in
  the module's own docstring. Better to be the entry that says so.
