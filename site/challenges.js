window.GrinderChallenges = function ({ client: db, me, app, frame, status }) {
  const esc = (x) =>
    String(x ?? "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const $ = (id) => document.getElementById(id);
  const nav =
    '<nav class="social-nav"><a href="/?crews">Crews</a><a href="/?rigs">Rigs</a><a href="/?challenges">Challenges</a><a href="/?agents">Agents</a></nav>';
  async function data(query) {
    const r = await query;
    if (r.error) throw new Error(r.error.message);
    return r.data || [];
  }
  function start(title) {
    frame(null, null);
    app().innerHTML =
      nav +
      `<div class="head"><h2>${esc(title)}</h2></div><div id="challenge-body" aria-live="polite">Loading…</div>`;
  }
  function fail(e) {
    status(GrinderContract.message(e), true);
  }
  function action(form, callback) {
    form.onsubmit = async (e) => {
      e.preventDefault();
      const b = form.querySelector("button[type=submit],button:not([type])");
      b.disabled = true;
      try {
        await callback(form);
      } catch (error) {
        fail(error);
      } finally {
        b.disabled = false;
      }
    };
  }
  async function ownCrews() {
    return me()
      ? data(db.from("grinder_crews").select("id,name").eq("owner_id", me().id))
      : [];
  }
  async function ownRigs() {
    return me()
      ? data(
          db
            .from("grinder_rig_revisions")
            .select("id,label")
            .eq("owner_id", me().id)
            .eq("visibility", "public"),
        )
      : [];
  }
  const options = (items, key) =>
    items
      .map((r) => `<option value="${r.id}">${esc(r[key])}</option>`)
      .join("");

  async function rigs() {
    start("Show your Rig");
    try {
      const rows = await data(
        db
          .from("grinder_rig_revisions")
          .select(
            "*,owner:profiles!grinder_rig_revisions_owner_id_fkey(github_handle,name)",
          )
          .order("created_at", { ascending: false })
          .limit(50),
      );
      $("challenge-body").innerHTML =
        "<p>A saved Rig is a version you can name, share and lock for a Challenge. Downloading it does not change your agent settings.</p>" +
        rows
          .map(
            (r) =>
              `<article class="card"><h3><a href="/?rigversion=${r.id}">${esc(r.label)}</a></h3><p>${esc(r.owner?.name || r.owner?.github_handle || "A grinder")} · ${esc(r.visibility)}</p><small>${esc(new Date(r.created_at).toLocaleString())}</small></article>`,
          )
          .join("") +
        (me()
          ? '<form id="save-rig" class="panel reply-form"><h3>Save a Rig version</h3><label>Name<input name="label" required maxlength="100"></label><label>Harnesses, comma separated<input name="harnesses" placeholder="Claude Code, Cursor"></label><label>Model<input name="model" maxlength="100"></label><label>MCP names, comma separated<input name="mcps"></label><label>Skill names, comma separated<input name="skills"></label><label>Setup notes · never credentials<textarea name="notes" maxlength="2000"></textarea></label><label>Visibility<select name="visibility"><option value="private">Private</option><option value="public">Public · needed for a Challenge entry</option></select></label><button>Save version</button></form>'
          : "<p>Sign in to save your Rig.</p>");
      if (me())
        action($("save-rig"), async (form) => {
          const split = (name) =>
            form.elements[name].value
              .split(",")
              .map((x) => x.trim())
              .filter(Boolean);
          const manifest = {
            harnesses: split("harnesses"),
            model: form.elements.model.value,
            mcps: split("mcps"),
            skills: split("skills"),
            notes: form.elements.notes.value,
          };
          await data(
            db
              .from("grinder_rig_revisions")
              .insert({
                owner_id: me().id,
                label: form.elements.label.value,
                visibility: form.elements.visibility.value,
                manifest,
              }),
          );
          await rigs();
        });
    } catch (e) {
      $("challenge-body").textContent = "Rigs could not load.";
      fail(e);
    }
  }

  async function rig(id) {
    start("Rig version");
    try {
      const rows = await data(
        db.from("grinder_rig_revisions").select("*").eq("id", id),
      );
      const r = rows[0];
      if (!r) {
        $("challenge-body").textContent = "This Rig is private or unavailable.";
        return;
      }
      const m = r.manifest || {};
      $("challenge-body").innerHTML =
        `<article class="card"><h2>${esc(r.label)}</h2><p>Saved ${esc(new Date(r.created_at).toLocaleString())}. This version does not change when its owner changes their current setup.</p><dl>${["harnesses", "model", "mcps", "skills", "notes"].map((k) => `<dt>${esc(k)}</dt><dd>${esc(Array.isArray(m[k]) ? m[k].join(", ") : m[k] || "Not supplied")}</dd>`).join("")}</dl><button id="download-rig">Download Rig manifest</button><p>Run <code>agentgrinder rig-config preview FILE</code> to see the changes, then <code>agentgrinder rig-config import FILE</code> to select it in Grinder. Use <code>rig-config revert REVISION</code> to restore a saved version. This changes your declared Grinder Rig; your agent settings stay unchanged.</p></article>`;
      $("download-rig").onclick = () => {
        const manifest = {
          schema_version: 1,
          rig_revision: r.id,
          label: r.label,
          manifest: r.manifest,
        };
        const url = URL.createObjectURL(
          new Blob([JSON.stringify(manifest, null, 2)], {
            type: "application/json",
          }),
        );
        const a = document.createElement("a");
        a.href = url;
        a.download = "grinder-rig-" + r.id + ".json";
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      };
    } catch (e) {
      $("challenge-body").textContent = "This Rig could not load.";
      fail(e);
    }
  }

  async function index() {
    start("Challenges");
    try {
      const rows = await data(
        db
          .from("grinder_challenges")
          .select("*")
          .order("created_at", { ascending: false })
          .limit(50),
      );
      const crews = await ownCrews();
      $("challenge-body").innerHTML =
        "<p>One task Contract. A locked Rig. Real grinds and visible organiser reviews. OCTACON brings eight Crews to the same task.</p>" +
        rows
          .map(
            (c) =>
              `<article class="card"><small>${esc(c.kind === "octacon" ? "OCTACON" : "Challenge")}</small><h3><a href="/?challenge=${c.id}">${esc(c.name)}</a></h3><p>${esc(c.contract.task)}</p><small>${c.capacity} places · closes ${esc(new Date(c.closes_at).toLocaleString())}</small></article>`,
          )
          .join("") +
        (crews.length
          ? `<form id="create-challenge" class="panel reply-form"><h3>Host a Challenge</h3><label>Your host Crew<select name="crew">${options(crews, "name")}</select></label><label>Name<input name="title" required maxlength="120"></label><label>Format<select name="format"><option value="challenge">Challenge</option><option value="octacon">OCTACON · eight Crews</option></select></label><label>Task<textarea name="task" required maxlength="4000"></textarea></label><label>Required checks · one per line<textarea name="checks" required maxlength="8000"></textarea></label><label>Closes at · your local time<input type="datetime-local" name="closes" required></label><p>The Contract and entries are public. Reviews are made by the organiser and remain in the history.</p><button>Create public Challenge</button></form>`
          : '<p>Own a Crew to host a Challenge. <a href="/?crews">Open Crews</a>.</p>');
      if (crews.length)
        action($("create-challenge"), async (form) => {
          const id = await data(
            db.rpc("grinder_create_challenge", {
              crew: form.elements.crew.value,
              title: form.elements.title.value,
              task_contract: {
                task: form.elements.task.value,
                checks: form.elements.checks.value
                  .split("\n")
                  .map((s) => s.trim())
                  .filter(Boolean),
              },
              closes: new Date(form.elements.closes.value).toISOString(),
              format: form.elements.format.value,
              places: 8,
            }),
          );
          location.href = "/?challenge=" + id;
        });
    } catch (e) {
      $("challenge-body").textContent = "Challenges could not load.";
      fail(e);
    }
  }

  function octaconBoard(event, entries, submissions) {
    if (event.kind !== "octacon") return "";
    const cells = entries.map((entry) => {
      const last = submissions.find((s) => s.entry_id === entry.id);
      return `<article class="octacon-place"><strong>${esc(entry.crew_name)}</strong>${last ? GrinderContract.trace(last.snapshot) : "<p>Awaiting a grind</p>"}<small>${last ? "Submitted rhythm · " + esc(last.snapshot.trace_basis || "timing not specified") : "Rig locked"}</small></article>`;
    });
    while (cells.length < 8)
      cells.push(
        '<div class="octacon-place open"><span>Open place</span></div>',
      );
    return (
      '<section aria-label="OCTACON places"><h3>' +
      entries.length +
      ' of 8 Crews entered</h3><div class="octacon-board">' +
      cells.join("") +
      "</div></section>"
    );
  }
  async function show(id) {
    start("Challenge");
    try {
      const events = await data(
        db.from("grinder_challenges").select("*").eq("id", id),
      );
      const c = events[0];
      if (!c) {
        $("challenge-body").textContent = "This Challenge is unavailable.";
        return;
      }
      const entries = await data(
        db
          .from("grinder_challenge_entries")
          .select("*")
          .eq("challenge_id", id)
          .order("created_at"),
      );
      const submissions = entries.length
        ? await data(
            db
              .from("grinder_challenge_submissions")
              .select("*")
              .in(
                "entry_id",
                entries.map((e) => e.id),
              )
              .order("created_at", { ascending: false }),
          )
        : [];
      const reviews = submissions.length
        ? await data(
            db
              .from("grinder_challenge_reviews")
              .select("*")
              .in(
                "submission_id",
                submissions.map((s) => s.id),
              )
              .order("created_at", { ascending: false }),
          )
        : [];
      const appeals = reviews.length
        ? await data(
            db
              .from("grinder_challenge_appeals")
              .select("*")
              .in(
                "review_id",
                reviews.map((r) => r.id),
              ),
          )
        : [];
      const crews = await ownCrews(),
        rigs = await ownRigs(),
        mine = entries.filter((e) => e.owner_id === me()?.id),
        open = new Date(c.closes_at) > new Date();
      const runs = mine.length
        ? await data(
            db
              .from("runs")
              .select("id,title,measurement_revision")
              .eq("profile_id", me().id)
              .eq("visibility", "public")
              .not("measurement_revision", "is", null)
              .order("created_at", { ascending: false })
              .limit(50),
          )
        : [];
      $("challenge-body").innerHTML =
        `<article class="card"><small>${esc(c.kind === "octacon" ? "OCTACON" : "Challenge")}</small><h2>${esc(c.name)}</h2><p>${esc(c.contract.task)}</p><ol>${(c.contract.checks || []).map((check) => `<li>${esc(check)}</li>`).join("")}</ol><p>${entries.length} of ${c.capacity} Crews entered · ${open ? "closes" : "closed"} ${esc(new Date(c.closes_at).toLocaleString())}</p><small>This Contract is fixed. A changed task needs a new Challenge.</small></article>` +
        octaconBoard(c, entries, submissions) +
        (open && crews.length && rigs.length
          ? `<form id="enter-challenge" class="panel reply-form"><h3>Enter your Crew</h3><label>Crew<select name="crew">${options(crews, "name")}</select></label><label>Lock this public Rig<select name="rig">${options(rigs, "label")}</select></label><p>Your Crew name and selected Rig become part of the public entry.</p><button>Enter and lock Rig</button></form>`
          : open && me()
            ? '<p>To enter, own a Crew and <a href="/?rigs">save a public Rig version</a>.</p>'
            : "") +
        entries
          .map(
            (e) =>
              `<article class="card"><h3>${esc(e.crew_name)}</h3><a href="/?rigversion=${e.rig_revision}">Locked Rig</a><p>${submissions.some((s) => s.entry_id === e.id) ? "Submitted" : "Awaiting a grind"}</p></article>`,
          )
          .join("") +
        (open && mine.length && runs.length
          ? `<form id="submit-challenge" class="panel reply-form"><label>Your entry<select name="entry">${options(mine, "crew_name")}</select></label><label>Public grind with a measurement<select name="grind">${options(runs, "title")}</select></label><p>A snapshot of its counts and measurement reference will remain in the event history.</p><button>Submit grind</button></form>`
          : "") +
        '<div class="head"><h2>Submissions and reviews</h2></div>' +
        submissions
          .map((s) => {
            const team = entries.find((e) => e.id === s.entry_id);
            const history = reviews.filter((r) => r.submission_id === s.id);
            return `<article class="card"><h3>${esc(team?.crew_name)}</h3><p>${esc(s.snapshot.title || "Submitted grind")}</p><a href="/?run=${s.run_id}">Open source grind</a><p>Measurement ${esc(s.measurement_revision.slice(0, 12))} · client-reported snapshot</p>${
              history
                .map(
                  (r) =>
                    `<div class="review-history"><b>${esc(r.verdict)} · organiser review</b><p>${esc(r.evidence)}</p>${r.supersedes ? "<small>Revises an earlier review; both remain visible.</small>" : ""}${appeals
                      .filter((a) => a.review_id === r.id)
                      .map((a) => `<p>Entrant appeal: ${esc(a.body)}</p>`)
                      .join(
                        "",
                      )}${team?.owner_id === me()?.id ? `<form data-appeal="${r.id}" class="reply-form"><label>Appeal this review<textarea name="reason" required maxlength="4000"></textarea></label><button>Post public appeal</button></form>` : ""}</div>`,
                )
                .join("") || "<p>Awaiting organiser review.</p>"
            }${c.owner_id === me()?.id ? `<form data-review="${s.id}" data-previous="${history[0]?.id || ""}" class="reply-form"><label>Decision<select name="decision"><option value="accepted">Accepted</option><option value="rejected">Rejected</option></select></label><label>Checks and evidence for this decision<textarea name="reason" required maxlength="4000"></textarea></label><button>Record organiser review</button></form>` : ""}</article>`;
          })
          .join("");
      if ($("enter-challenge"))
        action($("enter-challenge"), async (form) => {
          await data(
            db.rpc("grinder_enter_challenge", {
              challenge: id,
              crew: form.elements.crew.value,
              rig: form.elements.rig.value,
            }),
          );
          await show(id);
        });
      if ($("submit-challenge"))
        action($("submit-challenge"), async (form) => {
          await data(
            db.rpc("grinder_submit_challenge", {
              entry: form.elements.entry.value,
              grind: form.elements.grind.value,
            }),
          );
          await show(id);
        });
      document.querySelectorAll("[data-review]").forEach((form) =>
        action(form, async (f) => {
          await data(
            db.rpc("grinder_review_submission", {
              submission: f.dataset.review,
              decision: f.elements.decision.value,
              reason: f.elements.reason.value,
              previous_review: f.dataset.previous || null,
            }),
          );
          await show(id);
        }),
      );
      document.querySelectorAll("[data-appeal]").forEach((form) =>
        action(form, async (f) => {
          await data(
            db.rpc("grinder_appeal_review", {
              review: f.dataset.appeal,
              reason: f.elements.reason.value,
            }),
          );
          await show(id);
        }),
      );
    } catch (e) {
      $("challenge-body").textContent = "This Challenge could not load.";
      fail(e);
    }
  }
  async function declareRig(run, slot) {
    if (!slot || !me() || run.profile_id !== me().id) return;
    try {
      const choices = await ownRigs();
      if (!choices.length) return;
      const form = document.createElement("form");
      form.className = "panel reply-form";
      form.innerHTML =
        '<h3>Rig used for this grind</h3><label>Your public Rig version<select name="rig">' +
        options(choices, "label") +
        "</select></label><p>This is your declaration of the configuration used. It is not independent verification. A Challenge submission must use its locked Rig and start after entry.</p><button>Save Rig declaration</button>";
      if (run.rig_revision) form.elements.rig.value = run.rig_revision;
      slot.append(form);
      action(form, async (f) => {
        await data(
          db.rpc("grinder_declare_run_rig", {
            grind: run.id,
            rig: f.elements.rig.value,
          }),
        );
        status("Rig declaration saved.");
      });
    } catch (e) {
      fail(e);
    }
  }
  return { index, show, rigs, rig, declareRig };
};
