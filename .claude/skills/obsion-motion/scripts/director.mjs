// director.mjs — the creative gate as ONE auditable command (SKILL §1, direction.md §3c).
//   node scripts/director.mjs init "<brief>" [--out plan]   → plan/creative.md skeleton + plan/pitch-A|B|C.html (animatic copies, paths fixed)
//   (the agent now fills creative.md and the BEATS of each pitch: three DIFFERENT whole-piece concepts, one of them a «collision»)
//   node scripts/director.mjs check [--out plan] [--sheet-only]            → creative_check.py, 3 fps sheet + WAV per pitch (render.cjs), watch.py,
//                                                              layout_check.mjs → plan/DIRECTOR.md table for the critic subagent
// Nothing is played aloud. Needs Playwright (npm i -D playwright, or PLAYWRIGHT_PATH) and ffmpeg.
import fs from "fs"; import path from "path"; import { execSync } from "child_process"; import { fileURLToPath } from "url";
const HERE = path.dirname(fileURLToPath(import.meta.url));
const a = process.argv.slice(2), mode = a[0], outI = a.indexOf("--out"), OUT = path.resolve(outI >= 0 ? a[outI + 1] : "plan");
// --sheet-only: screenshots via __seek at 3 fps (no MP4), for briefs that forbid rendering video
const SHEET = `const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');const fs=require('fs'),path=require('path');(async()=>{const[f,o]=process.argv.slice(1);fs.mkdirSync(o,{recursive:true});const b=await chromium.launch({args:['--mute-audio']});const p=await b.newPage({viewport:{width:1920,height:1080}});await p.goto('file://'+path.resolve(f));const d=await p.evaluate(()=>window.__duration||10);for(let i=0;i<=d*3;i++){await p.evaluate(t=>window.__seek(t),i/3);await p.screenshot({path:path.join(o,'f'+String(i).padStart(4,'0')+'.jpg'),type:'jpeg',quality:70})}await b.close()})()`;
const sh = (c) => { try { return { ok: true, out: execSync(c, { stdio: ["ignore", "pipe", "pipe"] }).toString() }; } catch (e) { return { ok: false, out: (e.stdout || "") + (e.stderr || "") + "" }; } };
if (mode === "init") {
  const brief = (a[1] || "(бриф)").replace(/</g, "‹").replace(/>/g, "›");   // a brief must never close the page's <script> fs.mkdirSync(OUT, { recursive: true });
  const cr = path.join(OUT, "creative.md");
  if (!fs.existsSync(cr)) fs.writeFileSync(cr, `# Бриф\n${brief}\n\n# 10 частых приёмов темы (5 пометь «запрещён»)\n- \n\n# Сюрпризы (секунда каждого)\n- \n\n# Фирменный момент\n\n# Семя и где оно окупается\n\n# Столкновение (объект темы + один сломанный закон)\n\n# Три питча\n- A:\n- B:\n- C (столкновение):\n`);
  const tpl = fs.readFileSync(path.join(HERE, "animatic.html"), "utf8");
  const rel = path.relative(OUT, HERE).split(path.sep).join("/") || ".";
  for (const P of ["A", "B", "C"]) {
    const f = path.join(OUT, `pitch-${P}.html`); if (fs.existsSync(f)) continue;
    let s = tpl.replace('src="vendor/gsap.min.js"', `src="${rel}/vendor/gsap.min.js"`).replace('src="camlife.js"', `src="${rel}/camlife.js"`).replace('src="sfx.js"', `src="${rel}/sfx.js"`);
    s = s.replace("// ===== EDIT THIS: the beats of one pitch =====", `// ===== PITCH ${P} — brief: ${brief.replace(/\n/g, " ")} =====\n// ===== EDIT THIS: the beats of one pitch =====`);
    fs.writeFileSync(f, s);
  }
  console.log(`init: ${cr} + pitch-A|B|C.html in ${OUT}. Fill them, then: node ${path.relative(process.cwd(), path.join(HERE, "director.mjs"))} check --out ${path.relative(process.cwd(), OUT) || "."}`);
} else if (mode === "check") {
  const rows = [], cc = sh(`python3 "${path.join(HERE, "creative_check.py")}" "${path.join(OUT, "creative.md")}"`);
  rows.push(`## creative.md\n${cc.ok ? "PASS" : "FAIL"}\n\n\`\`\`\n${cc.out.trim()}\n\`\`\``);
  for (const P of ["A", "B", "C"]) {
    const f = path.join(OUT, `pitch-${P}.html`); if (!fs.existsSync(f)) { rows.push(`## pitch ${P}\nmissing`); continue; }
    const same = fs.readFileSync(f, "utf8").includes("Хук: герой-объект уже движется");
    const sheetOnly = a.includes("--sheet-only");
    const mp4 = path.join(OUT, `pitch-${P}.mp4`), r = sheetOnly ? sh(`node -e "${SHEET.replace(/"/g, '\\"')}" "${f}" "${path.join(OUT, `pitch-${P}-sheet`)}"`) : sh(`node "${path.join(HERE, "render.cjs")}" "${f}" --fps 3 --w 1920 --h 1080 --out "${mp4}"`);
    const w = (r.ok && !sheetOnly) ? sh(`python3 "${path.join(HERE, "watch.py")}" "${mp4}" "${path.join(OUT, `pitch-${P}-watch`)}" --fps 3`) : { ok: false, out: "" };
    const l = sh(`node "${path.join(HERE, "layout_check.mjs")}" "${f}" --step 1`);
    rows.push(`## pitch ${P}${same ? " — WARNING: still the template beats, not a real pitch" : ""}\n- render: ${r.ok ? "OK → " + path.basename(mp4) + ", sheets in pitch-" + P + "-watch/sheets/" : "FAIL"}\n- watch: ${(w.out.match(/- (Judder|Audio)[^\n]*/g) || []).join(" · ")}\n- layout: ${l.ok ? "OK" : (l.out.split("\n").slice(0, 4).join(" · "))}`);
  }
  const md = `# DIRECTOR — creative gate before assets\n\nGive this file, the sheets and the three pitch pages to the critic subagent (references/critic.md). It picks ONE pitch (the one it could not predict from the brief) and scores idea + rhythm before any asset is generated.\n\n${rows.join("\n\n")}\n`;
  fs.writeFileSync(path.join(OUT, "DIRECTOR.md"), md); console.log(md);
} else { console.log("usage: director.mjs init \"<brief>\" [--out plan] | check [--out plan]"); process.exit(1); }
