"""The v0 claim rule: which of the agent's claims carry tool evidence in the same trace.

This is a LOCAL STAND-IN for `helicon witness` (the owner of verified-claims share in
fleet-ops/METRICS-AGENTIC-ENGINEERING-2026-09-02.md). It is deliberately small and every step
is named so it can be replaced, not trusted:

  claim     = a line of assistant TEXT matching CLAIM_RE
              (passes|passed|fixed|done|deployed|works|green|verified|ship|ships|shipped)
  evidence  = a tool_result in the SAME HUMAN TURN (the span between two typed turns) whose text
              carries a token that matches the claim:
                - a test name from the claim line      (test_\\w+)
                - a file path from the claim line      (something/with.ext)
                - a generic success token              ("N passed", a line starting "OK", "exit 0" / "exit code 0")
                  which does NOT count if the same result also says "N failed" / "FAILED" / "Traceback"
  verified  = the claim has at least one such evidence result

DEVIATION, stated: the brief said "followed ... by a tool_use". In real traces the agent runs the
check FIRST and then states the claim, so a strictly-after window marks almost every true claim
unverified — a red light nobody audits. The window is therefore the whole human turn, either side
of the claim. Evidence from a different human turn never counts.

Known v0 blind spots (documented, not hidden): a claim about one thing can be "verified" by a
passing test for another thing in the same turn; "done" as a heading matches; prose that quotes
an error while claiming a fix is read as a claim. Probed 2 Sep over 11 real sittings: most read
100% verified — the rule OVER-COUNTS. Treat the share as a ceiling, not a proof, until Helicon
witness replaces it. No prompt text leaves this function — it returns counts.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

CLAIM_RE = re.compile(r"\b(passes|passed|fixed|done|deployed|works|green|verified|ships?|shipped)\b", re.I)
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
        if not line or not CLAIM_RE.search(line):
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
