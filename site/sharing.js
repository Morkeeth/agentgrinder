/* The preview and downloaded PNG use the same canvas and explicit share fields. */
(function(root){
'use strict';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function mount({run,slot,status}){
 const readable=['public','link'].includes(run.visibility), handle=run.profiles?.github_handle;
 const url=location.origin+'/?run='+encodeURIComponent(run.id);
 slot.innerHTML=`<div class="head"><h2>Share your run</h2><a href="/?run=${encodeURIComponent(run.id)}">Back to run</a></div>
 <p class="hint">${readable?(run.visibility==='public'?'Public run · anyone can read it.':'Link-only run · anyone with the link can read it.'):'Private run · exporting an image does not change who can read the run.'}</p>
 <div class="share-studio"><form id="post-editor" class="panel reply-form">
 <label>What did you build?<input name="title" maxlength="100" required value="${esc(run.title)}"></label>
 <label>Where did the agent help or struggle?<textarea name="contribution" maxlength="240" placeholder="Describe one useful contribution or difficult moment."></textarea></label>
 <label>What was the result?<textarea name="result" maxlength="240" placeholder="Describe what you checked. Keep claims specific."></textarea></label>
 <label>What will you try next?<input name="next" maxlength="160" placeholder="One change for the next run"></label>
 <label>Image format<select name="format"><option value="square">Square · 1080 × 1080</option><option value="portrait">Portrait · 1080 × 1350</option></select></label>
 <label><input type="checkbox" name="identity" ${handle?'checked':''}> Include public handle and agent name</label>
 <p class="hint">Only these fields, the selected identity, the trace and three counts appear in the image. Your existing notes and project name are not copied.</p>
 <label><input type="checkbox" name="review"> I have reviewed this image and caption for sharing.</label>
 <div class="cta"><button type="button" id="post-download" disabled>Download PNG</button><button type="button" class="ghost" id="post-copy" disabled>Copy caption</button></div>
 </form><div class="post-preview"><canvas aria-label="Exact share image preview" role="img"></canvas><label>Caption<textarea id="post-caption" readonly rows="8"></textarea></label><p class="hint" id="post-message" role="status"></p></div></div>`;
 const form=slot.querySelector('form'),canvas=slot.querySelector('canvas'),ctx=canvas.getContext('2d');
 const fields=()=>({title:form.elements.title.value.trim(),contribution:form.elements.contribution.value.trim(),result:form.elements.result.value.trim(),next:form.elements.next.value.trim(),identity:form.elements.identity.checked});
 function lines(text,x,y,width,font,lineHeight,maxLines){ctx.font=font;let words=String(text).split(/\s+/),line='',rows=[];for(const word of words){const candidate=line?line+' '+word:word;if(ctx.measureText(candidate).width>width&&line){rows.push(line);line=word}else line=candidate;}if(line)rows.push(line);rows=rows.flatMap(row=>{if(ctx.measureText(row).width<=width)return[row];const parts=[];let part='';for(const c of row){if(ctx.measureText(part+c).width>width){parts.push(part);part=''}part+=c}if(part)parts.push(part);return parts});const clipped=rows.length>maxLines;rows=rows.slice(0,maxLines);if(clipped){let last=rows.at(-1);while(last&&ctx.measureText(last+'…').width>width)last=last.slice(0,-1);rows[rows.length-1]=last+'…'}rows.forEach((row,i)=>ctx.fillText(row,x,y+i*lineHeight));return clipped;}
 function draw(){const f=fields(),portrait=form.elements.format.value==='portrait';canvas.width=1080;canvas.height=portrait?1350:1080;let clipped=false;ctx.fillStyle='#f8f8f6';ctx.fillRect(0,0,1080,canvas.height);ctx.fillStyle='#123cff';ctx.fillRect(64,64,44,8);ctx.fillStyle='#111';ctx.font='600 23px sans-serif';ctx.fillText('AGENT GRINDER',128,80);ctx.fillStyle='#666';ctx.font='20px sans-serif';ctx.fillText('RUN NOTES',820,80);
 ctx.fillStyle='#111';clipped=lines(f.title||'Your run',64,160,952,'600 48px sans-serif',56,2)||clipped;
 ctx.fillStyle='#555';const identity=f.identity&&handle?'@'+handle:'Identity not included';clipped=lines(identity+' · '+(run.harness||'Harness unknown')+(f.identity&&run.agent_name?' · '+run.agent_name:''),64,276,952,'23px sans-serif',28,1)||clipped;
 const values=run.rhythm;ctx.strokeStyle='#123cff';ctx.lineWidth=4;const valid=Array.isArray(values)&&values.length>1&&values.length<=10000&&values.every(v=>Number.isFinite(v)&&v>=0);if(valid){const max=Math.max(...values)||1;ctx.beginPath();values.forEach((v,i)=>{const x=64+i/(values.length-1)*952,y=450-v/max*125;i?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.stroke()}else{ctx.fillStyle='#666';ctx.font='24px sans-serif';ctx.fillText('Trace unavailable',64,390)}
 ctx.fillStyle='#666';ctx.font='19px sans-serif';ctx.fillText(run.trace_basis==='elapsed-agent-tool-calls'?'Agent tool requests · elapsed time':run.trace_basis==='elapsed'?'Session activity · elapsed time':run.trace_basis==='position'?'Session activity · event order':'Session activity · time basis unknown',64,485);
 const metrics=[['Typed turns',run.prompts??run.turns_typed],['Artifacts',run.artifacts_produced],['Commits',run.commits]];metrics.forEach(([name,value],i)=>{const x=64+i*324;ctx.fillStyle='#666';ctx.font='20px sans-serif';ctx.fillText(name,x,545);ctx.fillStyle='#111';ctx.font='600 38px sans-serif';ctx.fillText(value==null?'Unknown':String(value),x,596)});
 let y=665;const blocks=[['THE AGENT',f.contribution],['THE RESULT',f.result],['NEXT RUN',f.next]].filter(([,v])=>v);for(const [label,body] of blocks){ctx.fillStyle='#123cff';ctx.font='600 17px sans-serif';ctx.fillText(label,64,y);ctx.fillStyle='#111';clipped=lines(body,64,y+34,952,'26px sans-serif',32,portrait?3:2)||clipped;y+=portrait?160:110;}
 ctx.strokeStyle='#ddd';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(64,canvas.height-65);ctx.lineTo(1016,canvas.height-65);ctx.stroke();ctx.fillStyle='#666';ctx.font='18px sans-serif';ctx.fillText('Builder’s account · recorded counts are not independent verification',64,canvas.height-30);
 slot.querySelector('#post-caption').value=[f.title,f.contribution&&'Agent: '+f.contribution,f.result&&'Result: '+f.result,f.next&&'Next run: '+f.next,readable?url:''].filter(Boolean).join('\n\n');
 slot.querySelector('#post-message').textContent=clipped?'Some text is shortened in the image. Shorten your text or choose portrait. The caption keeps the full text.':'';
 const ready=form.elements.review.checked&&!!f.title;slot.querySelector('#post-download').disabled=!ready;slot.querySelector('#post-copy').disabled=!ready;
 }
 form.addEventListener('input',e=>{if(e.target.name!=='review')form.elements.review.checked=false;draw()});form.addEventListener('submit',e=>e.preventDefault());
 slot.querySelector('#post-copy').onclick=async()=>{try{await navigator.clipboard.writeText(slot.querySelector('#post-caption').value);status('Caption copied.')}catch(_){status('Select and copy the caption below the image.')}};
 slot.querySelector('#post-download').onclick=()=>canvas.toBlob(blob=>{if(!blob){status('Image export failed. Try again.');return}const link=document.createElement('a'),object=URL.createObjectURL(blob);link.href=object;link.download='agent-grinder-'+run.id+'-'+form.elements.format.value+'.png';link.click();setTimeout(()=>URL.revokeObjectURL(object),1000)},'image/png');
 draw();return{draw};
}
root.GrinderSharing={mount};
})(window);
