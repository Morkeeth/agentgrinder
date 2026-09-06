/* Deliberately authored highlights: the evidence shown is exactly what the maker saved. */
(function (root) {
  "use strict";
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
  const uuid = (x) =>
    /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i.test(x || "");
  function safeLink(x) {
    try {
      const u = new URL(x);
      return ["https:", "http:"].includes(u.protocol) &&
        !u.username &&
        !u.password &&
        !/[\x00-\x20]/.test(x)
        ? u.href
        : null;
    } catch (_) {
      return null;
    }
  }
  async function rows(q) {
    const r = await q;
    if (r.error) throw Error(r.error.message);
    return r.data || [];
  }
  async function mount({ run, slot, client: db, me, status }) {
    const owner = me()?.id === run.profile_id;
    let moments = [];
    let selected = null;
    let requestId = crypto.randomUUID();
    try {
      moments = await rows(
        db
          .from("grinder_run_moments")
          .select("*")
          .eq("run_id", run.id)
          .order("created_at", { ascending: true }),
      );
    } catch (e) {
      slot.innerHTML =
        '<p class="hint">Grind moments are unavailable on this deployment. Your run and practices are still available.</p>';
      return;
    }
    slot.innerHTML = `<section class="moment-room panel"><div class="pad"><p class="meta">THE MOMENT BEHIND THE GRIND</p><h2>Show the bit worth coming back for.</h2><p>Choose a moment. Open the evidence. Turn it into your next practice.</p><p class="hint">Builder-authored observations, not independent verification. A pin marks the builder’s chosen activity bucket, not a recovered event time.</p><div class="moment-map">${GrinderContract.trace(run)}<div class="moment-pins" role="group" aria-label="Grind moments"></div></div><div class="moment-reader" aria-live="polite"></div>${
      owner
        ? `<details class="moment-compose"><summary>Add a moment</summary><form class="reply-form" id="moment-form"><label>Moment title<input name="title" maxlength="100" required placeholder="The test that changed the plan"></label><label>What happened?<textarea name="claim" maxlength="1000" required></textarea></label><label>Exact evidence reference<input name="evidence_ref" maxlength="1000" required placeholder="Public commit URL, test name or receipt identifier"></label><label>Exact excerpt to show<textarea name="excerpt" maxlength="3000" required placeholder="Paste only the non-sensitive result you want this audience to read."></textarea></label><label>What does this NOT establish?<textarea name="limitation" maxlength="1000" required placeholder="For example: one local check, not adoption or deployment."></textarea></label><label>One change for the next grind<input name="next_action" maxlength="160" required></label><label>Place on the activity trace<select name="bucket"><option value="">No time position claimed</option>${
            Array.isArray(run.rhythm)
              ? run.rhythm
                  .slice(0, 10000)
                  .map(
                    (_, i) =>
                      `<option value="${i}">Activity bucket ${i + 1}</option>`,
                  )
                  .join("")
              : ""
          }</select></label><p>Saved with this run’s audience. These exact fields become visible wherever the run is readable; its future audience changes also apply. Raw transcripts and existing notes are never copied.</p><label><input name="consent" type="checkbox" required> I reviewed these fields for this run’s audience.</label><button ${run.measurement_revision ? "" : "disabled"}>Save moment</button>${run.measurement_revision ? "" : "<p>A measured revision is required before you can bind a moment.</p>"}<p id="moment-save-status" role="status"></p></form></details>`
        : ""
    }</div></section>`;
    const pins = slot.querySelector(".moment-pins"),
      reader = slot.querySelector(".moment-reader");
    function show(id) {
      selected = moments.find((x) => x.id === id) || moments[0];
      if (!selected) {
        reader.innerHTML =
          "<p>No moment recorded yet. The activity trace alone cannot tell us what was achieved.</p>";
        return;
      }
      const m = selected,
        stale = m.measurement_revision !== run.measurement_revision,
        link = safeLink(m.evidence_ref);
      pins
        .querySelectorAll("button")
        .forEach((b) =>
          b.setAttribute("aria-pressed", String(b.dataset.id === m.id)),
        );
      reader.innerHTML = `<article id="moment-${esc(m.id)}"><p class="meta">${stale ? "OLD MEASUREMENT · CURRENT RUN CHANGED" : "BUILDER OBSERVATION"} · ${m.bucket == null ? "No time position claimed" : "Builder-selected bucket " + (m.bucket + 1)}</p><h3>${esc(m.title)}</h3><p class="moment-claim">${esc(m.claim)}</p><details class="moment-proof" open><summary>Inspect the exact evidence</summary><p>${link ? `<a href="${esc(link)}" target="_blank" rel="noreferrer noopener">${esc(m.evidence_ref)}</a>` : `<code>${esc(m.evidence_ref)}</code>`}</p><pre>${esc(m.excerpt)}</pre><p><strong>Limit:</strong> ${esc(m.limitation)}</p><small>Bound measurement: <code>${esc(m.measurement_revision)}</code>. A reference is not proof of its contents.</small></details><p><strong>Next practice:</strong> ${esc(m.next_action)}</p><div class="cta">${!stale ? `<a class="act" href="/?share=1&run=${encodeURIComponent(run.id)}&moment=${encodeURIComponent(m.id)}">Make this my share card</a>` : "<span>Share export unavailable: the run measurement changed.</span>"}${owner ? '<button class="ghost" id="moment-remove">Remove moment</button>' : ""}</div>${owner && !stale ? `<form id="moment-practice" class="reply-form"><h3>Try it on the next grind</h3><label>One change<input name="action" required maxlength="160" value="${esc(m.next_action)}"></label><label>What would you look for?<textarea name="expected" required maxlength="2000" placeholder="Name the result or failure that would change your mind."></textarea></label><p>Save a private practice and freeze this grind as its baseline. Review a later session through the existing practice flow.</p><button>Save practice and baseline</button></form>` : stale ? "<p>This moment belongs to an older measurement. Keep it as history; make a new moment before starting a practice.</p>" : '<p>Want to try a change yourself? <a href="/?practices">Choose a practice using your own baseline.</a></p>'}</article>`;
      const remove = reader.querySelector("#moment-remove");
      if (remove)
        remove.onclick = async () => {
          if (
            !confirm(
              "Remove this authored moment? The grind and its history stay.",
            )
          )
            return;
          remove.disabled = true;
          try {
            await rows(db.from("grinder_run_moments").delete().eq("id", m.id));
            moments = moments.filter((x) => x.id !== m.id);
            draw();
          } catch (e) {
            status(GrinderContract.message(e), true);
            remove.disabled = false;
          }
        };
      const f = reader.querySelector("#moment-practice");
      if (f)
        f.onsubmit = async (e) => {
          e.preventDefault();
          const b = f.querySelector("button");
          b.disabled = true;
          try {
            const result = await rows(
              db.rpc("grinder_practice_from_moment", {
                moment: m.id,
                action_title: f.elements.action.value,
                expected_change: f.elements.expected.value,
              }),
            );
            location.href =
              "/?practice=" +
              result.practice_id +
              "#attempt-" +
              result.attempt_id;
          } catch (error) {
            status(GrinderContract.message(error), true);
            b.disabled = false;
          }
        };
    }
    function draw() {
      const svg = slot.querySelector(".moment-map svg");
      if (svg) {
        svg.querySelectorAll(".moment-dot").forEach((x) => x.remove());
        const vals = run.rhythm;
        moments.forEach((m) => {
          if (
            !Number.isInteger(m.bucket) ||
            m.bucket < 0 ||
            m.bucket >= vals.length
          )
            return;
          const dot = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "circle",
          );
          dot.setAttribute("class", "moment-dot");
          dot.setAttribute(
            "cx",
            String(4 + (m.bucket * 232) / Math.max(1, vals.length - 1)),
          );
          dot.setAttribute(
            "cy",
            String(64 - (vals[m.bucket] * 54) / Math.max(1, ...vals)),
          );
          dot.setAttribute("r", "4");
          dot.setAttribute("fill", "var(--blue)");
          dot.setAttribute("aria-hidden", "true");
          svg.append(dot);
        });
      }
      pins.innerHTML = moments
        .map(
          (m, i) =>
            `<button type="button" data-id="${esc(m.id)}" aria-pressed="false" title="${esc(m.title)}">${i + 1} · ${esc(m.title)}</button>`,
        )
        .join("");
      pins
        .querySelectorAll("button")
        .forEach((b) => (b.onclick = () => show(b.dataset.id)));
      show(selected?.id || new URLSearchParams(location.search).get("moment"));
    }
    const f = slot.querySelector("#moment-form");
    if (f)
      f.onsubmit = async (e) => {
        e.preventDefault();
        if (!f.reportValidity()) return;
        const b = f.querySelector("button");
        b.disabled = true;
        const v = f.elements;
        try {
          const row = {
            id: requestId,
            run_id: run.id,
            owner_id: me().id,
            measurement_revision: run.measurement_revision,
            ...Object.fromEntries(
              [
                "title",
                "claim",
                "evidence_ref",
                "excerpt",
                "limitation",
                "next_action",
              ].map((k) => [k, v[k].value.trim()]),
            ),
            bucket: v.bucket.value === "" ? null : Number(v.bucket.value),
          };
          const result = await rows(
            db.from("grinder_run_moments").insert(row).select("*"),
          );
          if (!result[0])
            throw Error(
              "The saved moment could not be read. Reload before retrying.",
            );
          moments.push(result[0]);
          selected = result[0];
          requestId = crypto.randomUUID();
          f.reset();
          draw();
          f.closest("details").open = false;
          status("Moment saved with this run’s audience.");
        } catch (error) {
          status(GrinderContract.message(error), true);
        } finally {
          b.disabled = false;
        }
      };
    draw();
  }
  root.GrinderMoments = { mount, safeLink };
})(window);
