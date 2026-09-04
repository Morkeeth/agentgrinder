# Stranger audit: can Oscar send this to his friends today?

*4 September 2026. Run as a cold clone of what is actually published, not as a review of the
working tree.*

**The stranger:** a technical friend of Oscar's. They click a link or clone a repo, form an
opinion in about ten seconds, and never say why they closed the tab. Two paths, both checked: the
person who clicks the live URL, and the person who clones and runs.

**The machine, stated because a timing without one is not a measurement:** MacBookPro18,3, arm64,
macOS 26.6.2, system Python 3.12.5, warm network and warm DNS. Cold clone into an empty scratch
directory, `env -i` with an empty `HOME`, no credentials, no ambient packages on the path.

**The object under test:** `origin/main` at `60a0c49`. That is what a friend gets. The six commits
this lane made today are **not pushed**, and that fact produces the first two findings rather than
being a footnote to them.

---

## VERDICT

**Not sendable today.** Three blockers, and the first one is the reason the other findings are as
bad as they are. None of the three is a bug in the code. Two are a merge, one is a ruling.

The good news is that everything a friend *does* reach works. No command produced a traceback, the
cold clone is genuinely one command with no dependencies, the site is up and honest, and no secret
exists anywhere in the history.

---

## BLOCKERS

### B1. Everything fixed today is invisible to a friend

**Promised:** the repository is the product, so what the docs say is what a stranger gets.
**Happened:** `git clone` lands on `main` at `60a0c49`. The lane branch
`lane/claim-rule-population-2026-09-04` at `81029d9` is on no remote:
`git branch -r --contains 81029d9` returns nothing. So a friend cloning right now gets the
pre-audit code *and* the pre-audit docs, including the surfaces that were measurably wrong.
**Fix:** merge the lane branch to `main` and push, before the link goes to anybody.

### B2. A Cursor friend is told something false, by the tool, to their face

**Promised:** `--harness cursor` reads a Cursor session and cards it.
**Happened:** on published `main`, with a Cursor transcript containing two `Write`/`StrReplace`
blocks carrying absolute paths and a `Shell` command containing `git commit`, the tool prints:

```
  Cursor transcripts carry no file paths and no commits, so the grind trace
  cannot be drawn for them. The v1 card is rendered instead
```

Both halves of that sentence are false, and the file it just read is the disproof. The card comes
out with dashes for files touched, commits, artifacts produced and reach. A friend on Cursor is
told their harness is the limitation when the reader was.
**Fix:** B1. The lane branch already reads all four; on it the same fixture cards 2 files, 1
artifact and 1 commit.

### B3. A friend cannot post a run without a GitHub account, and the door is not built

**Promised:** "Where you post your real runs", and a README that opens "no account".
**Happened:** the local card genuinely needs no account. Publishing does. The site's only sign-in
is `signInWithOAuth({provider:'github'})`, twice, no alternative. And the anonymous door does not
exist yet: an anonymous insert against the live database returns

```
HTTP 401  {"code":"42501","message":"new row violates row-level security policy for table \"runs\""}
```

Probed with a duplicate primary key so no row could be created either way; the row count was 2
before and 2 after. That is the *correct* state, there is no open write policy, but it means every
friend who wants to publish needs GitHub and an OAuth authorisation.
**Fix:** ruling R3, the rate-limited edge function. Until then the link is "look at Oscar's runs",
not "post yours".

---

## THE RULING THAT GATES THE SEND

**R5 is unruled and it blocks the walkthrough.** `docs/WALKTHROUGH.md` quotes a headline figure.
Oscar has not chosen which one it is.

> Keep **0.63** as the headline with the Claude Code 0.72 printed beside it, or promote **0.72**
> with 0.63 kept as the corpus-wide note?

**Recommendation: keep 0.63.** The reason is not conservatism. It is that raising your own
published score on your own authority is not something this project gets to do quietly, and that
sentence is the product. The walkthrough is written that way; if he rules the other way, one
section changes.

