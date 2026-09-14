(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.GrinderPracticeEligibility = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function outcomeRuns(attempt, runs, now = Date.now()) {
    const attemptTime = Date.parse(attempt.created_at || "");
    if (!Number.isFinite(attemptTime)) return [];
    return runs.filter((run) => {
      const runTime = Date.parse(run.started_at || "");
      return Number.isFinite(runTime) &&
        runTime >= attemptTime &&
        runTime <= now &&
        run.measurement_revision !== attempt.baseline?.measurement_revision;
    });
  }
  return { outcomeRuns };
});
