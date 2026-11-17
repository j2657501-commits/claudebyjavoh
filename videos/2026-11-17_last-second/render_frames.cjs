// render_frames.cjs <index.html> <outdir> <fps> <WxH> <worker> <nworkers> — frame-exact render (SwiftShader WebGL), every nworkers-th frame
const { chromium } = require('playwright'); const path=require('path'), fs=require('fs'), http=require('http');
(async()=>{ const [src,out,fpsS,res,wk,nw]=process.argv.slice(2); const fps=+fpsS, [w,h]=res.split('x').map(Number), W=+wk, NW=+nw; const root=path.dirname(path.resolve(src));
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.woff2':'font/woff2'};
const srv=http.createServer((q,r)=>{const f=path.join(root,decodeURIComponent(q.url.split('?')[0]));fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return;}r.writeHead(200,{'Content-Type':types[path.extname(f)]||'application/octet-stream'});r.end(d);});});
await new Promise(ok=>srv.listen(0,'127.0.0.1',ok)); fs.mkdirSync(out,{recursive:true});
const b=await chromium.launch({args:['--mute-audio','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']}); const p=await b.newPage({viewport:{width:w,height:h}});
p.on('pageerror',e=>console.log('ERR',String(e)));
await p.goto(`http://127.0.0.1:${srv.address().port}/${path.basename(src)}?render=1&w=${w}&h=${h}`,{waitUntil:'load'}); await p.evaluate(()=>document.fonts.ready);
const dur=await p.evaluate(()=>window.__duration), n=Math.round(dur*fps);
if(W===0){ const b64=await p.evaluate(async()=>await window.__audioWav()); fs.writeFileSync(path.join(out,'..','audio.raw.wav'),Buffer.from(b64,'base64')); console.log('audio ok'); }
for(let i=W;i<n;i+=NW){ const f=path.join(out,`f${String(i).padStart(6,'0')}.png`); if(fs.existsSync(f)) continue;
  await p.evaluate(t=>window.__seek(t), i/fps); await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>r())));
  await p.screenshot({path:f+'.tmp.png'}); fs.renameSync(f+'.tmp.png',f); if(i%48<NW) console.log('frame',i,'/',n); }
console.log('done worker',W); await b.close(); srv.close(); })();
