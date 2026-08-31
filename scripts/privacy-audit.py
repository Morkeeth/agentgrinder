#!/usr/bin/env python3
"""Walk a directory and report privacy findings per file.

Text/HTML: uses agentgrinder.privacy.scan / scan_html.
Images: UNSCANNED (no OCR vendored in this repo).
DOC-GLOB: tool-path documentation only — passes seed, listed for review.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from agentgrinder import privacy  # noqa: E402

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
TEXT_EXT = {".md", ".py", ".json", ".toml", ".txt", ".html", ".htm", ".svg", ".css", ".js", ".ts"}

# Documented tool locations — not Oscar-specific secrets (see PRIVACY-2026-08-31.md §1c)
_DOC_GLOB = re.compile(
    r"(~/.claude(?:\.json|/projects|/settings\.json|/skills)?"
    r"|~/.cursor/projects"
    r"|~/.agentgrinder/"
    r"|\.claude/(?:projects|settings\.json|skills)"
    r"|\.cursor/projects"
    r"|agent-transcripts"
    r"|/\*\.jsonl"
    r"|~/CODE/[a-zA-Z0-9_-]+"
    r"|~/.codex(?:/archived_sessions)?"
    r"|~/CODE,)"
)


def _is_doc_glob(rule: str, hit: str) -> bool:
    if rule == "memory-filename" and hit in ("archive", "reference"):
        return True
    if rule == "memory-filename" and "archived_sessions" in hit:
        return True
    if rule in ("home-tilde", "claude-dir", "home-any") and _DOC_GLOB.search(hit):
        return True
    if rule == "notes-vault" and "obsidian" in hit.lower() and "synced" not in hit.lower():
        # generic product architecture mention
        return True
    return False


def classify_findings(found: list[tuple[str, str]]) -> tuple[str, list[tuple[str, str]]]:
    if not found:
        return "CLEAN", []
    if all(_is_doc_glob(r, h) for r, h in found):
        return "DOC-GLOB", found
    return "DIRTY", found


def classify(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGE_EXT:
        return "UNSCANNED"
    if ext in TEXT_EXT or not ext:
        return "SCAN"
    return "SKIP"


def audit_file(path: str) -> tuple[str, list[tuple[str, str]]]:
    if os.path.basename(path) == "privacy-audit.py":
        return "SKIP", []
    kind = classify(path)
    if kind == "UNSCANNED":
        return "UNSCANNED", []
    if kind == "SKIP":
        return "SKIP", []
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError as e:
        return "SKIP", [("read-error", str(e))]
    if not text.strip():
        return "EMPTY", []
    if path.endswith((".html", ".htm", ".svg")):
        found = privacy.scan_html(text)
    else:
        found = privacy.scan(text)
    return classify_findings(found)


def walk(root: str) -> list[dict]:
    rows: list[dict] = []
    for dirpath, _, filenames in os.walk(root):
        for name in sorted(filenames):
            if name == ".DS_Store":
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            verdict, found = audit_file(full)
            rows.append({
                "path": rel,
                "verdict": verdict,
                "findings": found,
                "count": len({f for f in found}),
            })
    return rows


def print_report(rows: list[dict], root: str) -> int:
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

    print(f"# privacy audit — {root}\n")
    print("| verdict | count |")
    print("|---------|-------|")
    for v in ("CLEAN", "DOC-GLOB", "DIRTY", "UNSCANNED", "EMPTY", "SKIP"):
        if counts.get(v):
            print(f"| {v} | {counts[v]} |")
    print()

    for label in ("DIRTY", "DOC-GLOB"):
        group = [r for r in rows if r["verdict"] == label]
        if not group:
            continue
        print(f"## {label} files\n")
        for r in group:
            print(f"### `{r['path']}` — {r['count']} distinct\n")
            seen: set[tuple[str, str]] = set()
            for rule, hit in r["findings"]:
                if (rule, hit) in seen:
                    continue
                seen.add((rule, hit))
                print(f"- **{rule}**: `{hit[:100]}`")
            print()

    unscanned = [r for r in rows if r["verdict"] == "UNSCANNED"]
    if unscanned:
        print(f"## UNSCANNED images ({len(unscanned)})\n")
        print("PNG/JPEG contents not read — OCR not vendored. Open at real size before publish.\n")
        for r in unscanned[:20]:
            print(f"- `{r['path']}`")
        if len(unscanned) > 20:
            print(f"- … and {len(unscanned) - 20} more")
        print()

    return counts.get("DIRTY", 0)


def main() -> int:
    p = argparse.ArgumentParser(description="Privacy audit walk for seed review")
    p.add_argument("directory", help="root to audit (e.g. /tmp/grinder-seed)")
    args = p.parse_args()
    root = os.path.abspath(args.directory)
    if not os.path.isdir(root):
        print(f"not a directory: {root}", file=sys.stderr)
        return 2
    rows = walk(root)
    dirty = print_report(rows, root)
    return 1 if dirty else 0


if __name__ == "__main__":
    sys.exit(main())
