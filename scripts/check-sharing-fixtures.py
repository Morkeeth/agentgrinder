"""Exercise actual sharing controls and exported bytes using labelled fixture data."""
import os,re,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
style=re.search(r'<style>(.*?)</style>',(ROOT/'site/index.html').read_text(),re.S).group(1)+(ROOT/'site/design.css').read_text()+(ROOT/'site/social.css').read_text()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('BRAVE_BINARY','/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'),headless=True)
 page=browser.new_page(viewport={'width':1280,'height':900},accept_downloads=True)
 page.route('**/*',lambda r:r.fulfill(content_type='text/html',body='<meta charset="utf-8"><style>'+style+'</style><div class="shell solo"><main class="main" id="app"></main></div>'))
 page.goto('https://grinder-fixture.test/');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_script_tag(content=(ROOT/'site/sharing.js').read_text())
 page.evaluate("""window.fixture={id:'fixture-run',title:'Fixture: repaired a broken import',visibility:'private',harness:'Codex',profiles:{github_handle:'fixture-builder'},rhythm:[1,3,2,5,1,2],trace_basis:'elapsed',prompts:8,artifacts_produced:2,commits:null,note:'PRIVATE NOTE MUST NOT BE COPIED',project:'PRIVATE PROJECT'};GrinderSharing.mount({run:fixture,slot:document.getElementById('app'),status:()=>{}})""")
 assert page.get_by_role('button',name='Download PNG').is_disabled()
 caption=page.get_by_label('Caption',exact=True)
 assert 'PRIVATE' not in caption.input_value() and '?run=' not in caption.input_value()
 page.get_by_label('Where did the agent').fill('Located the failing parser branch and proposed a fix.')
 page.get_by_label('What was the result?').fill('Fixture example only: the import check passed.')
 page.get_by_label('What will you try next?').fill('Run the import check before editing.')
 page.get_by_label('I have reviewed').check()
 with page.expect_download() as event:page.get_by_role('button',name='Download PNG').click()
 event.value.save_as('/tmp/grinder-share-square.png')
 page.get_by_label('Image format').select_option('portrait')
 assert page.get_by_role('button',name='Download PNG').is_disabled()
 page.get_by_label('I have reviewed').check()
 with page.expect_download() as event:page.get_by_role('button',name='Download PNG').click()
 event.value.save_as('/tmp/grinder-share-portrait.png')
 from PIL import Image
 assert Image.open('/tmp/grinder-share-square.png').size==(1080,1080)
 assert Image.open('/tmp/grinder-share-portrait.png').size==(1080,1350)
 page.screenshot(path='/tmp/grinder-share-desktop.png',full_page=True)
 page.set_viewport_size({'width':390,'height':844})
 assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
 page.screenshot(path='/tmp/grinder-share-phone.png',full_page=True)
 page.evaluate("fixture.visibility='public';GrinderSharing.mount({run:fixture,slot:document.getElementById('app'),status:()=>{}})")
 assert '?run=fixture-run' in page.get_by_label('Caption',exact=True).input_value()
 page.get_by_label('What did you build?').fill('<script>alert(1)</script>')
 assert not page.locator('#app script').count()
 assert not errors,errors
 print(json.dumps({'exports':'1080×1080 and 1080×1350 PNG bytes verified','privacy':'private note/project excluded; private link omitted; review reset after edit','mobile_overflow':False,'js_errors':errors}))
 browser.close()
