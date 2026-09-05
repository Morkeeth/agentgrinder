"""Verify forum search and discussion-to-practice using explicit UI fixtures."""
import os,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('BRAVE_BINARY','/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'),headless=True)
 page=browser.new_page(viewport={'width':390,'height':844})
 page.route('**/*',lambda r:r.fulfill(content_type='text/html',body='<meta charset="utf-8"><div id="app"></div>'))
 page.goto('https://grinder-fixture.test/?forum');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 for name in ['run-contract.js','forum.js','practices.js']:page.add_script_tag(content=(ROOT/'site'/name).read_text())
 page.evaluate("""window.queries=[];window.writes=[];const reply='10000000-0000-0000-0000-000000000001',run='20000000-0000-0000-0000-000000000001';const rows={runs:[{id:run,title:'Fixture parser repair',visibility:'public',rhythm:[1,3,2]}],grinder_replies:[{id:reply,run_id:run,body:'Run the import check before editing.',created_at:'2026-09-04T12:00:00Z'}],grinder_practice_versions:[],grinder_memberships:[]};window.db={from(name){let filters=[],offset=0,end=100,inserted=false;const q={select(){return q},order(){return q},range(a,b){offset=a;end=b+1;return q},limit(n){end=n;return q},eq(k,v){filters.push(r=>r[k]===v);return q},ilike(k,v){queries.push([name,k,v]);filters.push(r=>String(r[k]).toLowerCase().includes(v.slice(1,-1).toLowerCase()));return q},insert(row){writes.push(row);inserted=true;return q},then(resolve,reject){if(inserted)return new Promise(()=>{});return Promise.resolve({data:inserted?[{id:'saved-practice'}]:(rows[name]||[]).filter(r=>filters.every(f=>f(r))).slice(offset,end)}).then(resolve,reject)}};return q}};window.config={client:db,app:()=>document.getElementById('app'),frame:()=>{},status:()=>{},me:()=>({id:'owner'})};window.forum=GrinderForum(config);window.practices=GrinderPractices(config);forum.index();""")
 page.get_by_label('Show',exact=True).select_option('runs')
 page.get_by_role('button',name='Search forum').click()
 page.get_by_role('link',name='Fixture parser repair').wait_for()
 page.get_by_label('Show',exact=True).select_option('replies')
 page.get_by_label('Find a conversation').fill('import')
 page.get_by_role('button',name='Search forum').click()
 page.get_by_role('link',name='Turn into a practice').wait_for()
 href=page.get_by_role('link',name='Turn into a practice').get_attribute('href')
 assert href=='/?practices&from_reply=10000000-0000-0000-0000-000000000001'
 page.evaluate('(url)=>{history.replaceState(null,"",url);return practices.index()}',href)
 page.get_by_label('What to try',exact=True).wait_for()
 assert page.get_by_label('What to try',exact=True).input_value()=='Run the import check before editing.'
 assert page.get_by_label('Audience',exact=True).input_value()=='private'
 assert page.get_by_role('link',name='Source conversation').get_attribute('href').endswith('#reply-10000000-0000-0000-0000-000000000001')
 page.get_by_label('Name',exact=True).fill('Check before editing')
 page.get_by_label('Task context',exact=True).fill('Fixture parser change')
 page.get_by_label('Expected change',exact=True).fill('A known failure before a patch')
 # Record submitted persistence payload before the real navigation leaves the fixture.
 page.evaluate("document.getElementById('practice-create').dispatchEvent(new Event('submit',{cancelable:true,bubbles:true}))")
 assert page.evaluate('writes[0].visibility')=='private'
 assert page.evaluate('writes[0].source_run')=='20000000-0000-0000-0000-000000000001'
 assert page.evaluate('writes[0].instruction')=='Run the import check before editing.'
 print('Forum search → source-linked private practice draft → correct persistence payload passed')
 assert not errors,errors
 browser.close()
