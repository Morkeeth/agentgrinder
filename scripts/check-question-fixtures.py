"""Drive question choice, follow and read controls with explicit server-response fixtures."""
import os,json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
style=re.search(r'<style>(.*?)</style>',(ROOT/'site/index.html').read_text(),re.S).group(1)+(ROOT/'site/design.css').read_text()+(ROOT/'site/social.css').read_text()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('BRAVE_BINARY','/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'),headless=True)
 page=browser.new_page(viewport={'width':390,'height':844});page.route('**/*',lambda r:r.fulfill(content_type='text/html',body='<meta charset="utf-8"><style>'+style+'</style><div class="shell solo"><main id="app" class="main"></main></div>'))
 page.goto('https://grinder-fixture.test/?forum');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 for name in ['run-contract.js','forum.js']:page.add_script_tag(content=(ROOT/'site'/name).read_text())
 page.evaluate("""window.calls=[];window.qid='10000000-0000-0000-0000-000000000001';window.answer='20000000-0000-0000-0000-000000000001';const question={id:qid,run_id:'30000000-0000-0000-0000-000000000001',author_id:'owner',title:'Fixture: which check would help?',body:'A controlled test question.',accepted_reply:null};const rows={grinder_forum_questions:[question],grinder_replies:[{id:answer,forum_question_id:qid,body:'Run the import check before editing.',author:{github_handle:'fixture-answerer'},created_at:'2026-09-05T09:00:00Z'}],grinder_forum_subscriptions:[]};window.db={from(name){let filters=[];const q={select(){return q},eq(k,v){filters.push(r=>r[k]===v);return q},order(){return q},limit(){return q},then(ok,bad){return Promise.resolve({data:rows[name].filter(r=>filters.every(f=>f(r)))}).then(ok,bad)}};return q},async rpc(name,payload){calls.push({name,payload});if(name==='grinder_forum_accept')question.accepted_reply=payload.answer;if(name==='grinder_forum_subscribe'){rows.grinder_forum_subscriptions=payload.enabled?[{question_id:qid,profile_id:'owner'}]:[]}return {data:true}}};window.forum=GrinderForum({client:db,me:()=>({id:'owner'}),app:()=>document.getElementById('app'),frame:()=>{},status:()=>{}});forum.question(qid);""")
 page.get_by_role('button',name='Choose this answer').click()
 page.get_by_role('heading',name='Chosen answer').wait_for()
 assert page.evaluate('calls[0].payload.answer')=='20000000-0000-0000-0000-000000000001'
 page.get_by_role('button',name='Follow replies',exact=True).click()
 page.get_by_role('button',name='Unfollow question',exact=True).wait_for()
 page.get_by_role('button',name='Mark current replies read').click()
 page.get_by_role('button',name='Marked read').wait_for()
 assert page.evaluate('calls[2].payload.through_reply')=='20000000-0000-0000-0000-000000000001'
 assert page.get_by_role('link',name='Try this as a practice').get_attribute('href').endswith('from_reply=20000000-0000-0000-0000-000000000001')
 assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
 page.screenshot(path='/tmp/grinder-question-phone.png',full_page=True)
 page.set_viewport_size({'width':1280,'height':900});page.screenshot(path='/tmp/grinder-question-desktop.png',full_page=True)
 assert not errors,errors
 print('Question → chosen answer → follow → mark observed replies read → practice link passed')
 browser.close()
