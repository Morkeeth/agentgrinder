"""Controlled local UI journey; PostgreSQL rules run separately in test-database.mjs."""
import os,json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('GRINDER_MOMENT_RECEIPTS','/tmp/grinder-moment-fixtures'));OUT.mkdir(parents=True,exist_ok=True)
style=re.search(r'<style>(.*?)</style>',(ROOT/'site/index.html').read_text(),re.S).group(1)+(ROOT/'site/design.css').read_text()+(ROOT/'site/social.css').read_text()
setup=r'''
const owner='10000000-0000-0000-0000-000000000004',runId='20000000-0000-0000-0000-000000000004',practiceId='40000000-0000-0000-0000-000000000004',attemptId='50000000-0000-0000-0000-000000000004';
const run={id:runId,profile_id:owner,title:'TEST DATA parser repair',profiles:{github_handle:'fixture-builder'},visibility:'private',harness:'Codex',measurement_revision:'a'.repeat(64),trace_basis:'elapsed',rhythm:[0,1,4,2,1,3,0],prompts:3,artifacts_produced:1,commits:null,started_at:'2026-09-01T10:00:00Z',note:'DO NOT EXPORT RAW NOTE',project:'DO NOT EXPORT PRIVATE PROJECT'};
const tables=JSON.parse(sessionStorage.getItem('fixtureTables')||'null')||{grinder_run_moments:[],grinder_practice_versions:[],grinder_practice_attempts:[],runs:[run,{...run,id:'20000000-0000-0000-0000-000000000005',title:'TEST DATA later check',started_at:'2026-09-03T10:00:00Z',measurement_revision:'b'.repeat(64),prompts:2}]};
const persist=()=>sessionStorage.setItem('fixtureTables',JSON.stringify(tables));
let failSave=false;
const db={from(name){let filters=[],insert=null,del=false;const q={select(){return q},eq(k,v){filters.push(r=>r[k]===v);return q},not(){return q},order(){return q},limit(){return q},insert(v){insert=v;return q},delete(){del=true;return q},then(resolve,reject){if(insert&&failSave)return Promise.resolve({error:{message:'TEST DATA save unavailable'}}).then(resolve,reject);let data=(tables[name]||[]).filter(r=>filters.every(f=>f(r)));if(insert){data=[{...insert,created_at:'2026-09-02T10:00:00Z'}];tables[name].push(...data);persist()}if(del){tables[name]=tables[name].filter(r=>!data.includes(r));persist()}return Promise.resolve({data}).then(resolve,reject)}};return q},async rpc(name,payload){if(name==='grinder_practice_from_moment'){tables.grinder_practice_versions.push({id:practiceId,title:payload.action_title,instruction:payload.action_title,expected:payload.expected_change,visibility:'private',harness:'Codex',task_context:'TEST DATA from moment'});tables.grinder_practice_attempts.push({id:attemptId,owner_id:owner,practice_id:practiceId,baseline:{...run,turns_typed:3},visibility:'private',created_at:'2026-09-02T12:00:00Z'});persist();return {data:{practice_id:practiceId,attempt_id:attemptId}}}if(name==='grinder_review_attempt'){const a=tables.grinder_practice_attempts[0];a.reviewed_at='2026-09-04T10:00:00Z';a.decision=payload.choice;a.note=payload.reflection;a.outcome={...tables.runs.find(r=>r.id===payload.outcome_run),turns_typed:2};persist();return {data:[]}}throw Error('Unexpected fixture RPC '+name)}};
const status=text=>document.getElementById('status').textContent=text;
const config={client:db,me:()=>({id:owner,github_handle:'fixture-builder'}),app:()=>document.getElementById('app'),frame:()=>{},status};
window.openMoments=()=>GrinderMoments.mount({...config,run,slot:document.getElementById('app')});
window.openPractice=()=>GrinderPractices(config).detail(practiceId);
window.openShare=()=>GrinderSharing.mount({run,slot:document.getElementById('app'),status,moment:tables.grinder_run_moments[0]});
'''
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 page=browser.new_page(viewport={'width':390,'height':844},accept_downloads=True)
 page.route('**/*',lambda r:r.fulfill(content_type='text/html',body='<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>'+style+'</style><p>TEST DATA · controlled interface fixture</p><div id="status" role="status"></div><main id="app"></main>'))
 page.goto('https://grinder-moment-fixture.test/?run=20000000-0000-0000-0000-000000000004')
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def boot():
  for name in ['run-contract.js','practice-eligibility.js','practices.js','sharing.js','moments.js']:page.add_script_tag(content=(ROOT/'site'/name).read_text())
  page.add_script_tag(content=setup)
 boot();page.evaluate('openMoments()')
 page.get_by_text('No moment recorded yet.',exact=False).wait_for()
 page.get_by_text('Add a moment',exact=True).click()
 for label,value in [('Moment title','TEST DATA the check that changed the plan'),('What happened?','TEST DATA parser check passed after repair.'),('Exact evidence reference','https://example.test/receipt'),('Exact excerpt to show','TEST DATA: 1 check passed\n<script>not code</script>'),('What does this NOT establish?','One local fixture, not deployed or independently verified.'),('One change for the next grind','Run the failing check before editing')]:page.get_by_label(label,exact=True).fill(value)
 page.get_by_label('Place on the activity trace').select_option('2')
 page.get_by_label('I reviewed these fields').check()
 page.evaluate('failSave=true');page.get_by_role('button',name='Save moment',exact=True).click()
 page.get_by_text('TEST DATA save unavailable',exact=True).wait_for();assert page.get_by_label('Exact excerpt to show').input_value().endswith('<script>not code</script>')
 page.evaluate('failSave=false');page.get_by_role('button',name='Save moment',exact=True).click()
 page.get_by_text('Moment saved with this run’s audience.',exact=True).wait_for()
 assert page.locator('.moment-dot').count()==1
 assert page.locator('.moment-proof pre').inner_text()=='TEST DATA: 1 check passed\n<script>not code</script>'
 assert page.locator('.moment-reader script').count()==0
 assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
 page.screenshot(path=str(OUT/'moment-phone.png'),full_page=True)
 page.set_viewport_size({'width':1440,'height':1000});page.screenshot(path=str(OUT/'moment-desktop.png'),full_page=True)
 # Existing share export, now populated by the explicitly chosen moment, with a mandatory review.
 page.evaluate('openShare()');assert page.get_by_role('button',name='Download PNG').is_disabled()
 caption=page.get_by_label('Caption',exact=True).input_value()
 assert 'Limit:' in caption and 'independently verified' in caption
 assert 'DO NOT EXPORT' not in caption and '<script>' not in caption and '?run=' not in caption
 page.get_by_label('Image format').select_option('portrait');page.get_by_label('I have reviewed this image').check()
 with page.expect_download() as download:page.get_by_role('button',name='Download PNG').click()
 download.value.save_as(str(OUT/'moment-share.png'))
 page.get_by_label('What was the result?',exact=True).fill('TEST DATA '+('long observation '*100))
 page.get_by_label('I have reviewed this image').check();assert page.get_by_role('button',name='Download PNG').is_disabled()
 from PIL import Image
 assert Image.open(OUT/'moment-share.png').size==(1080,1350)
 page.evaluate('openMoments()');page.get_by_label('What would you look for?').fill('TEST DATA check before edit; record missing evidence honestly')
 page.get_by_role('button',name='Save practice and baseline').click()
 page.wait_for_url('**/?practice=40000000-0000-0000-0000-000000000004#attempt-*')
 # New document, same browser fixture store: the actual existing practice screen receives the saved attempt.
 boot();page.evaluate('openPractice()');page.get_by_role('heading',name='Your baseline is saved',exact=True).wait_for()
 page.get_by_label('Session after you started this attempt').select_option('20000000-0000-0000-0000-000000000005')
 page.get_by_label('Your decision').select_option('keep');page.get_by_label('What happened?',exact=True).fill('TEST DATA check ran first; one observation, no causal claim')
 page.get_by_role('button',name='Save review').click();page.get_by_role('heading',name='This return is recorded',exact=True).wait_for()
 page.set_viewport_size({'width':390,'height':844});assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
 page.screenshot(path=str(OUT/'moment-return-phone.png'),full_page=True)
 # Frozen moment cannot be shared against different current metrics or used as a new baseline.
 page.evaluate("run.measurement_revision='f'.repeat(64);openMoments()")
 assert page.get_by_role('button',name='Save practice and baseline').count()==0
 assert page.get_by_role('link',name='Make this my share card').count()==0
 page.evaluate('openShare()');page.get_by_text('This moment belongs to a different measurement.',exact=False).wait_for()
 assert page.locator('canvas').count()==0
 assert page.evaluate("GrinderMoments.safeLink('javascript:alert(1)')") is None
 assert page.evaluate("GrinderMoments.safeLink('https://user:password@example.test')") is None
 assert not errors,errors
 print(json.dumps({'fixture':'controlled browser responses, not hosted users','moment_save_retry':True,'escaped_exact_excerpt':True,'pin':True,'review_gated_PNG':'1080x1350','private_caption_no_link':True,'practice_handoff_and_return':True,'phone_overflow':False,'page_errors':errors}))
 browser.close()
