"""AGENTGRINDER CLI — turn a coding-agent session into a shareable run card.

Usage:
  python3 -m agentgrinder demo                 # render the bundled sample
  python3 -m agentgrinder card RUN.json [-o out.html]
"""
from __future__ import annotations
import argparse, json, sys, webbrowser
from pathlib import Path
from .metrics import build_activity
from .render import render_card
from .ingest import parse_session, latest_session, parse_cursor_session, latest_cursor_session, best_recent_session, coach_lines
from .profile import build_profile
from .render import render_profile

SAMPLE = Path(__file__).resolve().parent.parent / "samples" / "sample_run.json"


def _render(run: dict, out: Path, open_it: bool) -> None:
    a = build_activity(run)
    out.write_text(render_card(a), encoding="utf-8")
    # terminal summary (Oscar reads the terminal too)
    print(f"\n  {a.athlete} · {a.title}")
    print(f"  {a.harness} · {a.project} · {a.date_str}")
    print(f"\n  VERIFIED PER TURN  {a.headline}    {a.headline_formula}")
    print("  " + " · ".join(f"{c.label} {c.value}" + (" (cost)" if c.cost else "") for c in a.five))
    print(f"\n  cost: {a.distance} | {a.moving_time} | {a.pace}")
    print(f"  effort {a.effort} · {a.segments} · {a.commits} commits · {a.prompts_per_hour}"
          + ("  ★ focus PB" if a.focus_pb else ""))
    print(f"\n  card -> {out}\n")
    if open_it:
        webbrowser.open(out.resolve().as_uri())


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="agentgrinder")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("demo", help="render the bundled sample run")
    d.add_argument("--no-open", action="store_true")
    c = sub.add_parser("card", help="render a run JSON to a card")
    c.add_argument("run"); c.add_argument("-o", "--out", default="card.html")
    c.add_argument("--no-open", action="store_true")
    g = sub.add_parser("grind", aliases=["run"],
                       help="one ordinary session -> the grind card (Claude Code or Cursor)")
    g.add_argument("session", nargs="?", help="path to a .jsonl (default: your most recent grind)")
    g.add_argument("--pick", type=int, default=None,
                   help="which sitting in that transcript (-1 = the last, 1 = the first)")
    g.add_argument("--list", action="store_true", help="list the sittings in the transcript and stop")
    g.add_argument("--gap", type=int, default=30,
                   help="minutes of total idle that end a grind (default 30)")
    g.add_argument("--athlete", default="you")
    g.add_argument("-o", "--out", default="grind.html")
    g.add_argument("--json", dest="as_json", action="store_true")
    g.add_argument("--harness", choices=["claude", "cursor", "codex", "auto"], default="claude",
                   help="which agent's transcript (auto = freshest Claude or Cursor)")
    g.add_argument("--no-rank", action="store_true",
                   help="skip the pass over your history (faster; drops the progression line)")
    g.add_argument("--show-paths", action="store_true",
                   help="OPT IN to printing paths outside this repo and the sentence you typed. "
                        "Off by default: see agentgrinder/privacy.py. Even on, a home path, a "
                        "synced-notes path or a memory filename is still refused.")
    g.add_argument("--no-open", action="store_true")
    g.add_argument("--push", action="store_true",
                   help="open the web importer with this grind's metrics (sign in there to publish)")
    g.add_argument("--share-rig-names", action="store_true",
                   help="with --push, include MCP server names in your shared rig (opt-in)")
    g.add_argument("--push-url", default=None,
                   help="web app base URL for --push (default: AGENTGRINDER_URL or agentgrinder.vercel.app)")
    fl = sub.add_parser("flex", help="compare your real runs across agents on this machine")
    fl.add_argument("--json", dest="as_json", action="store_true")
    sh = sub.add_parser("share", help="fun share card — claim-your-handle vibe, screenshot-ready")
    sh.add_argument("session", nargs="?", help="run JSON path (default: latest grind)")
    sh.add_argument("--claim", action="store_true", help="invite card — open handle slot")
    sh.add_argument("--profile", action="store_true", help="scrapbook card from local stats")
    sh.add_argument("--handle", default="you", help="GitHub handle on the card")
    sh.add_argument("--harness", choices=["claude", "cursor", "codex", "auto"], default="auto")
    sh.add_argument("-o", "--out", default="share.html")
    sh.add_argument("--no-open", action="store_true")
    sh.add_argument("--push-url", default=None, help="base URL printed on the claim stub")
    sh.add_argument("--vibe", action="store_true", help="stamp meme vibe on the card")
    sh.add_argument("--roast", action="store_true", help="add roast-shape lines to the card")
    vb = sub.add_parser("vibe", help="meme label for a grind — real numbers, no streaks")
    vb.add_argument("session", nargs="?", help="run JSON (default: latest grind)")
    vb.add_argument("--harness", choices=["claude", "cursor", "auto"], default="auto")
    vb.add_argument("--json", dest="as_json", action="store_true")
    rb = sub.add_parser("roast", help="roast your grind shape — receipts only, no streaks")
    rb.add_argument("session", nargs="?", help="run JSON (default: latest grind)")
    rb.add_argument("--json", dest="as_json", action="store_true")
    rg = sub.add_parser("rig", help="share your stack — MCPs, skills, harnesses")
    rg.add_argument("--handle", default="you")
    rg.add_argument("--share-names", action="store_true", help="print MCP server names on the card")
    rg.add_argument("--anon", action="store_true", help="ghost rig card — no handle")
    rg.add_argument("-o", "--out", default="rig.html")
    rg.add_argument("--no-open", action="store_true")
    hs = sub.add_parser("heist", help="rig heist card — someone ACKed your stack")
    hs.add_argument("victim", help="whose rig was ACKed (@handle)")
    hs.add_argument("--thief", default="friend", help="who ACKed")
    hs.add_argument("--harness", default="Claude Code")
    hs.add_argument("-o", "--out", default="heist.html")
    hs.add_argument("--no-open", action="store_true")
    hi = sub.add_parser("history", help="every grind on this machine, ranked (local only)")
    hi.add_argument("--top", type=int, default=15)
    lg = sub.add_parser("login", help="open the web app to sign in with GitHub")
    lg.add_argument("--url", default=None, help="web app base URL")
    a2 = sub.add_parser("a2a", help="Agent Activity protocol — export, feed, onboarding")
    a2sub = a2.add_subparsers(dest="a2cmd", required=True)
    a2sub.add_parser("onboard", help="print A2A agent onboarding (for MCP agents)")
    ex = a2sub.add_parser("export", help="export latest grind as A2A JSON")
    ex.add_argument("--harness", choices=["claude", "cursor"], default="claude")
    ex.add_argument("--handle", default="you")
    fd = a2sub.add_parser("feed", help="fetch public grinds (network)")
    fd.add_argument("--handle", default=None, help="athlete GitHub handle")
    fd.add_argument("--limit", type=int, default=10)
    ak = a2sub.add_parser("ack", help="open web to ACK a grind (human confirms)")
    ak.add_argument("run_id")
    ak.add_argument("--reason", default="shipped",
                    choices=["shipped", "focus", "pace", "rig", "comeback", "handoff"])
    ak.add_argument("--url", default=None, help="web app base URL")
    akls = a2sub.add_parser("acks", help="list ACKs on a grind (network)")
    akls.add_argument("run_id")
    r = sub.add_parser("v1card", help="the v1 sparkline card (kept for the bundled sample)")
    r.add_argument("session", nargs="?")
    r.add_argument("--harness", choices=["claude", "cursor"], default="claude")
    r.add_argument("--athlete", default="you")
    r.add_argument("-o", "--out", default="card.html")
    r.add_argument("--no-open", action="store_true")
    nr = sub.add_parser("nightrun", help="aggregate a multi-agent fleet run (orchestrator + lanes) into one card")
    nr.add_argument("--since", help="ISO start of the window (default: --hours ago)")
    nr.add_argument("--hours", type=float, default=12.0)
    nr.add_argument("--gap", type=int, default=30,
                    help="minutes of total idle (no human turn, no open lane) that end the run")
    nr.add_argument("--athlete", default="you")
    nr.add_argument("--title", help="card title (default: derived from the lane + repo counts)")
    nr.add_argument("-o", "--out", default="nightrun.html")
    nr.add_argument("--json", dest="as_json", action="store_true")
    nr.add_argument("--public", action="store_true",
                    help="redact repo and lane names for a card you can show a stranger "
                         "(shape and every number unchanged)")
    nr.add_argument("--no-open", action="store_true")
    au = sub.add_parser("authorship",
                        help="who wrote every type:user record in a window (the card's honest paragraph, as a table)")
    au.add_argument("--since", help="ISO start of the window (default: --hours ago)")
    au.add_argument("--hours", type=float, default=12.0)
    au.add_argument("--gap", type=int, default=30)
    pc = sub.add_parser("privacycheck",
                        help="fail if a rendered card prints a home path, a vault/.claude path, "
                             "an email, or a memory filename (the control; see agentgrinder/privacy.py)")
    pc.add_argument("paths", nargs="+", help="rendered .html cards (or any text file) to scan")
    pr = sub.add_parser("profile", help="build a builder profile + run feed from a GitHub user + local runs")
    pr.add_argument("username"); pr.add_argument("--runs", default="samples")
    pr.add_argument("-o", "--out", default="profile.html"); pr.add_argument("--no-open", action="store_true")
    args = p.parse_args(argv)

    if args.cmd == "privacycheck":
        from .privacy import check_files
        return 1 if check_files(args.paths) else 0
    if args.cmd == "flex":
        from .flex import format_flex, local_flex
        rows = local_flex()
        if args.as_json:
            print(json.dumps(rows, indent=2))
        else:
            print(format_flex(rows))
        return 0
    if args.cmd == "share":
        from .sharecard import from_run_dict, render_share_card
        from .push import DEFAULT_URL
        base = args.push_url or DEFAULT_URL
        if args.claim:
            html = render_share_card(handle=args.handle, mode="claim", base_url=base)
        elif args.profile:
            from .flex import local_flex
            rows = local_flex()
            prompts = sum(r["prompts"] for r in rows)
            mins = sum(r["moving_s"] for r in rows)
            harness = " · ".join(r["harness"] for r in rows) or None
            html = render_share_card(
                handle=args.handle,
                mode="profile",
                runs=sum(r["grinds"] for r in rows),
                prompts=prompts,
                hours=round(mins / 60, 1),
                commits=None,
                harness=harness,
                headline="Local grinds — push one to make it public.",
                base_url=base,
            )
        elif args.session:
            run = json.loads(Path(args.session).read_text())
            html = from_run_dict(run, handle=args.handle, base_url=base, vibe=args.vibe, roast=args.roast)
        else:
            run = _load_latest_run()
            if not run:
                print("no session found — try: agentgrinder share --claim"); return 1
            html = from_run_dict(run, handle=args.handle, base_url=base, vibe=args.vibe, roast=args.roast)
        out = Path(args.out)
        out.write_text(html, encoding="utf-8")
        print(f"\n  share card -> {out}")
        print("  screenshot it · the stub says claim your handle\n")
        if not args.no_open:
            webbrowser.open(out.resolve().as_uri())
        return 0
    if args.cmd == "vibe":
        from .meme import format_vibe, vibe_or_default
        run = _load_latest_run(getattr(args, "session", None))
        if not run:
            print("no session found"); return 1
        label, line = vibe_or_default(run)
        if args.as_json:
            print(json.dumps({"vibe": label, "line": line}, indent=2))
        else:
            print(format_vibe(run))
        return 0
    if args.cmd == "roast":
        from .meme import format_roast, roast_shape
        run = _load_latest_run(getattr(args, "session", None))
        if run is None:
            print("no session found"); return 1
        if args.as_json:
            print(json.dumps({"roast": roast_shape(run)}, indent=2))
        else:
            print(format_roast(run))
        return 0
    if args.cmd == "rig":
        from .flex import local_flex
        from .rigcard import render_rig_card, rig_from_local
        rig = rig_from_local()
        harnesses = [r["harness"] for r in local_flex()]
        html = render_rig_card(
            handle=args.handle,
            harnesses=harnesses,
            rig=rig,
            share_names=args.share_names,
            anonymous=args.anon,
        )
        out = Path(args.out)
        out.write_text(html, encoding="utf-8")
        print(f"\n  rig card -> {out}")
        if args.share_names and rig.get("mcp_names"):
            print(f"  MCP names on card: {', '.join(rig['mcp_names'][:8])}")
        print("  screenshot it · friends steal your stack\n")
        if not args.no_open:
            webbrowser.open(out.resolve().as_uri())
        return 0
    if args.cmd == "heist":
        from .ingest import detect_rig
        from .rigcard import render_heist_card
        rig = detect_rig()
        html = render_heist_card(
            victim_handle=args.victim.lstrip("@"),
            thief_handle=args.thief.lstrip("@"),
            rig=rig,
            harness=args.harness,
        )
        out = Path(args.out)
        out.write_text(html, encoding="utf-8")
        print(f"\n  rig heist card -> {out}\n")
        if not args.no_open:
            webbrowser.open(out.resolve().as_uri())
        return 0
    if args.cmd == "login":
        from .push import DEFAULT_URL
        base = args.url or DEFAULT_URL
        webbrowser.open(f"{base.rstrip('/')}/?onboard")
        print(f"\n  opened {base.rstrip('/')}/?onboard — sign in with GitHub\n")
        return 0
    if args.cmd == "a2a":
        from .a2a import export_grind, onboarding_text
        from .ingest import detect_rig, latest_cursor_session, latest_session, parse_cursor_session, parse_session
        if args.a2cmd == "onboard":
            print(onboarding_text())
            return 0
        if args.a2cmd == "feed":
            from .a2a_client import athlete_feed, format_feed, public_feed
            if args.handle:
                rows = athlete_feed(args.handle, args.limit)
                if not rows:
                    print(f"No public grinds for @{args.handle}.")
                    return 0
                lines = [f"# @{args.handle} — public grinds\n"]
                for r in rows:
                    mins = round((r.get("duration_s") or 0) / 60)
                    lines.append(
                        f"- {r.get('title') or r.get('project')} · {r.get('prompts')} prompts · "
                        f"{mins}m · id={r.get('id')}"
                    )
                print("\n".join(lines))
            else:
                print(format_feed(public_feed(args.limit)))
            return 0
        if args.a2cmd == "export":
            if args.harness == "cursor":
                p = latest_cursor_session()
                if not p:
                    print("no Cursor session"); return 1
                run = parse_cursor_session(p)
            else:
                p = latest_session()
                if not p:
                    print("no Claude session"); return 1
                run = parse_session(p)
            run["rig"] = detect_rig()
            print(json.dumps(export_grind(run, athlete_handle=args.handle, session_path=p), indent=2))
            return 0
        if args.a2cmd == "acks":
            from .a2a_client import format_acks, list_acks
            print(format_acks(list_acks(args.run_id)))
            return 0
        if args.a2cmd == "ack":
            from .ack import ack_url
            from .push import DEFAULT_URL
            url = ack_url(args.run_id, args.reason, args.url or DEFAULT_URL)
            print(f"\n  ACK -> {url}\n  open, sign in, confirm reason: {args.reason}\n")
            webbrowser.open(url)
            return 0
    if args.cmd in ("grind", "run"):
        return _grind(args)
    if args.cmd == "history":
        from .history import load, MEASURES
        h = load()
        print(f"\n  {len(h):,} grinds on this machine "
              f"(every sitting in ~/.claude/projects with a human turn, 30-minute idle rule)\n")
        for key, label in MEASURES:
            col = {"stretch": "stretch_s", "moving": "moving_s", "tools": "tools",
                   "edits": "edits", "prompts": "typed"}[key]
            top = sorted(h, key=lambda z: -z[col])[:args.top]
            print(f"  by {label}:")
            for i, g_ in enumerate(top[:5], 1):
                v = g_[col]
                shown = f"{v // 60}m" if col.endswith("_s") else str(v)
                print(f"    #{i:<2} {g_['at'][:16].replace('T', ' ')}  {shown:>7}  "
                      f"({g_['typed']} prompts, {g_['tools']} tool calls)")
            print()
        return 0
    if args.cmd == "v1card":
        # the pre-trace sparkline card. Kept because `demo`/`card` render the bundled sample,
        # which has no per-event data, and because the Cursor path still lands here.
        if args.harness == "cursor":
            path = args.session or latest_cursor_session()
            if not path:
                print("no Cursor session found under ~/.cursor/projects"); return 1
            run = parse_cursor_session(path, athlete=args.athlete)
        else:
            path = args.session or best_recent_session() or latest_session()
            if not path:
                print("no Claude Code session found under ~/.claude/projects"); return 1
            run = parse_session(path, athlete=args.athlete)
        _render(run, Path(args.out), not args.no_open)
        return 0
    if args.cmd == "demo":
        run = json.loads(SAMPLE.read_text())
        _render(run, Path("card.html"), not args.no_open)
    elif args.cmd == "card":
        run = json.loads(Path(args.run).read_text())
        _render(run, Path(args.out), not args.no_open)
    elif args.cmd == "profile":
        prof = build_profile(args.username, args.runs)
        out = Path(args.out); out.write_text(render_profile(prof), encoding="utf-8")
        g=prof["gh"]; t=prof["totals"]
        print(f"\n  {g.get('name')} (@{g.get('login')}) — {t['runs']} runs, {t['prompts']} prompts, {g.get('public_repos')} repos")
        print(f"  profile -> {out}\n")
        if not args.no_open:
            webbrowser.open(out.resolve().as_uri())   # module-level import (line 8); a LOCAL
            # `import webbrowser` here made the name local to all of main(), so `nightrun` at
            # line ~191 died with UnboundLocalError on every run that was not --no-open.
    elif args.cmd == "authorship":
        # The card's honest paragraph, printed as its own command so the claim is checkable
        # without opening the HTML. Same window resolution, same classifier, same numbers.
        from .authorship import CATEGORIES, LABELS
        from .fleet import collect, parse_window
        since, until = parse_window(args.since, args.hours)
        run = collect(since, until, burst_gap=args.gap)
        a = run["authorship"]
        tot = a["user_records_total"]
        print(f"\n  type:user records {run['started'][:19]} -> {run['ended'][:19]}"
              f"   ({len(run['lanes'])} lane transcripts + {len(run['sessions'])} sessions)")
        print(f"  gate: {a['gate']}\n")
        w = max(len(c) for c in CATEGORIES)
        for c in CATEGORIES:
            n = a["by_category"][c]
            print(f"  {n:>7,}  {100*n/tot if tot else 0:>5.1f}%  {c:<{w}}  {LABELS[c]}")
        print(f"  {'-'*7}")
        print(f"  {tot:>7,}  100.0%  total     every type:user record in the window")
        assert sum(a["by_category"].values()) == tot
        print(f"\n  parts sum to the total: {' + '.join(str(a['by_category'][c]) for c in CATEGORIES)}"
              f" = {tot:,}  OK")
        print(f"  keystroke check, sidechain rule OFF: {a['keystrokes_in_lane_transcripts']} of the"
              f" records in {len(run['lanes'])} lane transcripts carried promptSource typed|queued\n")
        return 0
    elif args.cmd == "nightrun":
        from .fleet import collect, parse_window
        from .fleetcard import render_fleet_card
        since, until = parse_window(args.since, args.hours)
        run = collect(since, until, athlete=args.athlete, burst_gap=args.gap)
        if args.public:
            from .fleet import redact
            run = redact(run)
        if not run["lanes"] and not run["turns_typed"]:
            print(f"\n  no agent activity between {since:%Y-%m-%d %H:%M} and {until:%H:%M}."
                  f"\n  Widen it with --hours or --since, or try   python3 -m agentgrinder demo\n")
            return 1
        if args.as_json:
            print(json.dumps(run, indent=2)); return 0
        out = Path(args.out)
        out.write_text(render_fleet_card(run, title=args.title), encoding="utf-8")
        # the population the next line names: repositories a LANE landed in, not every repo touched
        dests = {l["repo"] for l in run["lanes"] if l["repo"]}
        print(f"\n  {run['athlete']} · night run · {since:%a %d %b %H:%M} -> {until:%H:%M}")
        _a = run["authorship"]
        print(f"  {run['turns_typed']:>5} human prompts   (promptSource typed|queued, of "
              f"{_a['user_records_total']:,} type:user records; {_a['by_category']['tool_result']:,} "
              f"of those are tool results)")
        print(f"  {len(run['lanes']):>5} agent lanes     landing in {len(dests)} repos "
              f"(of {len(run['repos'])} touched)")
        print(f"  {run['tool_calls']:>5} tool calls")
        print(f"  {run['commits_verified']:>5} commits         (git log --since, window-bounded)")
        if run.get("redacted"):
            print("   redacted: repo and lane names replaced; counts and shape unchanged")
        print(f"\n  card -> {out}")
        print("  nothing was uploaded or posted; sharing it is your click\n")
        if not args.no_open:
            webbrowser.open(out.resolve().as_uri())
    return 0


