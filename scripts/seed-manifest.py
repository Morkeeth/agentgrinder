#!/usr/bin/env python3
"""Filter git ls-files output through seed-manifest.txt exclude globs."""
from __future__ import annotations

import fnmatch
import sys
from pathlib import Path

MANIFEST = Path(__file__).resolve().parent / "seed-manifest.txt"


def load_excludes() -> list[str]:
    out: list[str] = []
    for line in MANIFEST.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("!"):
            out.append(line[1:])
    return out


def included(path: str, excludes: list[str]) -> bool:
    for pat in excludes:
        if fnmatch.fnmatch(path, pat):
            return False
    return True


def main() -> int:
    excludes = load_excludes()
    for line in sys.stdin:
        path = line.strip()
        if path and included(path, excludes):
            print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
