"""Drive the real site against disposable PGlite: two authenticated contexts, real RPCs.

TEST DATA. No production writes. Bundled example.js is not used here.
"""
from __future__ import annotations

import base64
import json
import os
import threading
import tempfile
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from subprocess import PIPE, Popen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ["GRINDER_JOURNEY_RECEIPTS"]) if os.environ.get("GRINDER_JOURNEY_RECEIPTS") else Path(tempfile.mkdtemp(prefix="grinder-journey-"))
OUT.mkdir(parents=True, exist_ok=True)
print(f"Journey receipts: {OUT}", flush=True)
HOST = "kqxasvolwtrczusjhlli.supabase.co"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "site"), **kwargs)

    def log_message(self, fmt, *args):
        pass


def proxy(route, disposable):
    req = route.request
    if HOST not in req.url:
        return route.abort()
    target = req.url.replace("https://" + HOST, disposable).replace("http://" + HOST, disposable)
    headers = {k: v for k, v in req.headers.items() if k.lower() != "host"}
    data = req.post_data.encode() if req.post_data is not None else None
    request = urllib.request.Request(target, data=data, method=req.method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            body = resp.read()
            hdrs = {
                k: v
                for k, v in resp.headers.items()
                if k.lower() not in ("transfer-encoding", "content-encoding", "content-length")
            }
            route.fulfill(status=resp.status, headers=hdrs, body=body)
    except urllib.error.HTTPError as exc:
        body = exc.read()
        route.fulfill(status=exc.code, headers={"content-type": "application/json"}, body=body)


def insert_run(disposable, row):
    req = urllib.request.Request(
        disposable + "/_test/insert-run",
        data=json.dumps(row).encode(),
        method="POST",
        headers={"content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())["id"]


def session_script(session):
    return (
        "localStorage.setItem('sb-kqxasvolwtrczusjhlli-auth-token',"
        + json.dumps(json.dumps(session))
        + ");"
    )


def mint(sub, handle):
    header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').decode().rstrip("=")
    payload = (
        base64.urlsafe_b64encode(
            json.dumps(
                {
                    "sub": sub,
                    "email": handle + "@example.test",
                    "role": "authenticated",
                    "aud": "authenticated",
                    "exp": 2_000_000_000,
                }
            ).encode()
        )
        .decode()
        .rstrip("=")
    )
    token = f"{header}.{payload}.sig"
    user = {
        "id": sub,
        "aud": "authenticated",
        "role": "authenticated",
        "email": handle + "@example.test",
        "user_metadata": {"user_name": handle, "full_name": handle},
    }
    return {
        "access_token": token,
        "refresh_token": token,
        "token_type": "bearer",
        "expires_in": 86400,
        "expires_at": 2_000_000_000,
        "user": user,
    }


def main():
    env = os.environ.copy()
    env["GRINDER_DISPOSABLE_TEST"] = "1"
    proc = Popen(
        ["node", str(ROOT / "scripts/disposable-supabase.mjs"), "--serve"],
        cwd=str(ROOT),
        env=env,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )
    line = proc.stdout.readline()
    try:
        info = json.loads(line)
    except Exception as exc:
        err = proc.stderr.read() if proc.stderr else ""
        proc.kill()
        raise RuntimeError("disposable supabase failed to start: " + str(line) + "\n" + err) from exc
    disposable = info["url"]
    failures = []
    site = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=site.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{site.server_address[1]}"
    casey = mint(info["casey"], "test-casey")
    riley = mint(info["riley"], "test-riley")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])

            def bind(context):
                context.route("https://" + HOST + "/**", lambda route: proxy(route, disposable))
                context.route("http://" + HOST + "/**", lambda route: proxy(route, disposable))

            casey_ctx = browser.new_context(viewport={"width": 390, "height": 844})
            bind(casey_ctx)
            casey_ctx.add_init_script(session_script(casey))
            page = casey_ctx.new_page()
            page.on("pageerror", lambda e: failures.append("casey " + str(e)))
            page.goto(base + "/?run=" + info["caseyRun"], wait_until="domcontentloaded")
            page.locator("#grind-experiment").wait_for()
            assert page.locator("#grind-experiment").is_visible()
            assert not page.locator("#run-experiment").is_visible()
            page.goto(base + "/?u=test-casey", wait_until="domcontentloaded")
            page.locator(".coach-next").get_by_role("link", name="Try this next").click()
            page.wait_for_url("**next=1#grind-experiment")
            page.locator("#run-experiment").wait_for()
            page.locator("#grind-experiment").get_by_text("test_draft_renders", exact=False).first.wait_for()
            page.locator("#grind-experiment .mode-banner").first.wait_for()
            assert "not autonomous" in page.locator("#grind-experiment").inner_text().lower()
            assert "deterministic fallback" in page.locator("#grind-experiment").inner_text().lower()
            page.locator("#run-experiment input[name='title']").fill(
                "Run test_draft_renders in the same turn as the claim"
            )
            page.screenshot(path=str(OUT / "persist_casey_coach_phone.png"), full_page=True)
            page.get_by_role("button", name="Accept experiment and freeze baseline").click()
            page.wait_for_url("**/?practice=*", timeout=20000)
            page.get_by_text("Your baseline is saved", exact=False).wait_for()
            practice_id = page.url.split("practice=")[-1].split("&")[0].split("#")[0]
            assert page.locator("select[name='decision'] option[value='keep']").evaluate("option => option.disabled")
            assert "leave this attempt open" in page.locator(".review-evidence").inner_text()
            assert not page.locator("#start-attempt").is_visible()
            unlike = insert_run(disposable, {
                "profile_id": info["casey"], "title": "TEST DATA different harness later sitting",
                "harness": "Cursor", "measurement_revision": "d" * 64,
                "trace_basis": "elapsed", "prompts": 3, "claims": 2, "claims_verified": 2,
            })
            later = insert_run(
                disposable,
                {
                    "profile_id": info["casey"],
                    "title": "TEST DATA Casey later sitting",
                    "harness": "Codex",
                    "measurement_revision": "b" * 64,
                    "trace_basis": "elapsed",
                    "prompts": 3,
                    "claims": 2,
                    "claims_verified": 2,
                },
            )
            page.goto(base + "/?practice=" + practice_id, wait_until="domcontentloaded")
            page.get_by_label("Session after you started this attempt").select_option(unlike)
            assert page.locator("select[name='decision'] option[value='keep']").evaluate("option => option.disabled")
            assert "Harness differs" in page.locator(".review-evidence").inner_text()
            page.get_by_label("Session after you started this attempt").select_option(later)
            assert not page.locator("select[name='decision'] option[value='keep']").evaluate("option => option.disabled")
            page.get_by_label("Your decision").select_option("keep")
            page.get_by_label("Did you try the practice?").select_option("false")
            assert page.get_by_label("Your decision").input_value() == "incomparable"
            assert page.locator("select[name='decision'] option[value='keep']").evaluate("option => option.disabled")
            page.get_by_label("Did you try the practice?").select_option("true")
            page.get_by_label("Your decision").select_option("keep")
            page.get_by_label("What happened?").fill(
                "TEST DATA named check now has same-turn evidence. One observation, not proof of cause."
            )
            page.get_by_role("button", name="Save review").click()
            page.get_by_text("This return is recorded", exact=False).wait_for()
            page.get_by_role("heading", name="Comparable under the same measurements").wait_for()
            page.screenshot(path=str(OUT / "persist_casey_review_phone.png"), full_page=True)
            page.set_viewport_size({"width": 1280, "height": 900})
            page.screenshot(path=str(OUT / "persist_casey_review_desktop.png"), full_page=True)
            page.goto(base + "/?run=" + info["caseyRun"], wait_until="domcontentloaded")
            page.locator(".run-learning > summary").click()
            page.get_by_text("Add a moment", exact=False).click()
            page.get_by_label("Moment title").fill("TEST DATA the named check that was missing")
            page.get_by_label("What happened?").fill(
                "TEST DATA check_claim found no evidence in that turn"
            )
            page.get_by_label("Exact evidence reference").fill(
                "https://example.test/receipt/test_draft_renders"
            )
            page.get_by_label("Exact excerpt to show").fill(
                "TEST DATA: test_draft_renders had no matching snippet"
            )
            page.get_by_label("What does this NOT establish?").fill(
                "One local fixture sitting, not adoption or a real-user result"
            )
            page.get_by_label("One change for the next grind").fill(
                "Run test_draft_renders in the same turn as the claim"
            )
            page.get_by_label("I reviewed these fields").check()
            page.get_by_role("button", name="Save moment").click()
            page.get_by_role("heading", name="TEST DATA the named check that was missing").wait_for()
            page.locator("#run-audience").select_option("public")
            page.get_by_role("button", name="Save audience").click()
            page.get_by_text("public", exact=False).first.wait_for()

            riley_ctx = browser.new_context(viewport={"width": 390, "height": 844})
            bind(riley_ctx)
            riley_ctx.add_init_script(session_script(riley))
            other = riley_ctx.new_page()
            other.on("pageerror", lambda e: failures.append("riley " + str(e)))
            other.goto(base + "/?run=" + info["caseyRun"], wait_until="domcontentloaded")
            other.locator(".run-learning > summary").click()
            other.get_by_text("Keep this practice on my account", exact=False).wait_for()
            other.get_by_label("What would you look for?").fill(
                "check_claim returns verified on my own later sitting"
            )
            other.get_by_label("Keep this practice on my account").check()
            other.get_by_role("button", name="Keep this practice").click()
            other.wait_for_url("**/?practice=*", timeout=20000)
            assert info["caseyRun"] not in other.url
            other.locator(".kept-from").wait_for()
            riley_practice = other.url.split("practice=")[-1].split("&")[0].split("#")[0]
            assert riley_practice != practice_id
            riley_later = insert_run(
                disposable,
                {
                    "profile_id": info["riley"],
                    "title": "TEST DATA Riley later sitting",
                    "harness": "Codex",
                    "measurement_revision": "d" * 64,
                    "trace_basis": "elapsed",
                    "prompts": 4,
                    "claims": 2,
                    "claims_verified": 2,
                },
            )
            other.goto(base + "/?practice=" + riley_practice, wait_until="domcontentloaded")
            other.get_by_label("Session after you started this attempt").select_option(riley_later)
            other.get_by_label("Your decision").select_option("keep")
            other.get_by_label("What happened?").fill(
                "TEST DATA I ran the named check on my own baseline. Not the author counts."
            )
            other.get_by_role("button", name="Save review").click()
            other.get_by_text("This return is recorded", exact=False).wait_for()
            other.get_by_role("heading", name="Comparable under the same measurements").wait_for()
            other.get_by_role("button", name="Share my outcome").wait_for()
            other.screenshot(path=str(OUT / "persist_riley_return_phone.png"), full_page=True)
            other.set_viewport_size({"width": 1280, "height": 900})
            other.screenshot(path=str(OUT / "persist_riley_return_desktop.png"), full_page=True)

            page.set_viewport_size({"width": 390, "height": 844})
            page.goto(base + "/?run=" + info["caseyRun"], wait_until="domcontentloaded")
            page.locator("#run-audience").select_option("private")
            page.get_by_role("button", name="Save audience").click()
            other.set_viewport_size({"width": 390, "height": 844})
            other.goto(base + "/?practice=" + riley_practice, wait_until="domcontentloaded")
            other.get_by_text("no longer readable", exact=False).wait_for()
            other.get_by_text("This return is recorded", exact=False).wait_for()
            other.screenshot(path=str(OUT / "persist_riley_after_revoke_phone.png"), full_page=True)
            other.goto(base + "/?run=" + info["caseyRun"], wait_until="domcontentloaded")
            other.get_by_text("private or does not exist", exact=False).wait_for()
            assert not failures, failures
            receipt = {
                "fixture": True,
                "label": "TEST DATA · disposable PGlite · not live users",
                "casey_practice": practice_id,
                "riley_practice": riley_practice,
                "revocation_preserved_owned_work": True,
            }
            (OUT / "persist_journey_receipt.json").write_text(json.dumps(receipt, indent=2))
            print("persisted UI journey ok", receipt)
            browser.close()
    finally:
        site.shutdown()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