**R1 and R2 change shape for this audience.** For a judge, `uvx agentgrinder grind` and a real
domain were nice. For a friend who was sent a link, they are the difference between trying it and
closing the tab: today the install is a clone into a directory they did not ask for, and the URL is
a `.vercel.app`. Both remain his click and his card.

---

## COSMETIC

### C1. `authorship` prints a green OK over a population of zero

On an empty machine it exits 0 and prints `parts sum to the total: 0 + 0 + 0 + 0 + 0 = 0  OK`.
A check that says OK about nothing is the exact failure class this product exists to name, printed
by the product. **Fix:** say "no records to check" and skip the sum line when the total is 0.

### C2. `history` prints five empty headings

It honestly opens `0 grinds on this machine`, then prints five section headers with nothing under
them. Harmless, reads like a bug. **Fix:** print the first line and stop when there are 0 grinds.

### C3. Two commands dead-end where the best one does not

`grind` with no data is the best message in the tool: it names all four search paths and points at
`demo`. `vibe` and `roast` print `no session found` and stop, with no path and no next step.
**Fix:** reuse `grind`'s message.

### C4. `rig` on an empty machine builds a share card that says nothing

Exit 0, writes `rig.html`, a 1200x630 card reading `@you · 0 MCPs · 0 skills · Harness: run a grind
to detect harness` under the heading "SHOW YOUR RIG", and invites the reader to "Steal this rig".
Nothing is false. It is an empty poster asking to be shared. **Fix:** tell them to run a grind
first, rather than handing them the poster.

### C5. Hackathon furniture on the page being sent to friends

The live nav carries `Sep 14` and `Pitch`. A friend does not know what Sep 14 is, and after Sep 14
it is stale on a page Oscar is still sending to people. **Fix:** his call, but the deadline badge
should come down when the audience changes.

---

## WHAT HELD, named so that "clean" means something

- **Cold clone is genuinely one command.** 1.18 s real, 16 MB, 143 files, lands on `main`, warm
  network on the machine named above. No install step is needed to reach a card.
- **The "no dependencies" claim is true.** `python3 -X importtime -m agentgrinder demo` under
  `env -i` imports nothing outside the standard library. No `strands`, no `requests`, no `boto`.
- **`demo` works cold**, exit 0, 0.64 s, with an empty `HOME` and no network.
- **The empty-machine message is the best thing in the CLI.** `grind` with nothing to read names
  all four transcript locations it searched and points at `demo`. Exit 1, no traceback.
- **No command produced a traceback.** `demo`, `grind`, `grind --list`, `grind --harness auto`,
  `history`, `authorship`, `share`, `flex`, `vibe`, `roast`, `rig` all ran cold and degraded with a
  sentence. `profile` and `privacycheck` print argparse usage and exit 2, which is a CLI behaving.
- **No secret anywhere in the full history.** `git log --all -p` scanned for service-role keys,
  JWTs, AWS keys, GitHub tokens and OpenAI keys. One `eyJ` hit, and it decodes to `{"harness":"`,
  a base64 run payload in a share URL, not a token. The only credential in the tree is the
  publishable Supabase key, which is the one that is meant to be public.
- **No open write policy.** Anonymous inserts are denied on both `runs` and `profiles`.
- **The live site is up and fast.** `/` 200 in 0.15 s, `/methodology` 200, the run permalink 200.
- **A logged-out friend sees a real card immediately.** `FEATURED_SNAPSHOT` ships inside the page
  with 7 claims, 3 verified and 37 coach tool calls on a real Claude Code sitting, so the argument
  of the product is on screen before any sign-in.

---

## The order to fix in

1. Merge and push the lane branch. B1 and B2 close together, and nothing else can be evaluated
   honestly until a friend and the author are looking at the same code.
2. Rule R5. The walkthrough cannot go out quoting a figure nobody chose.
3. Rule R3, or send the link as "read my runs" and say so.
4. C1 through C4, about an hour together.
5. R1 and R2, which are now funnel, not polish.
6. Re-run this audit on the merged result. A stranger check on a tree that has since changed is a
   claim about a thing that no longer exists.
