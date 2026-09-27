import config from './public-config.json' with {type:'json'};
import {present,guard,formatDuration} from '../site/result-lead.js';
export const origin='https://agentgrinder.vercel.app';
export const validId=id=>typeof id==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export async function readPublic(id,fetcher=fetch){
 if(!validId(id))return null;
 const query=new URLSearchParams({id:'eq.'+id,visibility:'eq.public',select:'id,title,harness,visibility,prompts,artifacts_produced,commits,rhythm,trace_basis,note,coach_verdict,coach_tool_calls,duration_s,route,is_ship,profiles!runs_profile_id_fkey(github_handle)',limit:'1'});
 const response=await fetcher(config.SB_URL+'/rest/v1/runs?'+query,{headers:{apikey:config.SB_KEY},cache:'no-store',signal:AbortSignal.timeout(8000)});
 if(!response.ok)throw new Error('Public run unavailable');const rows=await response.json();
 return Array.isArray(rows)&&rows.length===1?rows[0]:null;
}
export function html(run){const lead=guard(present(run,'og'),run);const title=esc(run.title||'Agent run'),id=encodeURIComponent(run.id),image=origin+'/api/run?id='+id+'&image=1',url=origin+'/r/'+id;
 const outcome=esc(lead.outcome||'No observed outcome is stored for this view.');
 const description=esc((lead.outcome||'No observed outcome is stored for this view.')+' Limit: '+lead.limit).slice(0,300);
 const support=(lead.support||[]).map(row=>`<p>${esc(row.text)}</p>`).join('');
 const duration=esc(lead.duration||'Unknown');
 return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${outcome} · Agent Grinder</title><meta property="og:type" content="article"><meta property="og:title" content="${outcome}"><meta property="og:description" content="${description}"><meta property="og:url" content="${url}"><meta property="og:image" content="${image}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="${outcome}"><meta name="twitter:description" content="${description}"><meta name="twitter:image" content="${image}"><link rel="canonical" href="${url}"><style>body{background:#f8f8f6;color:#111;font:18px/1.45 system-ui;margin:0;padding:24px}main{max-width:720px;margin:24px auto}img{width:100%;height:auto;border:1px solid #ddd}a{color:#123cff}.kicker{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:#666;margin:18px 0 6px}h1{font-size:clamp(28px,6vw,44px);line-height:1.15;margin:0 0 12px}.source,.limit,.support{color:#333;margin:8px 0}.duration{margin-top:22px;padding-top:14px;border-top:1px solid #ddd;color:#666}.duration strong{display:block;color:#111;font-size:28px;font-weight:600}a.open{display:inline-block;background:#123cff;color:white;text-decoration:none;padding:16px 24px;margin:24px 0}</style></head><body><main><a href="/">Agent Grinder</a><p class="kicker">Observed outcome</p><h1>${outcome}</h1><p class="source">${esc(lead.sourceLine)}</p><div class="support">${support}</div><p class="limit"><strong>Limit:</strong> ${esc(lead.limit)}</p><p class="duration"><span>Session time</span><strong>${duration}</strong></p><p>${title}</p><img src="${image.replaceAll('&','&amp;')}" alt="${outcome}" width="1200" height="630"><a class="open" href="/?run=${id}">Open run and discussion</a></main></body></html>`;
}
const el=(type,props,...children)=>({type,props:{...props,children:children.length===1?children[0]:children}});
export function card(run){const lead=guard(present(run,'og'),run);
 const outcome=String(lead.outcome||'No observed outcome is stored for this view.').slice(0,280);
 const duration=lead.duration||'Unknown';
 if(lead.duration!=null&&lead.duration!==formatDuration(run.duration_s))throw new Error('result source guard: duration');
 return el('div',{style:{width:'100%',height:'100%',background:'#f8f8f6',color:'#111',display:'flex',flexDirection:'column',padding:'36px 56px',fontFamily:'sans-serif'}},
 el('div',{style:{display:'flex',color:'#123cff',fontSize:20,fontWeight:700}},'AGENT GRINDER'),
 el('div',{style:{display:'flex',fontSize:22,marginTop:10,color:'#444'}},String(run.title||'Agent run').slice(0,120)),
 el('div',{style:{display:'flex',fontSize:14,letterSpacing:1,color:'#666',marginTop:18}},'OBSERVED OUTCOME'),
 el('div',{style:{display:'flex',fontSize:32,fontWeight:700,marginTop:8,lineHeight:1.25,maxHeight:120,overflow:'hidden'}},outcome),
 el('div',{style:{display:'flex',fontSize:18,marginTop:14}},lead.sourceLine),
 ...(lead.support||[]).map(row=>el('div',{style:{display:'flex',fontSize:18,color:'#333',marginTop:4}},row.text)),
 el('div',{style:{display:'flex',fontSize:16,color:'#333',marginTop:12,lineHeight:1.35}},'Limit: '+lead.limit),
 el('div',{style:{display:'flex',flexDirection:'column',marginTop:18,paddingTop:12,borderTop:'1px solid #ddd'}},
  el('div',{style:{display:'flex',fontSize:14,color:'#666'}},'Session time'),
  el('div',{style:{display:'flex',fontSize:28,fontWeight:700,marginTop:4}},duration)));
}
