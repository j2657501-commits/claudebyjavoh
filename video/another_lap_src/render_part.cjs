// node render_part.cjs startFrame endFrame outDir
const {chromium}=require('playwright'),http=require('http'),fs=require('fs'),path=require('path');
const root=__dirname,types={'.html':'text/html','.js':'text/javascript','.json':'application/json'};
const [a,b,out]=[+process.argv[2],+process.argv[3],process.argv[4]];fs.mkdirSync(out,{recursive:true});
(async()=>{const srv=http.createServer((q,r)=>{const f=path.join(root,decodeURIComponent(q.url.split('?')[0]));fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return}r.writeHead(200,{'Content-Type':types[path.extname(f)]||'application/octet-stream'});r.end(d)})});
await new Promise(o=>srv.listen(0,'127.0.0.1',o));
const br=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--mute-audio']});
const p=await br.newPage({viewport:{width:1080,height:1920}});p.on('pageerror',e=>console.log('ERR',String(e)));
await p.goto(`http://127.0.0.1:${srv.address().port}/index.html`);await p.waitForFunction(()=>window.__ok,null,{timeout:120000});
for(let i=a;i<b;i++){const fp=path.join(out,`f${String(i).padStart(5,'0')}.png`);if(fs.existsSync(fp))continue;
 await p.evaluate(t=>window.__seek(t),i/30);await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
 await p.screenshot({path:fp+'.tmp.png'});fs.renameSync(fp+'.tmp.png',fp);if(i%60==0)console.log('frame',i)}
await br.close();srv.close();console.log('DONE',a,b)})();
