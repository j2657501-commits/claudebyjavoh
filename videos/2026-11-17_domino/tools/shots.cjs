// node tools/shots.cjs out_dir t1 t2 ... — screenshots at given times (scale 1, for my own checks)
const { chromium } = require("playwright"), http = require("http"), fs = require("fs"), path = require("path");
const root = path.resolve(__dirname, "..");
(async () => {
  const [out, ...ts] = process.argv.slice(2); fs.mkdirSync(out, { recursive: true });
  const types = { ".html": "text/html", ".js": "text/javascript" };
  const srv = http.createServer((q, r) => { const f = path.join(root, decodeURIComponent(q.url.split("?")[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { "Content-Type": types[path.extname(f)] || "application/octet-stream" }); r.end(d); }); });
  await new Promise(ok => srv.listen(0, "127.0.0.1", ok));
  const b = await chromium.launch({ args: ["--use-gl=angle", "--ignore-gpu-blocklist"] });
  const p = await b.newPage({ viewport: { width: 540, height: 960 } });
  p.on("pageerror", e => console.log("ERR", String(e))); p.on("console", m => { if (m.type() === "error" || m.type() === "warning") console.log("console", m.text().slice(0, 300)); });
  await p.goto(`http://127.0.0.1:${srv.address().port}/index.html?render=1`, { waitUntil: "load" });
  await p.waitForFunction(() => typeof window.__seek === "function", null, { timeout: 60000 });
  for (const t of ts) { const t0 = Date.now(); await p.evaluate(t => window.__seek(+t), t); await p.screenshot({ path: path.join(out, `t${(+t).toFixed(2).padStart(6, "0")}.jpg`), type: "jpeg", quality: 80 }); console.log("t", t, Date.now() - t0, "ms"); }
  await b.close(); srv.close();
})();
