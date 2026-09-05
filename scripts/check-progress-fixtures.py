"""Exercise the returning-user forms with explicit browser fixtures, never hosted writes."""
import json
import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
style=(ROOT/'site/design.css').read_text()+re.search(r'<style>(.*?)</style>',(ROOT/'site/index.html').read_text(),re.S).group(1)+(ROOT/'site/social.css').read_text()
setup=r'''
const owner='10000000-0000-0000-0000-000000000004';
const earlier='20000000-0000-0000-0000-000000000004',later='20000000-0000-0000-0000-000000000005';
const comparisonId='30000000-0000-0000-0000-000000000004',practiceId='40000000-0000-0000-0000-000000000004',attemptId='50000000-0000-0000-0000-000000000004';
window.calls=[];
const tables={runs:[{id:later,profile_id:owner,title:'Later fixture run',harness:'Codex',visibility:'private',schema_version:1,measurement_revision:'f'.repeat(64),trace_basis:'elapsed',started_at:'2026-09-02T10:00:00Z',prompts:4,artifacts_produced:2,rhythm:[1,2,1,4]},
{id:earlier,profile_id:owner,title:'Earlier fixture run',harness:'Codex',visibility:'private',schema_version:1,measurement_revision:'e'.repeat(64),trace_basis:'elapsed',started_at:'2026-09-01T10:00:00Z',prompts:3,artifacts_produced:1,rhythm:[3,1,2,1]},
{id:'20000000-0000-0000-0000-000000000006',profile_id:owner,title:'Unmeasured fixture run',harness:'Cursor',visibility:'private',measurement_revision:null}],grinder_practice_attempts:[],grinder_notifications:[],grinder_comparisons:[],grinder_practice_versions:[],grinder_memberships:[]};
const client={from(name){let filters=[],start=0,end=100;const q={select(){return q},eq(k,v){filters.push(r=>r[k]===v);return q},is(k,v){filters.push(r=>(r[k]??null)===v);return q},not(k,op,v){filters.push(r=>(r[k]??null)!==v);return q},order(){return q},range(a,b){start=a;end=b+1;return q},limit(n){end=n;return q},then(resolve,reject){return Promise.resolve({data:(tables[name]||[]).filter(r=>filters.every(f=>f(r))).slice(start,end)}).then(resolve,reject)}};return q},async rpc(name,payload){window.calls.push({name,payload});if(name==='grinder_save_comparison'){
// This is an explicit server-response fixture. Real freeze/ownership rules run in PostgreSQL tests.
const before={...tables.runs[1],turns_typed:3},after={...tables.runs[0],turns_typed:4};
tables.grinder_comparisons.push({id:comparisonId,owner_id:owner,task_context:payload.context_text,created_at:'2026-09-03T10:00:00Z',before_run:before,after_run:after,limitations:[],next_practice:null});return {data:comparisonId};}
if(name==='grinder_practice_from_comparison'){tables.grinder_comparisons[0].next_practice=practiceId;tables.grinder_comparisons[0].next_attempt=attemptId;tables.grinder_practice_versions.push({id:practiceId,title:payload.action_title,instruction:payload.action_title,task_context:'Two fixture bug fixes',expected:payload.expected_change,visibility:'private',harness:'Codex'});tables.grinder_practice_attempts.push({id:attemptId,practice_id:practiceId,owner_id:owner,baseline:tables.grinder_comparisons[0].after_run,visibility:'private',practice:{title:payload.action_title,instruction:payload.action_title}});return {data:{practice_id:practiceId,attempt_id:attemptId}};}return {data:[]}}};
const config={client,me:()=>({id:owner,github_handle:'fixture-builder'}),app:()=>document.getElementById('app'),frame:()=>{},status:text=>document.getElementById('status').textContent=text,signIn:()=>{}};
window.progress=GrinderProgress(config);window.practices=GrinderPractices(config);
'''
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('BRAVE_BINARY','/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'),headless=True)
    page=browser.new_page(viewport={'width':390,'height':844})
    page.route('**/*',lambda route:route.fulfill(status=200,content_type='text/html',body='<meta charset="utf-8"><style>'+style+'</style><p>UI TEST FIXTURE — no real users or results</p><div id="status"></div><div class="shell solo"><main id="app" class="main"></main></div>'))
    page.goto('https://grinder-fixture.test/?mine')
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    for name in ['run-contract.js','practices.js','progress.js']:page.add_script_tag(content=(ROOT/'site'/name).read_text())
    page.add_script_tag(content=setup)
    page.evaluate('progress.history()')
    page.get_by_role('heading',name='Earlier fixture run').wait_for()
    assert page.locator('.history-run').count()==3
    page.get_by_label('Harness',exact=True).select_option('Codex')
    page.get_by_role('button',name='Find runs',exact=True).click()
    assert page.locator('.history-run').count()==2
    page.get_by_label('Find a run',exact=True).fill('Earlier')
    page.get_by_role('button',name='Find runs',exact=True).click()
    assert page.locator('.history-run').count()==1
    assert page.get_by_role('link',name='Compare from this run').get_attribute('href').endswith('baseline=20000000-0000-0000-0000-000000000004')
    page.evaluate("history.replaceState(null,'','/?progress&baseline='+earlier);progress.index()")
    page.get_by_role('button',name='Save private comparison').wait_for()
    assert page.get_by_label('Earlier run',exact=True).input_value()=='20000000-0000-0000-0000-000000000004'
    page.get_by_label('Later run',exact=True).select_option('20000000-0000-0000-0000-000000000005')
    page.get_by_label('What tasks and constraints',exact=False).fill('Two fixture bug fixes')
    page.get_by_label('These runs had similar',exact=False).check()
    page.get_by_role('button',name='Save private comparison').click()
    page.get_by_role('heading',name='Your saved comparison',exact=True).wait_for()
    assert page.url.endswith('/?comparison=30000000-0000-0000-0000-000000000004')
    page.get_by_role('heading',name='Comparable context declared',exact=True).wait_for()
    assert page.evaluate('calls[0].payload.earlier')=='20000000-0000-0000-0000-000000000004'
    assert page.evaluate('calls[0].payload.similar_context') is True
    assert page.locator('.progress-metric').first.inner_text().endswith('+1 · later minus earlier')
    assert 'Unknown → Unknown' in page.locator('.progress-metrics').inner_text()
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    page.screenshot(path='/tmp/grinder-progress-phone.png',full_page=True)
    page.set_viewport_size({'width':1280,'height':900})
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    page.screenshot(path='/tmp/grinder-progress-desktop.png',full_page=True)
    page.get_by_label('What will you do differently?',exact=True).fill('Run the named check')
    page.get_by_label('What change would you look for?',exact=True).fill('A result in the completion turn')
    page.get_by_role('button',name='Save practice and start attempt').click()
    page.get_by_role('link',name='Open my practice').wait_for()
    assert page.evaluate('calls[1].payload.comparison')=='30000000-0000-0000-0000-000000000004'
    page.evaluate('practices.detail(practiceId)')
    page.get_by_role('heading',name='Run the named check',exact=True).wait_for()
    assert page.locator('#attempt-50000000-0000-0000-0000-000000000004').count()==1
    page.evaluate('progress.history()')
    page.get_by_role('link',name='Run the named check',exact=True).wait_for()
    # Unknown context must display two observations without a numeric change claim.
    separate=page.evaluate("progress.comparisonHTML({turns_typed:3},{turns_typed:4},['Task context is not confirmed comparable'])")
    assert 'Read these as two separate runs' in separate and '+1' not in separate
    assert not errors,errors
    print(json.dumps({'fixture':'history → frozen comparison → next practice → returning history','mobile_desktop_overflow':False,'javascript_errors':errors,'rpc_calls':[x['name'] for x in page.evaluate('calls')],'screenshots':['/tmp/grinder-progress-phone.png','/tmp/grinder-progress-desktop.png']}))
    browser.close()
