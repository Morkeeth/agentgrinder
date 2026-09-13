import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const context={window:{}};vm.runInNewContext(readFileSync(new URL('../site/sharing.js',import.meta.url),'utf8'),context);
const {reviewExport}=context.window.GrinderSharing;
const attempt={id:'fixture-attempt',owner_id:'reader',reviewed_at:'2026-09-13',decision:'keep',tried:true,note:'PRIVATE REFLECTION',source_run:'AUTHOR SOURCE',outcome:{turns_typed:3,artifacts_produced:1,harness:'Codex',rhythm:[1,2],trace_basis:'position',project:'PRIVATE PROJECT',title:'PRIVATE TITLE',profiles:{github_handle:'AUTHOR'},measurement_revision:'PRIVATE REVISION'}};
assert.equal(reviewExport(attempt,'other'),null);
assert.equal(reviewExport(attempt,null),null);
assert.equal(reviewExport({...attempt,reviewed_at:null},'reader'),null);
for(const decision of ['keep','change','drop','incomparable']){
 const out=reviewExport({...attempt,decision},'reader');
 assert.equal(out.review.decision,decision);assert.equal(out.run.turns_typed,3);assert.equal(out.run.visibility,'private');
 assert(!JSON.stringify(out).match(/PRIVATE|AUTHOR/));
 assert.equal(out.run.profiles,undefined);assert.equal(out.run.measurement_revision,undefined);
}
const missing=reviewExport({...attempt,decision:'incomparable',tried:false,outcome:null},'reader');
assert.equal(missing.run.turns_typed,null);assert.equal(missing.run.rhythm,null);
console.log('Review export: ownership, completion, all decisions, missing evidence and strict privacy allowlist passed.');
