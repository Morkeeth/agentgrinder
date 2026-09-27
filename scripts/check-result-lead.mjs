import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {ImageResponse} from '@vercel/og';
import {present, guard, resultSource, formatDuration} from '../site/result-lead.js';
import {readPublic, html, card} from '../server/public-run.mjs';

const sundayId = 'a6f0fc15-ebf9-4c33-9c18-91b4a6b2623f';
const live = await readPublic(sundayId);
assert.equal(live?.id, sundayId);
assert.equal(live.visibility, 'public');
assert.equal(
  live.note,
  'Shipped the CLI coach, the route map, and the ACK loop. One region ate the whole afternoon.',
);
assert.equal(live.duration_s, 8400);
assert.equal(formatDuration(live.duration_s), '2h 20m');
assert.equal(live.coach_verdict, null);
assert.equal(live.is_ship, true);
assert.equal(live.commits, 3);
assert.deepEqual(live.route, [0, 0, 1, 0, 2, 2, 1, 0, 3, 3, 2, 0, 0, 1, 4, 0]);
assert.equal(new Set(live.route).size, 5);

const lead = guard(present(live, 'view'), live);
assert.equal(lead.outcome, live.note);
assert.equal(lead.outcomeSource, 'runs.note');
assert.equal(lead.sourceLine, 'Evidence source: runs.note');
assert.equal(lead.duration, '2h 20m');
assert.equal(lead.durationSource, 'runs.duration_s');
for (const row of lead.support) {
  if (row.source === 'runs.route') assert.equal(row.value, 5);
  if (row.source === 'runs.commits') assert.equal(row.value, 3);
  if (row.source === 'runs.is_ship') assert.equal(row.value, true);
  assert.equal(row.text.includes(String(row.value === true ? 'shipped' : row.value)), true);
}

const page = html(live);
const body = page.slice(page.indexOf('<body>'));
const outcomeAt = body.indexOf('<h1>' + live.note);
const sourceAt = body.indexOf('Evidence source: runs.note');
const limitAt = body.indexOf('<strong>Limit:</strong>');
const durationAt = body.indexOf('>2h 20m<');
assert.ok(outcomeAt > 0 && sourceAt > outcomeAt && limitAt > sourceAt && durationAt > limitAt);
assert.ok(page.indexOf('<meta property="og:title" content="' + live.note) > 0);
assert.equal(page.includes('Deep focus'), false);
for (const row of lead.support) assert.ok(page.includes(row.text), row.text);
assert.ok(body.indexOf('Session time') < durationAt);

const privateShare = guard(present({ ...live, visibility: 'private' }, 'share'), { ...live, visibility: 'private' });
assert.equal(privateShare.outcome, null);
assert.equal(JSON.stringify(privateShare).includes(live.note), false);

const publicShare = guard(present(live, 'share'), live);
assert.equal(publicShare.outcome, live.note);

const withVerdict = { ...live, coach_verdict: '3 of 7 claims had evidence in their own turn.' };
const verdictLead = guard(present(withVerdict, 'view'), withVerdict);
assert.equal(verdictLead.outcome, withVerdict.coach_verdict);
assert.equal(verdictLead.outcomeSource, 'runs.coach_verdict');
assert.equal(verdictLead.outcome.includes('One region'), false);

const fake = { ...lead, outcome: 'Deep focus' };
assert.throws(() => guard(fake, live), /result source guard/);
const saved = resultSource.guard;
let brokenAccepted = false;
resultSource.guard = (broken) => {
  brokenAccepted = true;
  return broken;
};
resultSource.guard(fake, live);
assert.equal(brokenAccepted, true);
assert.equal(JSON.stringify(live).includes('Deep focus'), false);
resultSource.guard = saved;
assert.throws(() => guard(fake, live), /result source guard/);
assert.equal(guard(present(live, 'og'), live).outcome, live.note);

const image = new ImageResponse(card(live), { width: 1200, height: 630 });
const bytes = Buffer.from(await image.arrayBuffer());
assert.equal(bytes.subarray(1, 4).toString(), 'PNG');
assert.equal(bytes.readUInt32BE(16), 1200);
assert.equal(bytes.readUInt32BE(20), 630);

const app = readFileSync(new URL('../site/index.html', import.meta.url), 'utf8');
const cardSrc = app.slice(app.indexOf('function runCard('), app.indexOf('function wireKudos('));
assert.ok(cardSrc.indexOf('resultLeadHtml(r)') < cardSrc.indexOf('run-signature'));
assert.ok(cardSrc.indexOf('run-signature') < cardSrc.indexOf('run-key-facts'));
assert.equal(cardSrc.includes('Session time:'), false);

console.log('Result lead: Sunday outcome, source, limit, then 2h 20m; guard broken once and restored; OG PNG passed');
