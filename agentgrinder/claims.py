r"""The claim rule: which lines of the agent's own text are claims about work done, and which
of those carried tool evidence in the same trace.

MEASURED, 3 Sep 2026. 276 assistant lines were hand-labelled against a rubric written before the
sample was opened, sampled in three strata across three harnesses, split by session into a tuning
half and a held-out half. Numbers, the design, and the error bars:
docs/CLAIM-RULE-CALIBRATION-2026-09-03.md, counts in docs/claim-calibration.json.

  claim     = a line of assistant TEXT whose sentences assert, as accomplished fact, that work in
              this session is finished, correct, or checked (`is_claim_line`). Headings, table rows,
              labels that introduce a list, questions, plans, intentions, conditions, imperatives,
              quoted output and descriptions of how a thing behaves are NOT claims, and each of
              those rejections is a measured error of the v0 rule it replaces.
  evidence  = a tool_result in the SAME HUMAN TURN (the span between two typed turns) whose text
              carries a token that matches the claim:
                - a test name from the claim line      (test_\w+)
                - a file path from the claim line      (something/with.ext)
                - a generic success token              ("N passed", a line starting "OK", "exit 0" / "exit code 0")
                  which does NOT count if the same result also says "N failed" / "FAILED" / "Traceback"
  verified  = the claim has at least one such evidence result

WHAT REPLACED WHAT. v0 was one vocabulary regex over a whole line
(passes|passed|fixed|done|deployed|works|green|verified|ships?|shipped). Measured against the label
set it ran at precision 0.37 on the held-out half: nearly two of every three lines it called a claim
were a heading, a plan, a table row or a piece of advice. Its own docstring said "most sessions read
100% verified"; over 590 real sittings the median is 0.09. Both statements were unmeasured, and both
were wrong. The rule here is still one deterministic pass of small regexes over a line, no model and
no network, but it reads each SENTENCE, rejects the shapes that are not assertions, and requires an
assertion of completion, a named check outcome, or a first-person report of work.

DEVIATION, stated: the brief said "followed ... by a tool_use". In real traces the agent runs the
check FIRST and then states the claim, so a strictly-after window marks almost every true claim
unverified — a red light nobody audits. The window is therefore the whole human turn, either side
of the claim. Evidence from a different human turn never counts.

STILL UNMEASURED, stated plainly: `evidence_matches`. Whether a claim was correctly matched to its
evidence has no label set, so the verified SHARE inherits an unknown error even though the claim
count no longer does. A generic "N passed" in the same turn still verifies any claim beside it.
No prompt text leaves this function — it returns counts.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


DECOR = re.compile(r"[*`~]+")
# underscores only outside a word: test_never_ran is a name, not emphasis
UNDER = re.compile(r"(?<!\w)_+|_+(?!\w)")
BULLET = re.compile(r"^\s*(?:[-*+•]\s+|\d+[.)]\s+|\(\w\)\s+)+")

NOT_PROSE = re.compile(r"""^(?:
      \#{1,6}\s | \| | > | ``` | -{3,}$ | [\[\{]"? | \$\s | https?:// | /\w+
    | \w+\s*=\s*\S
)""", re.X)

V = (r"fixed|added|created|wrote|written|built|shipped|deployed|pushed|committed|merged|"
     r"landed|removed|deleted|renamed|replaced|updated|ran|re-?ran|rebuilt|reseeded|closed|"
     r"corrected|refreshed|relayed|stashed|replayed|secured|generated|staged|verified|"
     r"confirmed|checked|implemented|switched|flipped|wired|restored|archived|published|"
     r"released|resolved|repaired|cleaned|reloaded|regenerated|caught|killed|stamped|filed|"
     r"drafted|documented|captured|patched|swapped|reverted|told|sent|handed|routed|found|"
     r"hoisted|split|proven|reached")
VERB = r"(?<![-\w])(?:" + V + r")(?![-\w])"

OUT = (r"passes|passed|green|clean|failed|works(?! by| via| through)|worked|"
       r"succeeded|exit(?:ed| code)? 0|no errors")
OUTCOME = re.compile(r"(?<![-\w])(?:" + OUT + r")(?![-\w])", re.I)
OUTCOME_LOOSE = re.compile(r"(?<![-\w])(?:" + OUT + r"|pass|passing)(?![-\w])", re.I)
STATUS_TOKEN = re.compile(r"\b(PASS|PASSED|FAIL|FAILED|FAILURE|OK|GREEN|DONE|SHIPPED)\b")
CHECK_SUBJ = re.compile(r"\btest_\w+|\b(test|tests|suite|lint|build|ci|typecheck|tsc|verify|validator|check|"
                        r"checks|gate|gates|probe|run|deploy|npm|pytest|make|compile|branch|"
                        r"assertion|assertions|login|endpoint|api|script|cli|command|demo|"
                        r"install|clone|path|repo|node|python|docker|server)\b|\d", re.I)

SPEC = re.compile(r"\bdone\s*[-\s]?when\b|\bwhen:", re.I)
INTENT_HARD = re.compile(
    r"\b(i'll|we'll|i will|we will|going to|about to|let me|let's|next up|plan to|"
    r"need|needs|needed|todo|to-do|start by|begin by)\b", re.I)
INTENT = re.compile(
    r"\b(shall|should|would|could|must|i'd|we'd|maybe|perhaps|propose|proposed|"
    r"recommend|suggest|worth)\b", re.I)
COND_HEAD = re.compile(r"^(if|unless|until|once|when|whether|rather than|instead of|after|before|during|each time|every time)\b", re.I)
COND_MID = re.compile(r"\b(if|unless|until|whether)\b", re.I)
IMPERATIVE_HEAD = re.compile(
    r"^(use|add|keep|write|make|check|run|store|give|ship|stop|do|prove|test|read|fold|"
    r"contact|send|build|treat|cut|push|pick|choose|call|say|tell|ask|note|see|open|close|"
    r"consider|avoid|remember|measure|report|update|create|delete|remove|replace|hold|wait|"
    r"schedule|draft|post|publish|merge|deploy|verify|confirm|label|mark|set|put|move|"
    r"inspect|ensure|prefer|reject|allow|maximum|minimum)\b\s", re.I)
PROGRESSIVE = re.compile(
    r"^(?:i'm|we're|now|then)?\s*(?:currently\s+)?"
    r"(running|building|writing|checking|saving|updating|reading|tracing|drafting|"
    r"finishing|working|moving|adding|preparing|generating|reviewing|ensuring|"
    r"verifying|probing|scanning|switching|continuing|holding|waiting|looking|starting)\b", re.I)
INTERJECTION = re.compile(
    r"^(glad|happy|nice|great|good|thanks|thank you|sorry|yes|no|right|correct|agreed|"
    r"exactly|indeed|ok|okay|perfect|understood)\b", re.I)
CANT = re.compile(r"\b(cannot|can't|could not|couldn't|did not|didn't|does not|doesn't|"
                  r"won't|will not|unable to)\s+(?:\w+\s+){0,2}\w*$", re.I)
NOT_AGENT_SUBJ = re.compile(r"^(he|she|they|someone|somebody|nobody|no one|everyone|"
                            r"people|you|your|his|her|their|the author|the user)\b", re.I)
ADJECTIVAL = re.compile(r"\b(a|an|the|any|every|each|one|no|this|that|these|those)\s+$", re.I)

P1 = re.compile(r"\b(?:i|we)(?:'ve| have| had)?\b[^.;]{0,80}?\b" + VERB, re.I)
P2 = re.compile(r"^" + VERB, re.I)
P2b = re.compile(r"^[\w./-]{1,40}\s*[:\-–—]+\s*(?:" + VERB + r"|done|complete|green|clean|live|"
                 r"passed|passes|pass|failed|ok)(?![-\w])", re.I)
SUBJ_HEAD = (r"^(?:the |a |an |every |all |both |two |three |four |five |\d+ )?"
             r"[\w`'./-]+[,;:]?(?:\s+[\w`'.,/-]+){0,5}\s+")
P2c = re.compile(SUBJ_HEAD + VERB, re.I)
P2d = re.compile(SUBJ_HEAD + r"(?:" + OUT + r")(?![-\w])", re.I)
STATE_DONE = re.compile(
    r"\b(?:is|are|was|were|now)\s+(?:\w+[-\w]*\s+){0,2}"
    r"(?:done|complete|completed|fixed|shipped|deployed|merged|pushed|landed|green|clean|"
    r"closed|public|verified|committed|written|built|added|gone)(?![-\w])", re.I)
STATE_DONE2 = re.compile(r"\b(?:done|shipped|deployed|landed|closed|complete)(?![-\w])\s*[.!]", re.I)

SENT = re.compile(r"(?<=[.;!])\s+")


def _sentences(line: str):
    s = line.strip().replace("’", "'").replace("‘", "'")
    s = BULLET.sub("", s)
    s = UNDER.sub("", DECOR.sub("", s)).strip()
    return [x.strip() for x in SENT.split(s) if x.strip()]


def _accept(sent: str):
    """Position of the accepting match in one sentence, or None."""
    for rx in (P1, P2, P2b, P2c, P2d, STATE_DONE, STATE_DONE2):
        m = rx.search(sent)
        if m:
            head = sent[:m.end()]
            if CANT.search(head):          # "cannot be generated" is not work done
                continue
            # an adjectival use ("the verified claim", "a deployed app") asserts nothing
            vm = list(re.finditer(VERB, sent[m.start():m.end()], re.I))
            if vm and ADJECTIVAL.search(sent[m.start():m.start() + vm[-1].start()]):
                continue
            return m.start()
    mo = OUTCOME_LOOSE.search(sent) or STATUS_TOKEN.search(sent)
    if mo:
        for ms in CHECK_SUBJ.finditer(sent):
            # the checked thing is named BEFORE its outcome; a bare number must be adjacent
            gap = mo.start() - ms.end()
            if 0 <= gap <= (6 if ms.group(0).isdigit() else 25):
                return mo.start()
    return None


def _sentence_is_claim(sent: str) -> bool:
    if not sent or sent.endswith("?"):
        return False
    if SPEC.search(sent) or COND_HEAD.search(sent) or COND_MID.search(sent):
        return False
    if IMPERATIVE_HEAD.search(sent) or PROGRESSIVE.search(sent) or INTERJECTION.search(sent):
        return False
    if NOT_AGENT_SUBJ.search(sent) or INTENT_HARD.search(sent):
        return False
    pos = _accept(sent)
    if pos is None:
        return False
    m = INTENT.search(sent)
    if m and m.start() < pos:          # the intent governs the verb
        return False
    return True


def is_claim_line(line: str) -> bool:
    raw = line.strip()
    if not raw or NOT_PROSE.search(raw):
        return False
    flat = UNDER.sub("", DECOR.sub("", BULLET.sub("", raw.replace("’", "'")))).strip()
    if flat.endswith(":") and "." not in flat[:-1]:
        return False                    # a label that introduces a list
    return any(_sentence_is_claim(s) for s in _sentences(raw))


RULE_PARTS = (NOT_PROSE, VERB, OUT, OUTCOME, OUTCOME_LOOSE, STATUS_TOKEN, CHECK_SUBJ, SPEC,
              INTENT_HARD, INTENT, COND_HEAD, COND_MID, IMPERATIVE_HEAD, PROGRESSIVE,
              INTERJECTION, CANT, NOT_AGENT_SUBJ, ADJECTIVAL, P1, P2, P2b, P2c, P2d,
              STATE_DONE, STATE_DONE2, DECOR, UNDER, BULLET, SENT)


def rule_fingerprint() -> str:
    """A digest of every pattern the claim rule is made of.

    The published precision and recall belong to THIS rule text. The digest is stored beside
    those numbers in docs/claim-calibration.json, and a test fails when the rule changes and the
    calibration does not: a measured claim about an instrument stops being true the moment the
    instrument is edited.
    """
    import hashlib
    blob = "\n".join(p if isinstance(p, str) else p.pattern for p in RULE_PARTS)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


# ---- the evidence side (unchanged, and still unmeasured: see the docstring) ----
_TEST_NAME = re.compile(r"\btest_\w+")
_PATH = re.compile(r"[\w.\-]+(?:/[\w.\-]+)+\.\w{1,6}|\b[\w\-]+\.(?:py|ts|js|tsx|jsx|md|json|html|toml|sh|yml|yaml)\b")
_GENERIC_OK = re.compile(r"\b\d+ passed\b|^OK\b|\bexit(?: code)? 0\b", re.M)
_GENERIC_BAD = re.compile(r"\b\d+ failed\b|\bFAILED\b|\bTraceback\b")


@dataclass
class Claim:
    line: str
    tokens: set = field(default_factory=set)   # test names + paths named in the claim line
    verified: bool = False


def claims_in(text: str) -> list[Claim]:
    """Every line of assistant text that reads as a claim. Never persisted; counts only leave."""
    out = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or not is_claim_line(line):
            continue
        toks = set(_TEST_NAME.findall(line)) | set(_PATH.findall(line))
        out.append(Claim(line=line, tokens=toks))
    return out


def evidence_matches(claim: Claim, result_text: str) -> bool:
    if not result_text:
        return False
    for tok in claim.tokens:
        if tok in result_text:
            return True
    if _GENERIC_OK.search(result_text) and not _GENERIC_BAD.search(result_text):
        return True
    return False


class ClaimTracker:
    """Feed it the trace in order; read `claims` / `verified` at the end.

    A 'turn' is the span after one typed human turn up to the next. Claims and tool results
    collect per turn; when the turn closes (next typed turn or end of file) each claim is checked
    against every result of that turn, before or after it.
    """

    def __init__(self) -> None:
        self.claims = 0
        self.verified = 0
        self._turn_claims: list[Claim] = []
        self._turn_results: list[str] = []

    def typed_turn(self) -> None:
        self._close()

    def assistant_text(self, text: str) -> None:
        self._turn_claims.extend(claims_in(text))

    def tool_result(self, text: str) -> None:
        if text:
            self._turn_results.append(text)

    def close(self) -> None:
        self._close()

    def _close(self) -> None:
        for c in self._turn_claims:
            c.verified = any(evidence_matches(c, r) for r in self._turn_results)
            self.claims += 1
            self.verified += int(c.verified)
        self._turn_claims = []
        self._turn_results = []


def result_text(o: dict) -> str:
    """Flatten one `type: user` tool_result record (or its toolUseResult) to searchable text."""
    parts: list[str] = []
    msg = o.get("message") if isinstance(o.get("message"), dict) else {}
    c = msg.get("content")
    if isinstance(c, list):
        for b in c:
            if isinstance(b, dict) and b.get("type") == "tool_result":
                inner = b.get("content")
                if isinstance(inner, str):
                    parts.append(inner)
                elif isinstance(inner, list):
                    parts.extend(x.get("text", "") for x in inner if isinstance(x, dict))
    tr = o.get("toolUseResult")
    if isinstance(tr, dict):
        for k in ("stdout", "stderr", "output", "listing"):
            v = tr.get(k)
            if isinstance(v, str):
                parts.append(v)
    elif isinstance(tr, str):
        parts.append(tr)
    return "\n".join(p for p in parts if p)


def is_tool_result(o: dict) -> bool:
    msg = o.get("message") if isinstance(o.get("message"), dict) else {}
    c = msg.get("content")
    return o.get("type") == "user" and isinstance(c, list) and any(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in c)
