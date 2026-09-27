/* Result lead. Every visible outcome, count and duration is copied from one field
   on the run object. The guard rejects a lead that does not match that object. */
export function redact(value) {
  return String(value ?? "")
    .split("\n")
    .map((line) =>
      line
        .split(/\s+/)
        .map((raw) => {
          if (!raw) return raw;
          const parts = raw.match(/^([,.;:()[\]{}'"`]*)(.*?)([,.;:()[\]{}'"`]*)$/);
          const tok = parts ? parts[2] : raw;
          if (
            tok.startsWith("/") ||
            tok.startsWith("~") ||
            tok.includes("\\") ||
            tok.includes("/") ||
            /^[A-Za-z]:/.test(tok)
          )
            return (parts ? parts[1] : "") + "[file]" + (parts ? parts[3] : "");
          return raw;
        })
        .join(" "),
    )
    .join("\n");
}

export function formatDuration(seconds) {
  if (typeof seconds !== "number" || !Number.isFinite(seconds) || seconds < 0) return null;
  const minutes = Math.round(seconds / 60);
  if (minutes >= 60) return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
  return `${minutes}m`;
}

function validRoute(route) {
  return (
    Array.isArray(route) &&
    route.length > 0 &&
    route.length <= 10000 &&
    route.every((n) => Number.isInteger(n) && n >= 0)
  );
}

const LIMITS = {
  "runs.coach_verdict":
    "Client-supplied coach report. It does not independently verify result quality. Counts are activity, not a result.",
  "runs.note":
    "Builder-authored note. It is not checked against the route or the commits. Counts are activity, not result quality, and do not independently verify the result.",
  none: "No observed outcome is stored for this view. Duration and counts are activity, not result quality.",
};

export function present(run, surface) {
  if (!run || typeof run !== "object" || Array.isArray(run)) throw new Error("missing run");
  if (!["view", "og", "share"].includes(surface)) throw new Error("unknown surface");
  const verdict = typeof run.coach_verdict === "string" ? run.coach_verdict.trim() : "";
  const note = typeof run.note === "string" ? run.note.trim() : "";
  const noteAllowed = surface === "view" || surface === "og" || (surface === "share" && run.visibility === "public");
  let outcome = null;
  let outcomeSource = null;
  if (verdict) {
    outcome = redact(verdict);
    outcomeSource = "runs.coach_verdict";
  } else if (note && noteAllowed) {
    outcome = redact(note);
    outcomeSource = "runs.note";
  }
  const support = [];
  if (validRoute(run.route)) {
    const regions = new Set(run.route).size;
    support.push({ source: "runs.route", value: regions, text: `${regions} regions in touch order · runs.route` });
  }
  if (run.is_ship === true) support.push({ source: "runs.is_ship", value: true, text: "Marked shipped · runs.is_ship" });
  if (Number.isSafeInteger(run.commits) && run.commits >= 0) {
    support.push({ source: "runs.commits", value: run.commits, text: `${run.commits} commits recorded · runs.commits` });
  }
  if (outcomeSource === "runs.coach_verdict" && Number.isSafeInteger(run.coach_tool_calls) && run.coach_tool_calls >= 0) {
    support.push({
      source: "runs.coach_tool_calls",
      value: run.coach_tool_calls,
      text: `${run.coach_tool_calls} coach tool calls · runs.coach_tool_calls`,
    });
  }
  const duration = formatDuration(run.duration_s);
  return {
    surface,
    outcome,
    outcomeSource,
    sourceLine: outcomeSource ? `Evidence source: ${outcomeSource}` : "Evidence source: none stored for this view",
    support,
    limit: LIMITS[outcomeSource || "none"],
    duration,
    durationSource: duration == null ? null : "runs.duration_s",
  };
}

function sameSupport(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

export const resultSource = {
  guard(lead, run) {
    if (!lead || !run) throw new Error("result source guard: missing lead");
    const again = present(run, lead.surface);
    if (lead.outcome !== again.outcome) throw new Error("result source guard: outcome is not the stored field");
    if (lead.outcomeSource !== again.outcomeSource) throw new Error("result source guard: source field changed");
    if (lead.sourceLine !== again.sourceLine) throw new Error("result source guard: source line changed");
    if (lead.limit !== again.limit) throw new Error("result source guard: limit changed");
    if (lead.duration !== again.duration) throw new Error("result source guard: duration is not runs.duration_s");
    if (!sameSupport(lead.support, again.support)) throw new Error("result source guard: support is not on the run");
    if (lead.outcomeSource === "runs.note" && lead.outcome !== redact(String(run.note).trim())) {
      throw new Error("result source guard: note mismatch");
    }
    if (lead.outcomeSource === "runs.coach_verdict" && lead.outcome !== redact(String(run.coach_verdict).trim())) {
      throw new Error("result source guard: verdict mismatch");
    }
    if (lead.outcomeSource == null && lead.outcome != null) throw new Error("result source guard: unsourced outcome");
    if (lead.duration != null && lead.duration !== formatDuration(run.duration_s)) {
      throw new Error("result source guard: duration mismatch");
    }
    for (const row of lead.support || []) {
      if (row.source === "runs.route" && row.value !== new Set(run.route).size) throw new Error("result source guard: route");
      if (row.source === "runs.commits" && row.value !== run.commits) throw new Error("result source guard: commits");
      if (row.source === "runs.is_ship" && run.is_ship !== true) throw new Error("result source guard: ship");
      if (row.source === "runs.coach_tool_calls" && row.value !== run.coach_tool_calls) {
        throw new Error("result source guard: coach tool calls");
      }
    }
    return lead;
  },
};

export function guard(lead, run) {
  return resultSource.guard(lead, run);
}

export function html(lead, esc) {
  const e = esc || ((s) => String(s ?? ""));
  const outcome = lead.outcome ? e(lead.outcome) : "No observed outcome is stored for this view.";
  const support = (lead.support || [])
    .map((row) => `<p data-result-claim data-source="${e(row.source)}">${e(row.text)}</p>`)
    .join("");
  const duration = lead.duration ? e(lead.duration) : "Unknown";
  return `<section class="result-lead" data-result-lead>
    <p class="kicker">Observed outcome</p>
    <p class="outcome" data-result-claim data-source="${e(lead.outcomeSource || "none")}">${outcome}</p>
    <p data-result-claim data-source="${e(lead.outcomeSource || "none")}">${e(lead.sourceLine)}</p>
    ${support}
    <p class="limit" data-result-claim data-source="limit">${e(lead.limit)}</p>
    <p class="duration" data-result-claim data-source="${e(lead.durationSource || "runs.duration_s")}"><span>Session time</span><strong>${duration}</strong></p>
  </section>`;
}

if (typeof window !== "undefined") window.GrinderResultLead = { present, guard, html, formatDuration, redact, resultSource };
