/* Shared browser boundary: a successful parse is not permission to store arbitrary fields. */
(function (root) {
  "use strict";
  const counts = [
    "turns_typed",
    "tool_calls",
    "files_touched",
    "commits",
    "claims",
    "claims_verified",
    "artifacts_produced",
  ];
  function esc(value) {
    return String(value ?? "").replace(
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
  }
  function validate(run) {
    if (!run || typeof run !== "object" || Array.isArray(run))
      throw new Error("A grind must be a JSON object.");
    const version = run.schema_version ?? 0;
    if (!Number.isInteger(version) || ![0, 1].includes(version))
      throw new Error(
        "This grind uses an unsupported format. Update Agent Grinder to read it.",
      );
    for (const field of counts) {
      if (
        run[field] != null &&
        (!Number.isSafeInteger(run[field]) || run[field] < 0)
      )
        throw new Error(
          field + " must be a non-negative whole number or unknown.",
        );
    }
    if (
      run.duration_s != null &&
      (typeof run.duration_s !== "number" ||
        !Number.isFinite(run.duration_s) ||
        run.duration_s < 0)
    )
      throw new Error("Invalid grind duration.");
    if (run.claims_verified != null && run.claims == null)
      throw new Error("Verified claims require a counted-claims total.");
    if (
      run.claims != null &&
      run.claims_verified != null &&
      run.claims_verified > run.claims
    )
      throw new Error("Verified claims cannot exceed the claims counted.");
    for (const field of ["measurement_revision", "baseline_revision"]) {
      if (
        run[field] != null &&
        (typeof run[field] !== "string" || !/^[a-f0-9]{64}$/.test(run[field]))
      )
        throw new Error("Invalid measurement revision reference.");
    }
    return run;
  }
  function message(error) {
    const text =
      error?.message || "This action could not be completed. Try again.";
    return /schema cache|could not find the table|relation .*does not exist|column .*does not exist/i.test(
      text,
    )
      ? "This part of Grinder is not available on this deployment yet."
      : text;
  }
  function traceBasis(snapshot) {
    const named =
      snapshot &&
      typeof snapshot.trace_basis === "string" &&
      snapshot.trace_basis.trim();
    return named || "Trace time basis unknown";
  }
  function trace(snapshot) {
    const values = snapshot?.rhythm;
    if (
      !Array.isArray(values) ||
      !values.length ||
      values.length > 10000 ||
      values.some((v) => !Number.isFinite(v) || v < 0)
    )
      return "<small>Trace unavailable</small>";
    const max = Math.max(1, ...values),
      points = values
        .map(
          (v, i) =>
            `${4 + (i * 232) / Math.max(1, values.length - 1)},${64 - (v * 54) / max}`,
        )
        .join(" ");
    const basis = traceBasis(snapshot);
    return (
      '<svg viewBox="0 0 240 72" role="img" aria-label="Recorded session rhythm: ' +
      esc(basis) +
      '" style="display:block;width:100%;color:var(--ink)"><polyline points="' +
      points +
      '" stroke="currentColor" fill="none" stroke-width="2"/></svg>' +
      '<small class="trace-basis">' +
      esc(basis) +
      "</small>"
    );
  }
  const api = { validate, message, trace, traceBasis };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.GrinderContract = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
