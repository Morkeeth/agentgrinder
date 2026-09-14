"""Signed-in router journey with explicit UI fixtures — not empty nav chrome.

Serves candidate site/, mocks Supabase client, exercises real route() for
My runs / Progress / Practices / Community / Forum / Crews / Challenges / Inbox
at 390 and 1280. Labels every surface UI TEST FIXTURE. No hosted writes.
"""
from __future__ import annotations

import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = Path.home() / ".local/state/day-run/2026-09-11/grinder-evidence/final-30-min"
OWNER = "10000000-0000-0000-0000-000000000001"
RUN_A = "20000000-0000-0000-0000-000000000004"
RUN_B = "20000000-0000-0000-0000-000000000005"
PRACTICE = "40000000-0000-0000-0000-000000000004"
ATTEMPT = "50000000-0000-0000-0000-000000000004"
NOTE = "60000000-0000-0000-0000-000000000001"
CREW = "70000000-0000-0000-0000-000000000001"
CHALLENGE = "80000000-0000-0000-0000-000000000001"
THREAD = "90000000-0000-0000-0000-000000000001"

MOCK_SUPABASE = r"""
window.supabase = {
  createClient() {
    const owner = %OWNER%;
    const profile = {
      id: owner,
      auth_uid: "auth-fixture-owner",
      github_handle: "fixture-builder",
      name: "Fixture Builder",
      rig: {},
    };
    const tables = {
      profiles: [profile, {id: "actor-1", github_handle: "fixture-peer", name: "Fixture Peer", rig: {}}],
      runs: [
        {
          id: %RUN_A%,
          profile_id: owner,
          title: "Fixture earlier run",
          harness: "Codex",
          visibility: "private",
          schema_version: 1,
          measurement_revision: "e".repeat(64),
          trace_basis: "elapsed",
          started_at: "2026-09-01T10:00:00Z",
          created_at: "2026-09-01T10:00:00Z",
          prompts: 3,
          artifacts_produced: 1,
          rhythm: [3, 1, 2, 1],
          claims_verified: 1,
        },
        {
          id: %RUN_B%,
          profile_id: owner,
          title: "Fixture later run",
          harness: "Codex",
          visibility: "private",
          schema_version: 1,
          measurement_revision: "f".repeat(64),
          trace_basis: "elapsed",
          started_at: "2026-09-02T10:00:00Z",
          created_at: "2026-09-02T10:00:00Z",
          prompts: 4,
          artifacts_produced: 2,
          rhythm: [1, 2, 1, 4],
          claims_verified: 2,
        },
        {
          id: "20000000-0000-0000-0000-000000000099",
          profile_id: "someone-else",
          title: "Public fixture grind",
          harness: "Cursor",
          visibility: "public",
          created_at: "2026-09-03T10:00:00Z",
          prompts: 2,
          artifacts_produced: 3,
          rhythm: [1, 1],
          measurement_revision: "a".repeat(64),
        },
      ],
      grinder_practice_versions: [
        {
          id: %PRACTICE%,
          owner_id: owner,
          title: "Run the named fixture check",
          instruction: "Run the named fixture check",
          task_context: "Two fixture bug fixes",
          expected: "A result in the completion turn",
          visibility: "private",
          harness: "Codex",
        },
      ],
      grinder_practice_attempts: [
        {
          id: %ATTEMPT%,
          practice_id: %PRACTICE%,
          owner_id: owner,
          created_at: "2026-09-02T12:00:00Z",
          visibility: "private",
          reviewed_at: null,
          practice: {title: "Run the named fixture check", instruction: "Run the named fixture check"},
          baseline: {turns_typed: 4, artifacts_produced: 2, measurement_revision: "f".repeat(64)},
        },
      ],
      grinder_notifications: [
        {
          id: %NOTE%,
          recipient_id: owner,
          actor_id: "actor-1",
          kind: "ack",
          run_id: %RUN_B%,
          created_at: "2026-09-03T09:00:00Z",
          read_at: null,
          actor: {github_handle: "fixture-peer", name: "Fixture Peer"},
        },
      ],
      grinder_comparisons: [],
      grinder_memberships: [
        {profile_id: owner, crew: {id: %CREW%, name: "Fixture Crew", description: "UI TEST FIXTURE crew", visibility: "private"}},
      ],
      grinder_crews: [
        {id: %CREW%, name: "Fixture Crew", description: "UI TEST FIXTURE crew", visibility: "private", owner_id: owner},
      ],
      grinder_challenges: [
        {
          id: %CHALLENGE%,
          owner_id: owner,
          name: "OCTACON UI fixture",
          kind: "octacon",
          capacity: 8,
          closes_at: "2030-01-01T00:00:00Z",
          contract: {task: "One declared fixture task", checks: ["Run the fixture check"]},
        },
      ],
      grinder_challenge_entries: [
        {id: "entry-a", owner_id: owner, challenge_id: %CHALLENGE%, crew_name: "Fixture Crew A", rig_revision: "rig-a"},
      ],
      grinder_challenge_submissions: [],
      grinder_forum_threads: [
        {
          id: %THREAD%,
          title: "Fixture forum thread",
          body: "UI TEST FIXTURE forum body with a real question.",
          created_at: "2026-09-03T08:00:00Z",
          author_id: owner,
        },
      ],
      grinder_replies: [
        {
          id: "reply-1",
          run_id: "20000000-0000-0000-0000-000000000099",
          body: "Run the import check before editing.",
          created_at: "2026-09-04T12:00:00Z",
        },
      ],
      acks: [],
    };

    function matchJoin(row, select) {
      if (!select || !select.includes(":")) return row;
      const out = {...row};
      if (select.includes("practice:grinder_practice_versions")) {
        out.practice = tables.grinder_practice_versions.find((p) => p.id === row.practice_id) || row.practice;
      }
      if (select.includes("actor:profiles")) {
        out.actor = tables.profiles.find((p) => p.id === row.actor_id) || row.actor;
      }
      if (select.includes("crew:grinder_crews")) {
        out.crew = row.crew || tables.grinder_crews[0];
      }
      if (select.includes("profiles!")) {
        out.profiles = tables.profiles.find((p) => p.id === row.profile_id) || profile;
      }
      return out;
    }

    function from(name) {
      let filters = [];
      let start = 0;
      let end = 100;
      let selectCols = "*";
      let verb = "read";
      let payload = null;
      let countOnly = false;
      const q = {
        select(cols, opts) {
          selectCols = cols || "*";
          if (opts && opts.count === "exact" && opts.head) countOnly = true;
          return q;
        },
        eq(k, v) {
          filters.push((r) => (r[k] ?? null) === v);
          return q;
        },
        is(k, v) {
          filters.push((r) => (r[k] ?? null) === v);
          return q;
        },
        not(k, op, v) {
          filters.push((r) => (r[k] ?? null) !== v);
          return q;
        },
        in(k, values) {
          filters.push((r) => values.includes(r[k]));
          return q;
        },
        ilike(k, v) {
          const needle = String(v).replace(/^%/, "").replace(/%$/, "").toLowerCase();
          filters.push((r) => String(r[k] ?? "").toLowerCase().includes(needle));
          return q;
        },
        order() {
          return q;
        },
        range(a, b) {
          start = a;
          end = b + 1;
          return q;
        },
        limit(n) {
          end = n;
          return q;
        },
        maybeSingle() {
          return q.then((res) => ({
            data: (res.data && res.data[0]) || null,
            error: res.error,
          }));
        },
        single() {
          return q.then((res) => ({
            data: (res.data && res.data[0]) || null,
            error: res.error || (!(res.data && res.data[0]) ? {message: "not found"} : null),
          }));
        },
        insert(v) {
          verb = "insert";
          payload = v;
          return q;
        },
        update(v) {
          verb = "update";
          payload = v;
          return q;
        },
        delete() {
          verb = "delete";
          return q;
        },
        then(resolve, reject) {
          let rows = tables[name] || [];
          if (verb === "insert") {
            const row = Array.isArray(payload) ? payload[0] : payload;
            const saved = {id: "inserted-fixture", ...row};
            rows = [...rows, saved];
            tables[name] = rows;
            return Promise.resolve({data: [saved], error: null}).then(resolve, reject);
          }
          if (verb === "update") {
            rows = rows.map((r) => (filters.every((f) => f(r)) ? {...r, ...payload} : r));
            tables[name] = rows;
            return Promise.resolve({data: rows.filter((r) => filters.every((f) => f(r))), error: null}).then(
              resolve,
              reject,
            );
          }
          const filtered = rows.filter((r) => filters.every((f) => f(r))).map((r) => matchJoin(r, selectCols));
          if (countOnly) return Promise.resolve({count: filtered.length, data: null, error: null}).then(resolve, reject);
          return Promise.resolve({data: filtered.slice(start, end), error: null}).then(resolve, reject);
        },
      };
      return q;
    }

    async function rpc(name, payload) {
      if (name === "grinder_save_comparison") {
        const id = "30000000-0000-0000-0000-000000000004";
        const before = {...tables.runs.find((r) => r.id === payload.earlier), turns_typed: 3};
        const after = {...tables.runs.find((r) => r.id === payload.later), turns_typed: 4};
        tables.grinder_comparisons.push({
          id,
          owner_id: owner,
          task_context: payload.context_text,
          created_at: "2026-09-02T11:00:00Z",
          before_run: before,
          after_run: after,
          limitations: [],
          next_practice: null,
        });
        return {data: id, error: null};
      }
      return {data: null, error: null};
    }

    const auth = {
      async getSession() {
        return {
          data: {
            session: {
              user: {id: "auth-fixture-owner", user_metadata: {user_name: "fixture-builder", full_name: "Fixture Builder"}},
            },
          },
          error: null,
        };
      },
      onAuthStateChange() {
        return {data: {subscription: {unsubscribe() {}}}};
      },
      async signOut() {
        return {error: null};
      },
      async signInWithOAuth() {
        return {error: null};
      },
      async signInWithOtp() {
        return {error: null};
      },
    };

    return {from, rpc, auth};
  },
};
"""


