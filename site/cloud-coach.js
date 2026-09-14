/* Opt-in private coaching. The server reads the owned run; no transcript upload. */
(function (root) {
  'use strict';
  const FIELDS = ['prompts','tool_calls','files_touched','commits','claims','claims_verified','artifacts_produced','duration_s'];
  function preview(run) {
    const out = {harness: run.harness, measurement_revision: run.measurement_revision};
    for (const field of FIELDS) {
      const n = run[field];
      if (n != null && (typeof n !== 'number' || !Number.isFinite(n) || n < 0)) throw new Error('This run has invalid measurements.');
      out[field] = n == null ? null : n;
    }
    return out;
  }
  function validate(result, run, contract) {
    if (!result || result.run_id !== run.id || result.measurement_revision !== run.measurement_revision)
      throw new Error('The reply does not match this measured run. Reload before trying again.');
    const clean = contract.rejectPaths(result);
    const exp = clean && clean.coach_experiment;
    if (!exp || !['title','instruction','expected'].every(k => typeof exp[k] === 'string' && exp[k].trim()) ||
        typeof clean.coach_verdict !== 'string' || typeof clean.coach_mode !== 'string' ||
        !Number.isSafeInteger(clean.coach_tool_calls) || clean.coach_tool_calls < 1)
      throw new Error('The coach did not return a complete proposal. Nothing was saved.');
    return clean;
  }
  function mount({run, slot, client, me, contract, mountExperiment}) {
    const endpoint = root.GRINDER_COACH_URL;
    if (!slot || !endpoint || !me || me.id !== run.profile_id || run.visibility !== 'private' || !run.measurement_revision) return;
    let data;
    try { data = preview(run); } catch (_) { return; }
    slot.innerHTML = '<section class="panel reply-form"><h2>Coach this run</h2><p>Ask the AWS Strands coach for one practice to try next. It uses recorded measurements; it cannot inspect your files or verify your code.</p><form><label>What do you want to improve? (optional)<textarea name="goal" maxlength="400" rows="2" placeholder="For example: make my next session easier to review"></textarea></label><p class="hint">Keep secrets and private notes out of this goal.</p><details><summary>See the measurements sent to AWS</summary><pre class="cloud-preview" style="white-space:pre-wrap;overflow-wrap:anywhere"></pre></details><label style="display:flex;gap:10px;align-items:flex-start;margin:16px 0"><input type="checkbox" name="consent" required style="width:auto;margin-top:4px"><span>I agree to send these run counts, harness, measurement reference and my optional goal to AWS for this review. No transcript, run title, file paths or saved private notes are read from your run.</span></label><button type="submit">Coach this run</button><p class="hint">A proposal is private and is not saved until you accept it. This does not publish your run.</p><p class="cloud-status" role="status" aria-live="polite"></p></form><div class="cloud-result"></div></section>';
    slot.querySelector('.cloud-preview').textContent = JSON.stringify(data, null, 2);
    const form = slot.querySelector('form'), button = form.querySelector('button');
    const status = slot.querySelector('.cloud-status'), target = slot.querySelector('.cloud-result');
    form.onsubmit = async event => {
      event.preventDefault();
      if (!form.elements.consent.checked || button.disabled) return;
      button.disabled = true; status.textContent = 'The coach is reviewing these measurements…'; target.replaceChildren();
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 90000);
      try {
        const auth = await client.auth.getSession();
        const token = auth.data?.session?.access_token;
        if (!token) throw new Error('Sign in again before asking the coach.');
        const response = await fetch(endpoint, {method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},
          body:JSON.stringify({run_id:run.id,consent_version:'metrics-v1',goal:form.elements.goal.value.trim()}),signal:controller.signal});
        if (!response.ok) {
          const errors = {401:'Your sign-in expired. Sign in again.',403:'Only the owner can coach a private run.',409:'The run changed. Reload it before asking the coach.',429:'The coaching limit has been reached. Try again later.',503:'The AWS coach is unavailable. Please try again later.'};
          throw new Error(errors[response.status] || 'The coach could not complete this request. Nothing was saved.');
        }
        const result = validate(await response.json(), run, contract);
        if (!slot.isConnected) return;
        const summary = document.createElement('p'); summary.textContent = result.coach_verdict; target.append(summary);
        const proposed = document.createElement('div'); target.append(proposed);
        await mountExperiment({...run,coach_verdict:result.coach_verdict,coach_mode:result.coach_mode+' · metrics-only',coach_tool_calls:result.coach_tool_calls,coach_experiment:result.coach_experiment}, proposed);
        status.textContent = 'Review this proposal below. Nothing has been saved yet.';
      } catch (error) {
        status.textContent = error.name === 'AbortError' ? 'The request timed out. No proposal was saved. The AWS request may still finish.' : error.message;
      } finally { clearTimeout(timer); button.disabled = false; }
    };
  }
  root.GrinderCloudCoach = {mount, preview, validate};
  if (typeof module !== 'undefined') module.exports = root.GrinderCloudCoach;
})(typeof window !== 'undefined' ? window : globalThis);
