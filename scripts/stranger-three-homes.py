#!/usr/bin/env python3
"""Phase 1 — three temp HOMEs following the live site literally.

A stranger with Claude, Cursor, or Codex should reach a card from the command the website
hands them. This script:

  1. Fetches the LIVE site and extracts INSTALL_CMD (not the local checkout — the object).
  2. Builds three disposable HOMEs with synthetic, labelled-as-fixture transcripts.
  3. Runs the live install command's grind step under each HOME (card file, then --json).
  4. Also runs the empty-HOME path (no sessions) and records PASS or BLOCKED with the exact step.
  5. Writes a JSON receipt under docs/ and prints a markdown summary to stdout.

No real user transcript is read or written. Outward acts are Oscar's click: this never pushes.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LIVE = "https://agentgrinder.vercel.app/"

# Synthetic fixtures only. Written for this script; not drawn from any real transcript.
CLAUDE_JSONL = (REPO / "samples" / "sample_session.jsonl").read_text(encoding="utf-8")

CURSOR_JSONL = """\
{"role":"user","message":{"content":"<timestamp>Thursday, Sep 04, 2026, 10:00 AM</timestamp><user_query>[fixture] build the retry helper</user_query>"}}
{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Write","input":{"path":"samples/fixture-project/notes.md"}},{"type":"text","text":"Working."}]}}
{"role":"user","message":{"content":"<timestamp>Thursday, Sep 04, 2026, 10:01 AM</timestamp><user_query>[fixture] run the suite</user_query>"}}
{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Shell","input":{"command":"pytest -q"}},{"type":"text","text":"Added samples/fixture-project/notes.md and the suite is green at 12 tests."}]}}
"""

CODEX_JSONL = """\
{"type":"session_meta","payload":{"cwd":"/tmp/fixture-codex-app"}}
{"type":"user_message","content":"[fixture] wire the health check"}
{"role":"assistant","content":[{"type":"tool_use","name":"exec"},{"type":"text","text":"Deployed the worker to staging; the health check answers 200."}]}
{"type":"user_message","content":"[fixture] confirm"}
{"role":"assistant","content":[{"type":"text","text":"Still looking."}]}
"""


def fetch_live_install_cmd() -> tuple[str, str]:
    html = urllib.request.urlopen(LIVE, timeout=20).read().decode()
    m = re.search(r'const INSTALL_CMD="([^"]+)"', html)
    if not m:
        raise SystemExit("LIVE site no longer defines INSTALL_CMD — stranger path unreadable")
    cmd = m.group(1)
    bad = []
    for n, line in enumerate(html.splitlines(), 1):
        if "pip install -e ." not in line:
            continue
        if line.lstrip().startswith("//"):
            continue
        if "[coach]" in line or "venv" in line:
            continue
        bad.append(f"L{n}")
    return cmd, ",".join(bad)


def local_install_cmd() -> tuple[str, str]:
    html = (REPO / "site" / "index.html").read_text(encoding="utf-8")
    m = re.search(r'const INSTALL_CMD="([^"]+)"', html)
    if not m:
        raise SystemExit("local site/index.html has no INSTALL_CMD")
    cmd = m.group(1)
    bad = []
    for n, line in enumerate(html.splitlines(), 1):
        if "pip install -e ." not in line:
            continue
        if line.lstrip().startswith("//"):
            continue
        if "[coach]" in line or "venv" in line:
            continue
        bad.append(f"L{n}")
    return cmd, ",".join(bad)


def plant_home(root: Path, harness: str) -> Path:
    home = root / f"home-{harness}"
    home.mkdir(parents=True)
    if harness == "claude":
        d = home / ".claude" / "projects" / "-tmp-fixture-app"
        d.mkdir(parents=True)
        (d / "session.jsonl").write_text(CLAUDE_JSONL, encoding="utf-8")
    elif harness == "cursor":
        d = home / ".cursor" / "projects" / "tmp-fixture-app" / "agent-transcripts" / "aaaa"
        d.mkdir(parents=True)
        (d / "t.jsonl").write_text(CURSOR_JSONL, encoding="utf-8")
    elif harness == "codex":
        d = home / ".codex" / "sessions" / "2026" / "09" / "04"
        d.mkdir(parents=True)
        (d / "rollout-fixture.jsonl").write_text(CODEX_JSONL, encoding="utf-8")
    else:
        raise ValueError(harness)
    return home


def _env(home: Path, out_dir: Path) -> dict:
    return dict(os.environ, HOME=str(home),
                AGENTGRINDER_SERIES=str(out_dir / "series.db"),
                PYTHONPATH=str(REPO) + os.pathsep + os.environ.get("PYTHONPATH", ""))


def run_grind(home: Path, out_dir: Path, repo: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    card = out_dir / "grind.html"
    env = _env(home, out_dir)
    # Card first — the stranger's object. --json alone skips the HTML on the Claude path.
    card_proc = subprocess.run(
        [sys.executable, "-m", "agentgrinder", "grind", "--no-open", "-o", str(card)],
        cwd=str(repo), capture_output=True, text=True, env=env)
    json_proc = subprocess.run(
        [sys.executable, "-m", "agentgrinder", "grind", "--no-open", "--json",
         "-o", str(out_dir / "ignored.html")],
        cwd=str(repo), capture_output=True, text=True, env=env)
    run = None
    if json_proc.returncode == 0 and "{" in (json_proc.stdout or ""):
        try:
            run = json.loads(json_proc.stdout[json_proc.stdout.index("{"):])
        except json.JSONDecodeError:
            run = None
    result = {
        "rc": card_proc.returncode,
        "json_rc": json_proc.returncode,
        "card_exists": card.exists() and card.stat().st_size > 200,
        "card_bytes": card.stat().st_size if card.exists() else 0,
        "stdout_tail": (card_proc.stdout or "")[-1200:],
        "stderr_tail": (card_proc.stderr or "")[-400:],
        "harness_picked": (run or {}).get("harness"),
        "turns_typed": (run or {}).get("turns_typed"),
        "claims": (run or {}).get("claims"),
        "claims_verified": (run or {}).get("claims_verified"),
        "artifacts_produced": (run or {}).get("artifacts_produced"),
        "corrections": (run or {}).get("corrections"),
        "artifacts_promised": (run or {}).get("artifacts_promised"),
        "reach": (run or {}).get("reach"),
        "produced_reason": (run or {}).get("produced_reason"),
        "reach_reason": (run or {}).get("reach_reason"),
        "headline": None,
    }
    v, a, t = result.get("claims_verified"), result.get("artifacts_produced"), result.get("turns_typed")
    if v is not None and a is not None and t:
        result["headline"] = round((v + a) / t, 4)
    return result


def audit_dashes(result: dict) -> list[str]:
    """Unmeasured columns must be None (card prints —), never a fabricated 0."""
    lies = []
    for k in ("corrections", "artifacts_promised"):
        if result.get(k) is not None:
            lies.append(f"{k}={result[k]!r} (must be None — not measured)")
    return lies


def empty_home_path(repo: Path, root: Path) -> dict:
    home = root / "home-empty"
    home.mkdir()
    out = root / "out-empty"
    out.mkdir()
    env = _env(home, out)
    grind = subprocess.run(
        [sys.executable, "-m", "agentgrinder", "grind", "--no-open", "-o", str(out / "grind.html")],
        cwd=str(repo), capture_output=True, text=True, env=env)
    # demo must run from the clone: there is no install, so `python3 -m agentgrinder` resolves
    # against the repo on sys.path / cwd package layout.
    demo = subprocess.run(
        [sys.executable, "-m", "agentgrinder", "demo", "--no-open"],
        cwd=str(repo), capture_output=True, text=True, env=env)
    # demo writes card.html into cwd (= repo). Move it so we do not litter.
    written = repo / "card.html"
    demo_card = out / "card.html"
    if written.exists():
        written.replace(demo_card)
    return {
        "grind_rc": grind.returncode,
        "grind_names_paths": all(p in grind.stdout for p in (
            "~/.claude/projects/*/*.jsonl",
            "~/.cursor/projects/*/agent-transcripts/*/*.jsonl",
            "~/.codex/sessions/**/*.jsonl",
        )),
        "grind_points_at_demo": "python3 -m agentgrinder demo" in grind.stdout,
        "demo_rc": demo.returncode,
        "demo_card": demo_card.exists() and demo_card.stat().st_size > 200,
        "demo_stdout_tail": (demo.stdout or "")[-800:],
        "grind_stdout_tail": (grind.stdout or "")[-800:],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--local-cmd", action="store_true",
                    help="read INSTALL_CMD from the local checkout instead of the live site")
    ap.add_argument("--repo", type=Path, default=REPO,
                    help="checkout to run grind from (default: this repo)")
    ap.add_argument("--out", type=Path,
                    default=REPO / "docs" / "stranger-three-homes-2026-09-04.json")
    args = ap.parse_args()
    args.out = args.out if args.out.is_absolute() else (Path.cwd() / args.out)

    if args.local_cmd:
        install_cmd, bad_pip = local_install_cmd()
        cmd_source = "local site/index.html"
    else:
        try:
            install_cmd, bad_pip = fetch_live_install_cmd()
            cmd_source = LIVE
        except Exception as e:
            install_cmd, bad_pip = local_install_cmd()
            cmd_source = f"local fallback ({e})"

    root = Path(tempfile.mkdtemp(prefix="ag-stranger-"))
    receipt = {
        "measured": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cmd_source": cmd_source,
        "install_cmd": install_cmd,
        "bare_pip_still_on_page": bad_pip,
        "homes": {},
        "empty_home": None,
        "verdict": {},
    }

    receipt["empty_home"] = empty_home_path(args.repo, root)

    for harness in ("claude", "cursor", "codex"):
        home = plant_home(root, harness)
        result = run_grind(home, root / f"out-{harness}", args.repo)
        result["lies"] = audit_dashes(result)
        ok = (result["rc"] == 0 and result["card_exists"] and result["json_rc"] == 0
              and not result["lies"] and result.get("turns_typed"))
        result["status"] = "PASS" if ok else "BLOCKED"
        if not ok:
            if result["rc"] != 0:
                result["blocked_at"] = "grind (nonzero exit)"
            elif not result["card_exists"]:
                result["blocked_at"] = "grind (no card file)"
            elif result["json_rc"] != 0:
                result["blocked_at"] = "grind --json (nonzero exit)"
            elif not result.get("turns_typed"):
                result["blocked_at"] = "grind --json produced no turns_typed"
            else:
                result["blocked_at"] = "honesty audit: " + "; ".join(result["lies"])
        receipt["homes"][harness] = result

    eh = receipt["empty_home"]
    empty_ok = (eh["grind_rc"] == 1 and eh["grind_names_paths"] and eh["grind_points_at_demo"]
                and eh["demo_rc"] == 0 and eh["demo_card"])
    receipt["verdict"] = {
        "empty_home": "PASS" if empty_ok else "BLOCKED",
        "claude": receipt["homes"]["claude"]["status"],
        "cursor": receipt["homes"]["cursor"]["status"],
        "codex": receipt["homes"]["codex"]["status"],
        "bare_pip_strings_on_cmd_source": bool(bad_pip),
    }
    all_pass = all(receipt["verdict"][k] == "PASS" for k in ("empty_home", "claude", "cursor", "codex"))
    receipt["verdict"]["overall"] = "PASS" if all_pass and not bad_pip else (
        "PASS_WITH_LIVE_PIP_LIE" if all_pass else "BLOCKED")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    try:
        rel = args.out.relative_to(REPO)
    except ValueError:
        rel = args.out

    md = args.out.with_suffix(".md")
    lines = [
        f"# Stranger → card · three HOMEs · {receipt['measured'][:10]}",
        "",
        f"**INSTALL_CMD source:** `{cmd_source}`",
        "",
        "```",
        install_cmd,
        "```",
        "",
        f"Bare `pip install -e .` still on that page: "
        f"**{'YES — ' + bad_pip if bad_pip else 'no'}**",
        "",
        "| Path | Status | Detail |",
        "|------|--------|--------|",
        f"| empty HOME → grind | {receipt['verdict']['empty_home']} | "
        f"rc={eh['grind_rc']}, names paths={eh['grind_names_paths']}, "
        f"points at demo={eh['grind_points_at_demo']}, demo rc={eh['demo_rc']}, "
        f"demo card={eh['demo_card']} |",
    ]
    for h, r in receipt["homes"].items():
        detail = (f"rc={r['rc']}, card={r['card_exists']} ({r['card_bytes']}B), "
                  f"harness={r.get('harness_picked')}, turns={r.get('turns_typed')}, "
                  f"claims={r.get('claims_verified')}/{r.get('claims')}, "
                  f"artifacts={r.get('artifacts_produced')}, headline={r.get('headline')}")
        if r["status"] != "PASS":
            detail += f" · blocked_at={r.get('blocked_at')}"
        lines.append(f"| {h} HOME → grind | {r['status']} | {detail} |")
    lines += [
        "",
        f"**Overall:** `{receipt['verdict']['overall']}`",
        "",
        f"Machine receipt (counts only): `{rel}`",
        "",
        "Fixtures are synthetic lines written for this script (Claude uses "
        "`samples/sample_session.jsonl`). No real transcript text is stored.",
        "",
    ]
    md.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    shutil.rmtree(root, ignore_errors=True)
    return 0 if receipt["verdict"]["overall"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