def _load_latest_run(session: str | None = None) -> dict | None:
    """Latest grind dict from JSON path or local transcripts."""
    if session:
        try:
            return json.loads(Path(session).read_text())
        except (OSError, ValueError, json.JSONDecodeError):
            return None
    from .flex import latest_any
    from .solo import parse_solo, latest_grind
    from .ingest import parse_cursor_session, parse_codex_session, parse_session
    picked = latest_any()
    if not picked:
        return None
    harness, path = picked
    if harness == "cursor":
        return parse_cursor_session(path)
    if harness == "codex":
        return parse_codex_session(path)
    found = latest_grind()
    if found:
        path, pick = found
        return parse_solo(path, pick=pick)
    return parse_session(path)


def _grind(args) -> int:
    """`agentgrinder grind` — one ordinary session, the wide door.

    The verb is `grind` because the brand book names the noun (§4: Grind; "run/route/lap" are
    retired). `run` still resolves here so nothing that already works stops working.
    """
    from .solo import parse_solo, latest_grind, human_sittings
    from .solocard import render_solo_card

    if args.session and not Path(args.session).exists():
        print(f"no such transcript: {args.session}"); return 1

    harness = args.harness
    if harness == "auto" and not args.session:
        from .flex import latest_any
        picked = latest_any()
        if not picked:
            print("\n  no Claude or Cursor session found on this machine."
                  "\n  try:  python3 -m agentgrinder demo\n"); return 1
        harness, auto_path = picked
        args.session = auto_path
        print(f"  auto -> {harness} ({Path(auto_path).name})")

    if harness == "cursor":
        from .ingest import parse_cursor_session, latest_cursor_session
        from .metrics import build_activity
        from .render import render_card
        path = args.session or latest_cursor_session()
        if not path:
            print("no Cursor session under ~/.cursor/projects/*/agent-transcripts"); return 1
        run = parse_cursor_session(path, athlete=args.athlete)
        out = Path(args.out)
        out.write_text(render_card(build_activity(run)), encoding="utf-8")
        print(f"\n  Cursor transcripts carry no file paths and no commits, so the grind trace"
              f"\n  cannot be drawn for them. The v1 card is rendered instead -> {out}\n")
        if args.push:
            from .push import import_url
            from .ingest import detect_rig
            run["rig"] = detect_rig()
            if getattr(args, "share_rig_names", False):
                run["rig"]["share_names"] = True
            url = import_url(run, args.push_url)
            print(f"\n  push -> {url}\n")
            webbrowser.open(url)
            return 0
        if not args.no_open:
            webbrowser.open(out.resolve().as_uri())
        return 0

    if harness == "codex":
        from .ingest import parse_codex_session, latest_codex_session
        from .metrics import build_activity
        from .render import render_card
        path = args.session or latest_codex_session()
        if not path:
            print("no Codex session under ~/.codex/archived_sessions"); return 1
        run = parse_codex_session(path, athlete=args.athlete)
        out = Path(args.out)
        out.write_text(render_card(build_activity(run)), encoding="utf-8")
        print(f"\n  Codex rollouts carry no file-route trace yet — v1 card with real prompt/tool counts -> {out}\n")
        if args.push:
            from .push import import_url
            from .ingest import detect_rig
            run["rig"] = detect_rig()
            if getattr(args, "share_rig_names", False):
                run["rig"]["share_names"] = True
            url = import_url(run, args.push_url)
            print(f"  push -> {url}\n")
            webbrowser.open(url)
            return 0
        if not args.no_open:
            webbrowser.open(out.resolve().as_uri())
        return 0

    pick = args.pick
    if args.session:
        path = args.session
        if pick is None:
            pick = -1
    else:
        found = latest_grind()
        if not found:
            # A JUDGE WITH NO CLAUDE CODE HITS THIS FIRST. Until 31 Aug it was a dead end: one
            # sentence naming a directory, exit 1, no next step. Measured by running the whole
            # CLI with HOME pointed at an empty directory.
            print("\n  no Claude Code session with a human turn under ~/.claude/projects."
                  "\n  AGENT GRINDER only reads transcripts you already have, so there is"
                  "\n  nothing here to read. To see what a card looks like:"
                  "\n"
                  "\n      python3 -m agentgrinder demo"
                  "\n"
                  "\n  (that renders the bundled sample on the v1 card — the grind trace needs a"
                  "\n  real transcript, because every mark on it is a timestamp from one.)\n")
            return 1
        path, auto = found
        pick = auto if pick is None else pick

    if args.list:
        sits = human_sittings(path, gap=args.gap * 60)
        print(f"\n  {len(sits)} sitting{'' if len(sits) == 1 else 's'} you sat through in "
              f"{Path(path).name}   (gap {args.gap}m)\n")
        for i, s in enumerate(sits, 1):
            print(f"   --pick {i:<3} {s['start']:%a %d %b %H:%M} -> {s['end']:%H:%M}  "
                  f"{s['typed']:>3} prompts  {s['minutes']:>6.0f}m  {s['events']:>5} records")
        print()
        return 0

    try:
        run = parse_solo(path, athlete=args.athlete, pick=pick, gap=args.gap * 60,
                         show_paths=getattr(args, "show_paths", False))
    except ValueError as e:
        print(f"  {e}"); return 1
    if args.as_json:
        print(json.dumps(run, indent=2)); return 0

    ranks = None
    if not args.no_rank:
        from .history import load, rank
        ranks = rank(run, load())

    out = Path(args.out)
    out.write_text(render_solo_card(run, ranks=ranks), encoding="utf-8")

    from .solocard import headline
    t0 = run["started"][11:16]; t1 = run["ended"][11:16]
    h, _ = headline(run)
    a = run["authorship"]
    print(f"\n  {run['athlete']} · {run['project']} · {run['started'][:10]} {t0} -> {t1}"
          f"   (sitting {run['sitting']['index']} of {run['sitting']['of']})")
    print(f"  {h}\n")
    _pw = "prompt " if run['turns_typed'] == 1 else "prompts"
    print(f"  {run['turns_typed']:>5} {_pw} you typed   (promptSource typed|queued, of "
          f"{a['user_records_total']:,} type:user records)")
    print(f"  {run['tool_calls']:>5} tool calls")
    print(f"  {run['files_touched']:>5} files opened        ({run['files_edited']} changed, "
          f"{len(run['deadends'])} nothing has committed since)")
    print(f"  {run['commits']:>5} commit{'  ' if run['commits'] == 1 else 's '}            "
          f"(git log --all --name-only, during the grind)")
    if ranks and ranks.get("enough"):
        from .history import best_rank
        br = best_rank(ranks)
        print(f"\n  #{br[0]} of {br[1]:,} grinds on this machine by {br[2]}")
    print(f"\n  card -> {out}")
    if args.push:
        from .push import import_url
        from .ingest import detect_rig
        if "rig" not in run:
            run["rig"] = detect_rig()
        if getattr(args, "share_rig_names", False) and run.get("rig"):
            run["rig"]["share_names"] = True
        url = import_url(run, args.push_url)
        print(f"  push -> {url}")
        print("  sign in on the web page to publish — metrics only, nothing uploaded yet\n")
        webbrowser.open(url)
    else:
        print("  nothing was uploaded or posted; sharing it is your click\n")
        if not args.no_open:
            webbrowser.open(out.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