def _quote(value: str) -> str:
    return json.dumps(value)


def build_mock() -> str:
    return (
        MOCK_SUPABASE.replace("%OWNER%", _quote(OWNER))
        .replace("%RUN_A%", _quote(RUN_A))
        .replace("%RUN_B%", _quote(RUN_B))
        .replace("%PRACTICE%", _quote(PRACTICE))
        .replace("%ATTEMPT%", _quote(ATTEMPT))
        .replace("%NOTE%", _quote(NOTE))
        .replace("%CREW%", _quote(CREW))
        .replace("%CHALLENGE%", _quote(CHALLENGE))
        .replace("%THREAD%", _quote(THREAD))
    )


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "site"), **kwargs)

    def log_message(self, fmt, *args):
        pass


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    mock = build_mock()
    assertions: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []

        def attach_banner(pg):
            pg.evaluate(
                """() => {
              if (document.getElementById('fixture-banner')) return;
              const b = document.createElement('div');
              b.id = 'fixture-banner';
              b.textContent = 'UI TEST FIXTURE — controlled local data · not production · not live users';
              b.style.cssText = 'position:sticky;top:0;z-index:99;padding:8px 12px;background:#fff3bb;border-bottom:1px solid #c9b458;font:12px/1.3 system-ui';
              document.body.prepend(b);
            }"""
            )

        context = browser.new_context(viewport={"width": 1280, "height": 900})
        context.add_init_script(mock)
        context.route("**/*supabase*", lambda route: route.fulfill(status=204, body=""))
        context.route(
            "**/cdn.jsdelivr.net/npm/@supabase/**",
            lambda route: route.fulfill(
                status=200,
                content_type="application/javascript",
                body="/* fixture stub — createClient provided by init script */",
            ),
        )
        page = context.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))

        routes = [
            ("mine", "/?mine", ["Fixture earlier run", "Fixture later run", "My runs"]),
            ("progress", "/?progress", ["Progress", "Save private comparison", "Fixture earlier run"]),
            ("practices", "/?practices", ["A practice worth trying", "Run the named fixture check"]),
            ("practice", f"/?practice={PRACTICE}", ["Run the named fixture check"]),
            ("community", "/?community", ["Community", "Forum", "Crews", "Challenges"]),
            ("forum", "/?forum", ["The forum", "Public fixture grind"]),
            ("crews", "/?crews", ["Fixture Crew", "Crews"]),
            ("challenges", "/?challenges", ["OCTACON UI fixture", "Challenges"]),
            ("inbox", "/?inbox", ["Your inbox", "ACKed your work"]),
            ("following", "/?following", ["Your following feed", "Follow a builder"]),
        ]

        for name, path, needles in routes:
            for width, height, suffix in ((1280, 900, "desktop"), (390, 844, "phone")):
                page.set_viewport_size({"width": width, "height": height})
                page.goto(base + path, wait_until="domcontentloaded")
                page.wait_for_timeout(400)
                attach_banner(page)
                body = page.locator("#app").inner_text()
                nav_desk = page.evaluate(
                    """() => [...document.querySelectorAll('#nav > a')].filter(a=>a.offsetParent).map(a=>a.textContent.replace(/\\s+/g,' ').trim())"""
                )
                nav_mob = page.evaluate(
                    """() => [...document.querySelectorAll('#mobile-product-nav a')].filter(a=>a.offsetParent).map(a=>a.textContent.replace(/\\s+/g,' ').trim())"""
                )
                overflow = page.evaluate("document.documentElement.scrollWidth>innerWidth+1")
                missing = [n for n in needles if n not in body and n not in page.content()]
                # Practices index may be empty-state but still must not be blank shell
                populated = len(body.strip()) > 40 and "Loading…" not in body
                shot = OUT / f"app-{name}-{suffix}.png"
                page.screenshot(path=str(shot), full_page=False)
                assertions.append(
                    {
                        "route": path,
                        "viewport": f"{width}x{height}",
                        "shot": str(shot),
                        "nav_desk": nav_desk,
                        "nav_mob": nav_mob,
                        "overflow": overflow,
                        "populated": populated,
                        "missing_needles": missing,
                        "body_preview": body[:240].replace("\n", " | "),
                    }
                )

        # Deep-link smoke: old URLs still resolve to labeled sections
        for path in ("/?following", "/?forum", "/?crews", "/?challenges", "/?agents", "/?rigs", "/?practices", "/?progress"):
            page.goto(base + path, wait_until="domcontentloaded")
            page.wait_for_timeout(250)
            assert page.locator("#app").inner_text().strip(), f"empty body for {path}"

        browser.close()
    server.shutdown()

    failed = [a for a in assertions if (not a["populated"]) or a["overflow"] or a["missing_needles"]]
    (OUT / "assertions.json").write_text(json.dumps({"assertions": assertions, "page_errors": errors, "failed": failed}, indent=2))
    print(json.dumps({"ok": not failed and not errors, "shots": len(assertions), "failed": len(failed), "errors": errors[:5]}, indent=2))
    if failed or errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
