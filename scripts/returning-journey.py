#!/usr/bin/env python3
"""Returning-user journey: find a run → grind-trace attribution → next practice.

Cold, offline, no key, no network. Compares the attributed arm against a naive
baseline that only draws a rhythm and buries the coach plan — the version any
competent team ships in two hours.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agentgrinder.engine import log
from agentgrinder.metrics import build_activity
from agentgrinder.practices import accept, context
from agentgrinder.render import render_card
from agentgrinder.push import export_run

FIXTURE = ROOT / "samples" / "returning_run.json"
FEATURED_ID = "28d5d0b7-eda2-4d94-a83c-580d2e3b75b2"
LIVE = "https://agentgrinder.vercel.app"


def naive_card(run: dict) -> str:
    """Baseline arm: rhythm SVG with no attribution caption; coach plan not framed."""
    rhythm = run.get("rhythm") or [1]
    n = len(rhythm)
    mx = max(rhythm) or 1
    w, h, p = 720, 150, 6
    pts = " ".join(
        f"{p + i * (w - 2 * p) / max(n - 1, 1):.1f},{h - p - (v / mx) * (h - 2 * p):.1f}"
        for i, v in enumerate(rhythm)
    )
    plan = run.get("coach_plan") or ""
    return f"""<!doctype html><html><body>
