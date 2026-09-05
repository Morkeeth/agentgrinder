module.exports=async function handler(req,res){
 res.setHeader('Cache-Control','private, no-store, max-age=0');res.setHeader('X-Content-Type-Options','nosniff');
 try{
  const {readPublic,html,card}=await import('../server/public-run.mjs');
  const run=await readPublic(req.query.id);
  if(!run){res.statusCode=404;res.setHeader('Content-Type','text/plain; charset=utf-8');res.end('This public run is unavailable.');return}
  if(req.query.image==='1'){
   const {ImageResponse}=await import('@vercel/og');const image=new ImageResponse(card(run),{width:1200,height:630});
   res.setHeader('Content-Type','image/png');res.end(Buffer.from(await image.arrayBuffer()));
  }else{res.setHeader('Content-Type','text/html; charset=utf-8');res.end(html(run))}
 }catch(_){res.statusCode=503;res.setHeader('Content-Type','text/plain; charset=utf-8');res.end('Run preview temporarily unavailable.');}
};
