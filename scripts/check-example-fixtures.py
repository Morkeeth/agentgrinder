"""Bundled example UI journey. Labelled fixture. No hosted database."""
import json
import os
import re
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get("GRINDER_EXAMPLE_RECEIPTS", "/tmp/grinder-example-fixtures"))
OUT.mkdir(parents=True, exist_ok=True)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "site"), **kwargs)

    def log_message(self, fmt, *args):
        pass


def main():
    data = json.loads((ROOT / "site/bundled-example.json").read_text())
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"
    failures = []
    mock = """
    window.supabase = { createClient() {
      const q = {
        select(){return q;}, eq(){return q;}, order(){return q;}, limit(){return q;},
        maybeSingle: async () => ({ data: null }),
        single: async () => ({ data: null, error: { code: 'PGRST116' } }),
        then(resolve){ return Promise.resolve({ data: [] }).then(resolve); }
      };
      return {
        auth: {
          async getSession(){ return { data: { session: null } }; },
          onAuthStateChange(){ return { data: { subscription: { unsubscribe(){} } } }; },
          async signInWithOAuth(){ return { error: null }; },
          async signOut(){ return {}; }
        },
        from(){ return q; }
      };
    } };
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 390, "height": 844})
        context.add_init_script(mock)
        context.route("**/cdn.jsdelivr.net/npm/@supabase/**", lambda route: route.fulfill(
            status=200, content_type="application/javascript",
            body="/* fixture stub */",
        ))
        context.route("**/*supabase.co**", lambda route: route.fulfill(status=204, body=""))
        page = context.new_page()
        page.on("pageerror", lambda e: failures.append(str(e)))
        page.goto(base + "/?example", wait_until="domcontentloaded")
        page.add_style_tag(
            content="#fixture-banner{position:sticky;top:0;z-index:9;padding:8px;background:#fff3bb}"
        )
        page.evaluate(
            """() => {
              if (document.getElementById('fixture-banner')) return;
              const b = document.createElement('div');
              b.id = 'fixture-banner';
              b.textContent = 'UI TEST FIXTURE — bundled public-safe example · not live users';
              document.body.prepend(b);
            }"""
        )
        page.get_by_text("Deterministic demo", exact=False).wait_for()
        page.get_by_text("test_draft_renders", exact=False).wait_for()
        page.get_by_text("not autonomous reasoning", exact=False).wait_for()
        page.get_by_role("button", name="Freeze this fixture as my baseline").wait_for()
        assert page.get_by_text("BUNDLED EXAMPLE", exact=False).count() >= 1
        page.get_by_role("button", name="Freeze this fixture as my baseline").click()
        page.get_by_text("BASELINE FROZEN", exact=False).wait_for()
        page.get_by_role("button", name="Return with the later labelled sitting").click()
        page.get_by_label("One useful observed outcome").fill(
            "TEST DATA: named test now has same-turn evidence. Not proof of cause."
        )
        page.get_by_role("button", name="Save this review").click()
        page.get_by_text("Your decision: keep", exact=False).wait_for()
        page.get_by_label("I reviewed these fields").check()
        page.get_by_role("button", name="Save moment on this fixture").click()
        page.get_by_role("button", name="Open as another builder (fixture role)").click()
        page.get_by_label("Keep this practice on my fixture account").check()
        page.get_by_role("button", name="Keep this practice").click()
        page.get_by_role("button", name="Return with your own later fixture").click()
        page.get_by_label("Your observed outcome").fill(
            "TEST DATA: I ran the named check on my own baseline."
        )
        page.get_by_role("button", name="Save my outcome").click()
        page.get_by_text("Second builder decision: keep", exact=False).wait_for()
        assert "not proof" in page.content().lower() or "not shown" in page.content().lower()
        assert not page.evaluate("document.documentElement.scrollWidth>innerWidth")
        page.screenshot(path=str(OUT / "example-phone.png"), full_page=True)
        page.set_viewport_size({"width": 1280, "height": 900})
        assert not page.evaluate("document.documentElement.scrollWidth>innerWidth")
        page.screenshot(path=str(OUT / "example-desktop.png"), full_page=True)
        page.goto(base + "/", wait_until="domcontentloaded")
        page.get_by_role("button", name="Try the bundled example").wait_for()
        page.get_by_text("I tried this. Show me what changed.", exact=False).wait_for()
        page.screenshot(path=str(OUT / "landing-phone.png"), full_page=True)
        assert not failures, failures
        assert data["fixture"] is True
        print("example fixture ok", OUT)


if __name__ == "__main__":
    main()