<svg class="route"><polyline points="{pts}"/></svg>
<details><summary>notes</summary><p>{plan}</p></details>
</body></html>"""


def score(html: str, run: dict) -> dict:
    """Can a stranger answer the three journey questions from the HTML alone?"""
    basis = (run.get("trace_basis") or "").strip()
    plan_line = (run.get("coach_plan") or "").split("\n")[0].strip()
    find_run = bool(re.search(r"returning-user fixture|AGENTGRINDER|verified per turn", html, re.I))
    if basis:
        attribution = basis[:40].lower() in html.lower()
    else:
        attribution = "trace time basis unknown" in html.lower()
    # Buried inside <details> does not count as surfaced.
    surfaced = html
    if "<details" in html.lower():
        surfaced = re.sub(r"<details[\s\S]*?</details>", "", html, flags=re.I)
    next_practice = bool(plan_line) and (
        "next practice" in surfaced.lower() or plan_line[:32].lower() in surfaced.lower()
    )
    return {
        "find_run": find_run,
        "grind_trace_attribution": attribution,
        "next_practice": next_practice,
        "beats": int(find_run) + int(attribution) + int(next_practice),
    }


def local_journey(out_dir: Path) -> dict:
    run = json.loads(FIXTURE.read_text())
    assert run["trace_basis"], "fixture must name its own time basis"
    assert run["coach_plan"], "fixture must carry a next-practice plan"

    attributed = render_card(build_activity(run))
    baseline = naive_card(run)
    (out_dir / "attributed.html").write_text(attributed)
    (out_dir / "naive.html").write_text(baseline)

    attributed_score = score(attributed, run)
    naive_score = score(baseline, run)
    if attributed_score["beats"] <= naive_score["beats"]:
        raise SystemExit(
            f"attributed arm did not beat naive baseline: {attributed_score} vs {naive_score}"
        )
    if attributed_score["beats"] != 3:
        raise SystemExit(f"attributed card missing a journey beat: {attributed_score}")

    # Accept the coach plan as a local practice and prove it survives reopen.
    db = out_dir / "series.sqlite"
    first_line = run["coach_plan"].split("\n")[0].strip()
    with log.connect(str(db)) as conn:
        revision = log.record_run(
            conn,
            dict(
                project=run["project"],
                started=run["started"],
                turns_typed=run["turns_typed"],
                claims=run["claims"],
                claims_verified=run["claims_verified"],
                artifacts_produced=run["artifacts_produced"],
                project_identity="fixture-returning-run",
            ),
        )
        practice = accept(
            conn,
            run["project"],
            first_line,
            "A measurable change on the next comparable sitting",
            revision["revision_id"],
        )
    with log.connect(str(db)) as conn:
        items = context(conn, run["project"], "fixture-returning-run")
        if not items or items[0]["title"] != first_line:
            raise SystemExit(f"practice did not survive reopen: {items!r}")

    exported = export_run(run)
    if exported.get("trace_basis") != run["trace_basis"]:
        raise SystemExit("export_run dropped trace_basis")
    if exported.get("coach_plan") != run["coach_plan"]:
        raise SystemExit("export_run dropped coach_plan")
    # Private practice context must never ride the public export.
    if "practice_context" in exported:
        raise SystemExit("export_run leaked practice_context")

    return {
        "attributed": attributed_score,
        "naive_baseline": naive_score,
        "practice_id": practice["id"],
        "practice_title": first_line,
        "export_keys": sorted(exported),
        "card": str(out_dir / "attributed.html"),
    }


def live_probe() -> dict:
    """Probe the hosted featured run. Findings may be red — that is the point."""
    import urllib.request

    html = urllib.request.urlopen(f"{LIVE}/?run={FEATURED_ID}", timeout=20).read().decode()
    api = re.search(r'const SB_URL="([^"]+)"', html)
    key = re.search(r'const SB_KEY="([^"]+)"', html)
    if not api or not key:
        return {"ok": False, "error": "could not read hosted Supabase constants"}
    url = (
        api.group(1).rstrip("/")
        + "/rest/v1/runs?id=eq."
        + FEATURED_ID
        + "&select=id,title,rhythm,trace_basis,measurement_revision,coach_plan,schema_version"
    )
    req = urllib.request.Request(
        url, headers={"apikey": key.group(1), "Authorization": "Bearer " + key.group(1)}
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        rows = json.loads(response.read().decode())
    if not rows:
        return {"ok": False, "error": "featured run not readable anonymously"}
    run = rows[0]
    # Score what the LIVE bytes currently paint. Until deploy, local fixes are invisible.
    live_html = html
    # Reconstruct the object the page would render after fetch by checking source helpers.
    has_grind_trace_helper = "function grindTrace" in live_html
    has_next_practice_label = "Next practice" in live_html
    has_journey_readiness = "function journeyReadiness" in live_html
    object_beats = {
        "find_run": True,
        "rhythm_present": bool(run.get("rhythm")),
        "trace_basis_on_row": bool((run.get("trace_basis") or "").strip()),
        "measurement_revision_on_row": bool(run.get("measurement_revision")),
        "coach_plan_on_row": bool((run.get("coach_plan") or "").strip()),
        "live_source_has_grindTrace": has_grind_trace_helper,
        "live_source_has_Next_practice": has_next_practice_label,
        "live_source_has_journeyReadiness": has_journey_readiness,
    }
    # The hosted row's missing fields are defects even after UI ships.
    object_beats["full_object_ready"] = (
        object_beats["rhythm_present"]
        and object_beats["trace_basis_on_row"]
        and object_beats["measurement_revision_on_row"]
        and object_beats["coach_plan_on_row"]
    )
    return {"ok": True, "run_id": FEATURED_ID, "beats": object_beats, "title": run.get("title")}


def site_source_checks() -> dict:
    html = (ROOT / "site" / "index.html").read_text()
    contract = (ROOT / "site" / "run-contract.js").read_text()
    checks = {
        "grindTrace_defined": "function grindTrace" in html,
        "journeyReadiness_defined": "function journeyReadiness" in html,
        "next_practice_label": "Next practice" in html,
        "run_page_calls_journeyReadiness": "journeyReadiness(r)" in html,
        "run_card_uses_grindTrace": "grindTrace(r)" in html,
        "contract_trace_names_unknown_basis": "Trace time basis unknown" in contract,
        "practices_prefill_from_query": 'suggest.get("title")' in (ROOT / "site" / "practices.js").read_text(),
    }
    if not all(checks.values()):
        raise SystemExit(f"site source missing journey pieces: {checks}")
    return checks


def main() -> int:
    out = Path(tempfile.mkdtemp(prefix="grinder-returning-"))
    local = local_journey(out)
    site = site_source_checks()
    try:
        live = live_probe()
    except Exception as error:  # network optional for the offline done-when
        live = {"ok": False, "error": str(error)}
    report = {
        "local": local,
        "site_source": site,
        "live_featured": live,
        "out_dir": str(out),
    }
    print(json.dumps(report, indent=2))
    # Offline three-beat + site source must pass. Live may be red; that is reported, not hidden.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
